"""
Streaming API endpoints for real-time query responses
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import structlog

from app.models.query import Query
from app.agents.query import query_agent
from app.services.llm import llm_service

logger = structlog.get_logger()
router = APIRouter()


async def generate_streaming_response(query: Query) -> AsyncGenerator[str, None]:
    """
    Generate streaming response for a query
    
    Args:
        query: Query request
        
    Yields:
        Server-sent events with response chunks
    """
    try:
        # Send initial event
        yield f"data: {json.dumps({'type': 'start', 'message': 'Processing query...'})}\n\n"
        
        # Step 1: Retrieve context
        yield f"data: {json.dumps({'type': 'status', 'message': 'Retrieving relevant context...'})}\n\n"
        
        sources = await query_agent._retrieve_context(
            question=query.question,
            repository_id=query.repository_id,
            max_results=query.max_results,
            include_code=query.include_code,
            include_docs=query.include_docs
        )
        
        # Send sources
        sources_data = [
            {
                'type': s.type,
                'file_path': s.file_path,
                'relevance_score': s.relevance_score,
                'documentation_title': s.documentation_title
            }
            for s in sources
        ]
        yield f"data: {json.dumps({'type': 'sources', 'data': sources_data})}\n\n"
        
        # Step 2: Generate answer
        yield f"data: {json.dumps({'type': 'status', 'message': 'Generating answer...'})}\n\n"

        if sources:
            context_parts = []
            for idx, source in enumerate(sources[:5], 1):
                source_text = f"\n--- Source {idx} ---\n{source.content[:500]}\n"
                context_parts.append(source_text)
            context = "\n".join(context_parts)
            prompt = f"""Based on the following context from the codebase, answer the question.

Context:
{context}

Question: {query.question}

Provide a clear, accurate answer based on the context above."""
        else:
            prompt = f"""The user asked: {query.question}

No indexed documents were found in the knowledge base yet. Let the user know the collection is empty and they need to index their codebase first. Be helpful and explain what DocuMind does and how to get started."""
        
        # Stream LLM response
        answer_chunks = []
        async for chunk in llm_service.generate_stream(
            prompt=prompt,
            system_prompt=llm_service.QUERY_SYSTEM_PROMPT,
            max_tokens=1000
        ):
            answer_chunks.append(chunk)
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        
        # Send complete answer
        full_answer = "".join(answer_chunks)
        yield f"data: {json.dumps({'type': 'answer', 'content': full_answer})}\n\n"
        
        # Send completion
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        logger.error("Streaming error", error=str(e), exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.post("/stream")
async def stream_query(query: Query):
    """
    Stream query response in real-time
    
    Args:
        query: Query request
        
    Returns:
        Server-sent events stream
    """
    try:
        logger.info("Starting streaming query", question=query.question[:100])
        
        return StreamingResponse(
            generate_streaming_response(query),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        logger.error("Failed to start stream", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start stream: {str(e)}"
        )


# Made with Bob