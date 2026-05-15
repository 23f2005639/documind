"""LangGraph 1.0 supervisor with MemorySaver checkpointing."""

import logging
import operator
import os
from typing import Annotated, Optional, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

# OpenRouter configuration
OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def llm(model: str, temperature: float = 0.1) -> ChatOpenAI:
    """
    Factory for OpenRouter LLM access.
    
    Args:
        model: OpenRouter model ID (e.g., "qwen/qwen3-coder:free")
        temperature: Sampling temperature (0.1 for code/analysis, 0.3 for writing)
    
    Returns:
        Configured ChatOpenAI instance
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=api_key,
        openai_api_base=OPENROUTER_BASE,
    )


# LLM instances for different agents (lazy initialization to avoid import-time errors)
def get_analyzer_llm() -> ChatOpenAI:
    """Get analyzer LLM instance."""
    return llm("qwen/qwen3-coder:free")

def get_supervisor_llm() -> ChatOpenAI:
    """Get supervisor LLM instance."""
    return llm("deepseek/deepseek-r1:free")

def get_writer_llm() -> ChatOpenAI:
    """Get writer LLM instance."""
    return llm("deepseek/deepseek-chat-v3:free")

def get_query_llm() -> ChatOpenAI:
    """Get query LLM instance."""
    return llm("meta-llama/llama-4-scout:free")


class DocuMindState(TypedDict):
    """State shared across all LangGraph nodes."""
    
    # Input from watcher
    change_event: Optional[dict]
    
    # Analyzer output
    analysis_result: Optional[dict]
    
    # Writer output (accumulates across multiple docs)
    docs_written: Annotated[list[str], operator.add]
    
    # Query agent output
    query_response: Optional[str]
    
    # Error tracking
    error: Optional[str]


def watcher_node(state: DocuMindState) -> dict:
    """
    Entry point node: receives ChangeEvent from GitWatcher.
    
    Args:
        state: Current pipeline state
    
    Returns:
        Partial state update
    """
    try:
        change_event = state.get("change_event")
        if not change_event:
            logger.warning("watcher_node: No change_event in state")
            return {"error": "No change_event provided"}
        
        logger.info(f"watcher_node: Processing commit {change_event.get('commit_hash', 'unknown')[:8]}")
        return {"change_event": change_event}
    
    except Exception as e:
        logger.error(f"watcher_node failed: {e}")
        return {"error": f"watcher_node: {e}"}


def analyzer_node(state: DocuMindState) -> dict:
    """
    Analyzer node: calls Qwen3 Coder to analyze code changes.
    
    Args:
        state: Current pipeline state
    
    Returns:
        Partial state update with analysis_result
    """
    try:
        change_event = state.get("change_event")
        if not change_event:
            return {"error": "analyzer_node: No change_event in state"}
        
        logger.info("analyzer_node: Analyzing code changes...")
        
        # TODO: Replace with actual analyzer.py call in later phase
        # For now, return stub data
        stub_result = {
            "module": "stub",
            "functions": [],
            "classes": [],
            "arch_summary": "Stub analysis result",
        }
        
        logger.info(f"analyzer_node: Analysis complete for module '{stub_result['module']}'")
        return {"analysis_result": stub_result}
    
    except Exception as e:
        logger.error(f"analyzer_node failed: {e}")
        return {"error": f"analyzer_node: {e}"}


def writer_node(state: DocuMindState) -> dict:
    """
    Writer node: generates documentation using DeepAgents + DeepSeek V3.
    
    Args:
        state: Current pipeline state
    
    Returns:
        Partial state update with docs_written
    """
    try:
        analysis_result = state.get("analysis_result")
        if not analysis_result:
            return {"error": "writer_node: No analysis_result in state"}
        
        logger.info("writer_node: Writing documentation...")
        
        # TODO: Replace with actual writer.py call in later phase
        # For now, return stub data
        stub_doc_path = "docs/stub.md"
        
        logger.info(f"writer_node: Documentation written to {stub_doc_path}")
        return {"docs_written": [stub_doc_path]}
    
    except Exception as e:
        logger.error(f"writer_node failed: {e}")
        return {"error": f"writer_node: {e}"}


def indexer_node(state: DocuMindState) -> dict:
    """
    Indexer node: embeds and stores documentation in Qdrant + DuckDB.
    
    Args:
        state: Current pipeline state
    
    Returns:
        Partial state update (empty if successful)
    """
    try:
        docs_written = state.get("docs_written", [])
        if not docs_written:
            return {"error": "indexer_node: No docs_written in state"}
        
        logger.info(f"indexer_node: Indexing {len(docs_written)} documents...")
        
        # TODO: Replace with actual store calls in later phase
        # For now, just log
        for doc_path in docs_written:
            logger.info(f"indexer_node: Indexed {doc_path}")
        
        logger.info("indexer_node: Indexing complete")
        return {}
    
    except Exception as e:
        logger.error(f"indexer_node failed: {e}")
        return {"error": f"indexer_node: {e}"}


# Build StateGraph
def create_supervisor_graph() -> StateGraph:
    """
    Create and compile the LangGraph supervisor.
    
    Returns:
        Compiled StateGraph with MemorySaver checkpointing
    """
    graph = StateGraph(DocuMindState)
    
    # Add nodes
    graph.add_node("watcher", watcher_node)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("writer", writer_node)
    graph.add_node("indexer", indexer_node)
    
    # Define edges (linear flow)
    graph.set_entry_point("watcher")
    graph.add_edge("watcher", "analyzer")
    graph.add_edge("analyzer", "writer")
    graph.add_edge("writer", "indexer")
    graph.add_edge("indexer", END)
    
    # Compile with checkpointing
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# Global app instance
app = create_supervisor_graph()


def run_pipeline(change_event: dict) -> dict:
    """
    Run the documentation pipeline for a git change event.
    
    Args:
        change_event: Dictionary with commit_hash, files_changed, diff, etc.
    
    Returns:
        Final state after pipeline execution
    """
    commit_hash = change_event.get("commit_hash", "unknown")
    logger.info(f"run_pipeline: Starting for commit {commit_hash[:8]}")
    
    # Build initial state
    initial_state: DocuMindState = {
        "change_event": change_event,
        "analysis_result": None,
        "docs_written": [],
        "query_response": None,
        "error": None,
    }
    
    # Configure checkpointing with commit_hash as thread_id
    config = {"configurable": {"thread_id": commit_hash}}
    
    # Run graph
    try:
        final_state = app.invoke(initial_state, config)
        
        if final_state.get("error"):
            logger.error(f"run_pipeline: Pipeline failed with error: {final_state['error']}")
        else:
            logger.info(f"run_pipeline: Pipeline complete for commit {commit_hash[:8]}")
        
        return final_state
    
    except Exception as e:
        logger.error(f"run_pipeline: Unexpected error: {e}")
        return {**initial_state, "error": f"Pipeline error: {e}"}


# Made with Bob