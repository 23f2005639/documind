"""Pydantic v2 data models for DocuMind."""

from pydantic import BaseModel, Field
from typing import Optional


class ChangeEvent(BaseModel):
    """Git change event from watchdog."""
    files_changed: list[str]
    diff: str
    commit_msg: str
    commit_hash: str
    timestamp: str
    author: str


class FunctionInfo(BaseModel):
    """Analyzed function metadata."""
    name: str
    signature: str
    docstring: str
    dependencies: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Output from Analyzer agent."""
    module_name: str
    functions: list[FunctionInfo]
    classes: list[str]
    arch_summary: str
    dependencies: list[str]
    data_flows: list[str]


class DocChunk(BaseModel):
    """Embedded documentation chunk for Qdrant."""
    content: str
    module_name: str
    section: str
    commit_hash: str
    doc_path: str

# Made with Bob
