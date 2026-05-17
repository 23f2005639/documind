"""Models for repository management"""

from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from uuid import UUID


class RepositoryBase(BaseModel):
    """Base repository model"""
    github_url: str
    name: str
    default_branch: str = "main"
    notion_workspace_id: Optional[str] = None


class RepositoryCreate(RepositoryBase):
    """Schema for creating a repository"""
    webhook_secret: Optional[str] = None


class RepositoryUpdate(BaseModel):
    """Schema for updating a repository"""
    name: Optional[str] = None
    default_branch: Optional[str] = None
    notion_workspace_id: Optional[str] = None
    is_active: Optional[bool] = None


class Repository(RepositoryBase):
    """Complete repository model"""
    id: UUID
    webhook_secret: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class RepositoryStats(BaseModel):
    """Repository statistics"""
    id: UUID
    name: str
    github_url: str
    total_docs: int = 0
    stale_docs: int = 0
    avg_quality_score: Optional[float] = None
    total_commits: int = 0
    processed_commits: int = 0
    documentation_coverage: Optional[float] = None
    last_updated: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

# Made with Bob
