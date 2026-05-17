"""Models for documentation pages"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class CodeLink(BaseModel):
    """Link between documentation and code"""
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    symbol_name: Optional[str] = None
    symbol_type: Optional[str] = None
    commit_sha: str


class DocumentationBase(BaseModel):
    """Base documentation model"""
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)


class DocumentationCreate(DocumentationBase):
    """Schema for creating documentation"""
    repository_id: UUID
    notion_page_id: Optional[str] = None
    linked_code: List[CodeLink] = Field(default_factory=list)


class DocumentationUpdate(BaseModel):
    """Schema for updating documentation"""
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    quality_score: Optional[float] = None
    is_stale: Optional[bool] = None
    notion_page_id: Optional[str] = None


class DocumentationPage(DocumentationBase):
    """Complete documentation page model"""
    id: UUID
    repository_id: UUID
    notion_page_id: Optional[str] = None
    version: int = 1
    quality_score: Optional[float] = None
    is_stale: bool = False
    linked_code: List[CodeLink] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class DocumentationSearchResult(BaseModel):
    """Search result for documentation"""
    id: UUID
    title: str
    content_preview: str
    relevance_score: float
    repository_id: UUID
    repository_name: str
    tags: List[str]
    is_stale: bool
    updated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class DocumentationCoverage(BaseModel):
    """Documentation coverage metrics"""
    repository_id: UUID
    repository_name: str
    total_files: int = 0
    documented_files: int = 0
    coverage_percentage: float = 0.0
    total_docs: int = 0
    stale_docs: int = 0
    avg_quality_score: Optional[float] = None
    undocumented_files: List[str] = Field(default_factory=list)

# Made with Bob
