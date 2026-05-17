"""Models for query and search functionality"""

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class Source(BaseModel):
    """Source citation for query response"""
    type: str  # "code" or "documentation"
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    content: str
    relevance_score: float
    documentation_id: Optional[UUID] = None
    documentation_title: Optional[str] = None


class Query(BaseModel):
    """Query request model"""
    question: str
    repository_id: Optional[UUID] = None
    session_id: Optional[str] = None
    max_results: int = 10
    include_code: bool = True
    include_docs: bool = True


class QueryResponse(BaseModel):
    """Query response model"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    answer: str
    sources: List[Source]
    confidence_score: float
    response_time_ms: int
    session_id: str
    related_questions: List[str] = Field(default_factory=list)


class QueryHistory(BaseModel):
    """Query history record"""
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    id: UUID
    repository_id: Optional[UUID] = None
    session_id: str
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    feedback: Optional[int] = None  # -1, 0, 1
    response_time_ms: int
    created_at: datetime


class QueryFeedback(BaseModel):
    """Feedback on query response"""
    query_id: UUID
    feedback: int = Field(..., ge=-1, le=1)  # -1 (bad), 0 (neutral), 1 (good)
    comment: Optional[str] = None


class SearchQuery(BaseModel):
    """Search query model"""
    query: str
    repository_id: Optional[UUID] = None
    search_type: str = "hybrid"  # "semantic", "keyword", "hybrid"
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """Search result model"""
    id: str
    type: str  # "code" or "documentation"
    title: str
    content: str
    score: float
    metadata: Dict[str, Any]
    highlights: List[str] = Field(default_factory=list)

# Made with Bob
