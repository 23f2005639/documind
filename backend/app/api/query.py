"""
API endpoints for query functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from uuid import UUID
import structlog

from app.models.query import (
    Query,
    QueryResponse,
    QueryFeedback,
    SearchQuery,
    SearchResult
)
from app.agents.query import query_agent
from app.services.search import hybrid_search

logger = structlog.get_logger()
router = APIRouter()


@router.post("/ask", response_model=QueryResponse)
async def ask_question(query: Query):
    """
    Ask a question about the codebase
    
    Args:
        query: Query request with question and filters
        
    Returns:
        Query response with answer and sources
    """
    try:
        logger.info("Received query request", question=query.question[:100])
        
        response = await query_agent.answer_query(query)
        
        return response
        
    except Exception as e:
        logger.error("Failed to process query", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.post("/search", response_model=list[SearchResult])
async def search(search_query: SearchQuery):
    """
    Search for code and documentation
    
    Args:
        search_query: Search parameters
        
    Returns:
        List of search results
    """
    try:
        logger.info(
            "Received search request",
            query=search_query.query[:100],
            search_type=search_query.search_type
        )
        
        # Build filters
        filters = search_query.filters or {}
        if search_query.repository_id:
            filters['repository_id'] = str(search_query.repository_id)
        
        # Perform search
        results = await hybrid_search.search(
            query=search_query.query,
            search_type=search_query.search_type,
            limit=search_query.limit,
            filters=filters if filters else None
        )
        
        return results
        
    except Exception as e:
        logger.error("Search failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/feedback")
async def submit_feedback(feedback: QueryFeedback):
    """
    Submit feedback on a query response
    
    Args:
        feedback: Feedback data
        
    Returns:
        Success message
    """
    try:
        await query_agent.provide_feedback(
            query_id=feedback.query_id,
            feedback=feedback.feedback,
            comment=feedback.comment
        )
        
        return {"status": "success", "message": "Feedback recorded"}
        
    except Exception as e:
        logger.error("Failed to record feedback", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record feedback: {str(e)}"
        )


@router.get("/history/{session_id}")
async def get_session_history(
    session_id: str,
    limit: int = 10
):
    """
    Get query history for a session
    
    Args:
        session_id: Session ID
        limit: Maximum number of queries to return
        
    Returns:
        List of queries and responses
    """
    try:
        from app.db.database import supabase
        
        result = supabase.table('query_history') \
            .select('*') \
            .eq('session_id', session_id) \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        
        return result.data
        
    except Exception as e:
        logger.error("Failed to retrieve history", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@router.delete("/history/{session_id}")
async def clear_session_history(session_id: str):
    """
    Clear query history for a session
    
    Args:
        session_id: Session ID
        
    Returns:
        Success message
    """
    try:
        from app.db.database import supabase
        
        supabase.table('query_history') \
            .delete() \
            .eq('session_id', session_id) \
            .execute()
        
        return {"status": "success", "message": "History cleared"}
        
    except Exception as e:
        logger.error("Failed to clear history", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear history: {str(e)}"
        )


@router.get("/stats")
async def get_query_stats(repository_id: Optional[UUID] = None):
    """
    Get query statistics
    
    Args:
        repository_id: Optional repository filter
        
    Returns:
        Query statistics
    """
    try:
        from app.db.database import supabase
        
        # Build query
        query = supabase.table('query_history').select('*')
        
        if repository_id:
            query = query.eq('repository_id', str(repository_id))
        
        result = query.execute()
        
        # Calculate statistics
        total_queries = len(result.data)
        
        if total_queries == 0:
            return {
                "total_queries": 0,
                "avg_response_time_ms": 0,
                "positive_feedback": 0,
                "negative_feedback": 0,
                "neutral_feedback": 0
            }
        
        avg_response_time = sum(
            q.get('response_time_ms', 0) for q in result.data
        ) / total_queries
        
        positive_feedback = sum(
            1 for q in result.data if q.get('feedback') == 1
        )
        negative_feedback = sum(
            1 for q in result.data if q.get('feedback') == -1
        )
        neutral_feedback = sum(
            1 for q in result.data if q.get('feedback') == 0
        )
        
        return {
            "total_queries": total_queries,
            "avg_response_time_ms": int(avg_response_time),
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
            "neutral_feedback": neutral_feedback
        }
        
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )


# Made with Bob