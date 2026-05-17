"""Models for change reports and code analysis"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
from uuid import UUID


class ChangeType(str, Enum):
    """Type of code change"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    BREAKING = "breaking"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class FileChangeType(str, Enum):
    """Type of file change"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RENAME = "rename"


class SymbolType(str, Enum):
    """Type of code symbol"""
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    INTERFACE = "interface"
    TYPE = "type"


class Symbol(BaseModel):
    """Represents a code symbol (function, class, etc.)"""
    name: str
    type: SymbolType
    line_start: int
    line_end: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    complexity: Optional[int] = None
    
    class Config:
        use_enum_values = True


class FileChange(BaseModel):
    """Represents changes to a single file"""
    path: str
    change_type: FileChangeType
    language: str
    diff: str
    lines_added: int = 0
    lines_removed: int = 0
    symbols_added: List[Symbol] = Field(default_factory=list)
    symbols_modified: List[Symbol] = Field(default_factory=list)
    symbols_removed: List[Symbol] = Field(default_factory=list)
    dependencies_changed: List[str] = Field(default_factory=list)
    imports_added: List[str] = Field(default_factory=list)
    imports_removed: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class ChangeReport(BaseModel):
    """Complete change report for a commit"""
    id: Optional[UUID] = None
    repository_id: UUID
    commit_sha: str
    author: str
    author_email: Optional[str] = None
    timestamp: datetime
    message: str
    change_type: ChangeType
    files_changed: List[FileChange]
    impact_score: float = 0.0
    processed: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ChangeReportCreate(BaseModel):
    """Schema for creating a change report"""
    repository_id: UUID
    commit_sha: str
    author: str
    author_email: Optional[str] = None
    timestamp: datetime
    message: str
    change_type: ChangeType
    files_changed: List[FileChange]
    impact_score: float = 0.0
    
    class Config:
        use_enum_values = True


class ChangeReportUpdate(BaseModel):
    """Schema for updating a change report"""
    processed: Optional[bool] = None
    impact_score: Optional[float] = None
    
    class Config:
        use_enum_values = True

# Made with Bob
