# DocuMind — Code Mode Context

> Loaded by Bob in Code mode. Extends AGENTS.md with implementation-specific context.

## Implementation State

Track which agents are complete:
- [ ] `agents/watcher.py` — ChangeEvent emitter
- [ ] `agents/supervisor.py` — LangGraph StateGraph
- [ ] `agents/analyzer.py` — Qwen3 Coder analysis
- [ ] `agents/writer.py` — DeepAgents doc writer
- [ ] `agents/query.py` — Qdrant RAG
- [ ] `store/qdrant_store.py` — vector store wrapper
- [ ] `store/duckdb_store.py` — metadata store
- [ ] `models/schemas.py` — Pydantic models
- [ ] `ui/app.py` — Streamlit UI
- [ ] `mcp_server/server.py` — MCP server
- [ ] `main.py` — entry point

## LangGraph StateGraph Pattern

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Optional, Annotated
import operator

class DocuMindState(TypedDict):
    change_event: Optional[dict]
    analysis_result: Optional[dict]
    docs_written: Annotated[list[str], operator.add]
    query_response: Optional[str]
    error: Optional[str]

graph = StateGraph(DocuMindState)
graph.add_node("watcher", watcher_node)
graph.add_node("analyzer", analyzer_node)
graph.add_node("writer", writer_node)
graph.add_node("indexer", indexer_node)
graph.set_entry_point("watcher")
graph.add_edge("watcher", "analyzer")
graph.add_edge("analyzer", "writer")
graph.add_edge("writer", "indexer")
graph.add_edge("indexer", END)
app = graph.compile(checkpointer=MemorySaver())
```

## LLM Factory Pattern (always use this, never instantiate ChatOpenAI directly)

```python
import os
from langchain_openai import ChatOpenAI

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

def llm(model: str, temperature: float = 0.1) -> ChatOpenAI:
    return ChatOpenAI(
        base_url=OPENROUTER_BASE,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        model=model,
        temperature=temperature,
    )
```

## Qdrant Local Mode Pattern

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(path=".qdrant")  # local, no server
COLLECTION = "documind_docs"
VECTOR_DIM = 768  # nomic-embed-text dimension

client.recreate_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
)
```

## nomic-embed-text Pattern

```python
from sentence_transformers import SentenceTransformer

encoder = SentenceTransformer(
    "nomic-ai/nomic-embed-text-v1.5",
    trust_remote_code=True
)

def embed(text: str) -> list[float]:
    return encoder.encode(
        f"search_document: {text}",  # nomic requires this prefix for docs
        normalize_embeddings=True
    ).tolist()

def embed_query(text: str) -> list[float]:
    return encoder.encode(
        f"search_query: {text}",     # different prefix for queries
        normalize_embeddings=True
    ).tolist()
```

## DuckDB Pattern

```python
import duckdb

con = duckdb.connect("documind.db")
con.execute("""
    CREATE TABLE IF NOT EXISTS docs (
        id VARCHAR PRIMARY KEY,
        path VARCHAR,
        module VARCHAR,
        commit_hash VARCHAR,
        generated_at TIMESTAMP DEFAULT now(),
        word_count INTEGER,
        section_count INTEGER
    )
""")
```

## DeepAgents Writer Pattern

```python
from deepagents import create_deep_agent
from deepagents.tools import write_file, read_file, list_files

writer_agent = create_deep_agent(
    llm=llm("deepseek/deepseek-chat-v3:free"),
    tools=[write_file, read_file, list_files],
    system_prompt="You are a technical documentation writer...",
)

result = writer_agent.invoke({
    "task": f"Write Notion-style documentation for {module_name}",
    "context": analysis_result.model_dump_json(),
})
```

## File Hash Cache Pattern

```python
import hashlib

def file_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

CACHE: dict[str, str] = {}  # path → last hash

def needs_analysis(path: str) -> bool:
    h = file_hash(path)
    if CACHE.get(path) == h:
        return False
    CACHE[path] = h
    return True
```

## Import Order (follow this in every file)

```python
# 1. Standard library
import os, hashlib, json
from typing import Optional, TypedDict
from pathlib import Path

# 2. Third-party
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

# 3. Local
from models.schemas import ChangeEvent, AnalysisResult
from store.qdrant_store import QdrantStore
```
