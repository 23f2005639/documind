"""
Query Agent for DocuMind
Handles natural language queries using RAG (Retrieval-Augmented Generation)
"""

from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import time
import structlog

from app.models.query import Query, QueryResponse, Source
from app.services.search import hybrid_search
from app.services.llm import llm_service
from app.services.vector_store import vector_store
from app.db.database import supabase

logger = structlog.get_logger()


class QueryAgent:
    """Agent for answering questions about code and documentation"""
    
    def __init__(self):
        self.max_context_length = 4000  # Maximum context tokens
        self.min_confidence_threshold = 0.3
        
        logger.info("Query Agent initialized")
    
    async def answer_query(self, query: Query) -> QueryResponse:
        """
        Answer a user query using RAG
        
        Args:
            query: Query request
            
        Returns:
            Query response with answer and sources
        """
        start_time = time.time()
        
        logger.info(
            "Processing query",
            question=query.question[:100],
            repository_id=str(query.repository_id) if query.repository_id else None,
            session_id=query.session_id
        )
        
        # Generate session ID if not provided
        session_id = query.session_id or str(uuid4())
        
        # Step 1: Retrieve relevant context
        sources = await self._retrieve_context(
            question=query.question,
            repository_id=query.repository_id,
            max_results=query.max_results,
            include_code=query.include_code,
            include_docs=query.include_docs
        )
        
        if not sources:
            logger.warning("No relevant sources found for query")
            return QueryResponse(
                answer="I couldn't find any relevant information to answer your question. Please try rephrasing or check if the repository is properly indexed.",
                sources=[],
                confidence_score=0.0,
                response_time_ms=int((time.time() - start_time) * 1000),
                session_id=session_id,
                related_questions=[]
            )
        
        # Step 2: Retrieve conversation history if session exists
        conversation_history = []
        if query.session_id:
            conversation_history = await self._get_conversation_history(
                session_id=query.session_id,
                limit=5
            )
        
        # Step 3: Generate answer using LLM
        answer, confidence, related_questions = await self._generate_answer(
            question=query.question,
            sources=sources,
            conversation_history=conversation_history
        )
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Create response
        response = QueryResponse(
            answer=answer,
            sources=sources,
            confidence_score=confidence,
            response_time_ms=response_time_ms,
            session_id=session_id,
            related_questions=related_questions
        )
        
        # Step 4: Store query in history
        await self._store_query_history(
            query=query,
            response=response,
            repository_id=query.repository_id
        )
        
        logger.info(
            "Query processed successfully",
            response_time_ms=response_time_ms,
            sources_count=len(sources),
            confidence=confidence
        )
        
        return response
    
    async def _retrieve_context(
        self,
        question: str,
        repository_id: Optional[UUID],
        max_results: int,
        include_code: bool,
        include_docs: bool
    ) -> List[Source]:
        """
        Retrieve relevant context using hybrid search
        
        Args:
            question: User question
            repository_id: Optional repository filter
            max_results: Maximum number of results
            include_code: Include code snippets
            include_docs: Include documentation
            
        Returns:
            List of relevant sources
        """
        # Build filters
        filters = {}
        if repository_id:
            filters['repository_id'] = str(repository_id)
        
        # Determine what types to include
        type_filters = []
        if include_code:
            type_filters.append('code')
        if include_docs:
            type_filters.append('documentation')
        
        # Perform hybrid search
        search_results = await hybrid_search.search(
            query=question,
            search_type="hybrid",
            limit=max_results,
            filters=filters if filters else None,
            semantic_weight=0.7,  # Favor semantic understanding
            keyword_weight=0.3
        )
        
        # Convert to Source objects
        sources = []
        for result in search_results:
            # Skip if type doesn't match filters
            if type_filters and result.type not in type_filters:
                continue
            
            # Skip low-confidence results
            if result.score < self.min_confidence_threshold:
                continue
            
            metadata = result.metadata
            
            source = Source(
                type=result.type,
                file_path=metadata.get('file_path'),
                line_start=metadata.get('line_start'),
                line_end=metadata.get('line_end'),
                content=result.content,
                relevance_score=result.score,
                documentation_id=UUID(metadata['documentation_id']) if metadata.get('documentation_id') else None,
                documentation_title=metadata.get('title')
            )
            sources.append(source)
        
        logger.info(
            "Context retrieved",
            sources_count=len(sources),
            avg_score=sum(s.relevance_score for s in sources) / len(sources) if sources else 0
        )
        
        return sources
    
    async def _get_conversation_history(
        self,
        session_id: str,
        limit: int = 5
    ) -> List[Dict[str, str]]:
        """
        Retrieve conversation history for a session
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages
            
        Returns:
            List of conversation messages
        """
        try:
            result = supabase.table('query_history') \
                .select('question, answer') \
                .eq('session_id', session_id) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            
            # Reverse to get chronological order
            history = []
            for record in reversed(result.data):
                history.append({
                    'role': 'user',
                    'content': record['question']
                })
                history.append({
                    'role': 'assistant',
                    'content': record['answer']
                })
            
            logger.info("Conversation history retrieved", messages=len(history))
            return history
            
        except Exception as e:
            logger.error("Failed to retrieve conversation history", error=str(e))
            return []
    
    async def _generate_answer(
        self,
        question: str,
        sources: List[Source],
        conversation_history: List[Dict[str, str]]
    ) -> tuple[str, float, List[str]]:
        """
        Generate answer using LLM with retrieved context
        
        Args:
            question: User question
            sources: Retrieved sources
            conversation_history: Previous conversation
            
        Returns:
            Tuple of (answer, confidence_score, related_questions)
        """
        # Build context from sources
        context_parts = []
        total_length = 0
        
        for idx, source in enumerate(sources, 1):
            # Format source
            source_text = f"\n--- Source {idx} ({source.type}) ---\n"
            if source.file_path:
                source_text += f"File: {source.file_path}\n"
            if source.documentation_title:
                source_text += f"Documentation: {source.documentation_title}\n"
            source_text += f"Relevance: {source.relevance_score:.2f}\n"
            source_text += f"Content:\n{source.content}\n"
            
            # Check if adding this source exceeds context limit
            if total_length + len(source_text) > self.max_context_length:
                break
            
            context_parts.append(source_text)
            total_length += len(source_text)
        
        context = "\n".join(context_parts)
        
        # Build prompt
        prompt = self._build_query_prompt(
            question=question,
            context=context,
            conversation_history=conversation_history
        )
        
        # Generate answer
        try:
            response = await llm_service.generate_structured(
                prompt=prompt,
                system_prompt=llm_service.QUERY_SYSTEM_PROMPT,
                response_format={
                    "type": "json_object",
                    "schema": {
                        "answer": "string",
                        "confidence": "number",
                        "related_questions": "array"
                    }
                },
                max_tokens=1000,
                temperature=0.3  # Lower temperature for more focused answers
            )
            
            answer = response.get('answer', 'I apologize, but I could not generate a proper answer.')
            confidence = float(response.get('confidence', 0.5))
            related_questions = response.get('related_questions', [])
            
            # Ensure related_questions is a list
            if not isinstance(related_questions, list):
                related_questions = []
            
            logger.info(
                "Answer generated",
                answer_length=len(answer),
                confidence=confidence,
                related_count=len(related_questions)
            )
            
            return answer, confidence, related_questions[:3]  # Limit to 3 related questions
            
        except Exception as e:
            logger.error("Failed to generate answer", error=str(e))
            
            # Fallback: Create a simple answer from sources
            fallback_answer = self._create_fallback_answer(question, sources)
            return fallback_answer, 0.3, []
    
    def _build_query_prompt(
        self,
        question: str,
        context: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Build prompt for query answering"""
        
        prompt_parts = []
        
        # Add conversation history if available
        if conversation_history:
            prompt_parts.append("Previous conversation:")
            for msg in conversation_history[-6:]:  # Last 3 exchanges
                role = "User" if msg['role'] == 'user' else "Assistant"
                prompt_parts.append(f"{role}: {msg['content']}")
            prompt_parts.append("")
        
        # Add context
        prompt_parts.append("Relevant information from the codebase:")
        prompt_parts.append(context)
        prompt_parts.append("")
        
        # Add question
        prompt_parts.append(f"Question: {question}")
        prompt_parts.append("")
        
        # Add instructions
        prompt_parts.append("Please provide:")
        prompt_parts.append("1. A clear, accurate answer based on the provided context")
        prompt_parts.append("2. A confidence score (0.0 to 1.0) indicating how well the context supports your answer")
        prompt_parts.append("3. Up to 3 related questions the user might want to ask")
        prompt_parts.append("")
        prompt_parts.append("Format your response as JSON with keys: answer, confidence, related_questions")
        
        return "\n".join(prompt_parts)
    
    def _create_fallback_answer(
        self,
        question: str,
        sources: List[Source]
    ) -> str:
        """Create a simple fallback answer from sources"""
        
        if not sources:
            return "I couldn't find relevant information to answer your question."
        
        answer_parts = [
            "Based on the available information:",
            ""
        ]
        
        for idx, source in enumerate(sources[:3], 1):
            answer_parts.append(f"{idx}. From {source.type}:")
            # Take first 200 characters
            content_preview = source.content[:200]
            if len(source.content) > 200:
                content_preview += "..."
            answer_parts.append(f"   {content_preview}")
            answer_parts.append("")
        
        answer_parts.append("Please refer to the sources above for more details.")
        
        return "\n".join(answer_parts)
    
    async def _store_query_history(
        self,
        query: Query,
        response: QueryResponse,
        repository_id: Optional[UUID]
    ):
        """Store query and response in history"""
        
        try:
            # Convert sources to JSON-serializable format
            sources_data = [
                {
                    'type': s.type,
                    'file_path': s.file_path,
                    'content_preview': s.content[:200],
                    'relevance_score': s.relevance_score,
                    'documentation_id': str(s.documentation_id) if s.documentation_id else None,
                    'documentation_title': s.documentation_title
                }
                for s in response.sources
            ]
            
            data = {
                'repository_id': str(repository_id) if repository_id else None,
                'session_id': response.session_id,
                'question': query.question,
                'answer': response.answer,
                'sources': sources_data,
                'response_time_ms': response.response_time_ms
            }
            
            supabase.table('query_history').insert(data).execute()
            
            logger.info("Query stored in history", session_id=response.session_id)
            
        except Exception as e:
            logger.error("Failed to store query history", error=str(e))
    
    async def provide_feedback(
        self,
        query_id: UUID,
        feedback: int,
        comment: Optional[str] = None
    ):
        """
        Store user feedback on a query response
        
        Args:
            query_id: Query history ID
            feedback: Feedback score (-1, 0, 1)
            comment: Optional feedback comment
        """
        try:
            data = {'feedback': feedback}
            if comment:
                data['comment'] = comment
            
            supabase.table('query_history') \
                .update(data) \
                .eq('id', str(query_id)) \
                .execute()
            
            logger.info("Feedback stored", query_id=str(query_id), feedback=feedback)
            
        except Exception as e:
            logger.error("Failed to store feedback", error=str(e))


# Global instance
query_agent = QueryAgent()

# Made with Bob