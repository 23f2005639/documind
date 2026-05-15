# DocuMind — Project Context for IBM Bob

> Auto-loaded by Bob at the start of every conversation. Do not delete.
> Re-run `/init` after structural changes to regenerate this file.

## Project Purpose

DocuMind is a multi-agent AI codebase documentation engine built for the IBM BOB Hackathon (May 15–17, 2026, lablab.ai). It continuously watches a Git repository, generates structured Notion-style documentation on every commit, and makes documentation queryable via natural language — so new engineers understand any codebase without spending weeks reading code.

## Architecture

```
Git Repo → watchdog + git hook
  ↓ ChangeEvent
LangGraph 1.0 Supervisor (DeepSeek R1 free)
  ↓ dispatches to
  ├── Analyzer Agent (Qwen3 Coder 480B, 262K ctx) → AnalysisResult
  └── Writer Agent (DeepAgents + DeepSeek V3) → docs/{module}/index.md
        ↓
  Storage: Qdrant (vectors) + DuckDB (metadata)
        ↓
  Query Agent (Llama 4 Scout + Qdrant RAG) ← Streamlit UI
        ↓
  [Bonus] MCP Server → IBM Bob IDE queries DocuMind while coding
```

## File Structure

```
documind/
├── agents/
│   ├── watcher.py       # watchdog Observer + GitPython → emits ChangeEvent
│   ├── supervisor.py    # LangGraph 1.0 StateGraph, MemorySaver, routes events
│   ├── analyzer.py      # Qwen3 Coder 480B via OpenRouter → AnalysisResult
│   ├── writer.py        # DeepAgents + DeepSeek V3 → Notion markdown docs
│   └── query.py         # Qdrant RAG + Llama 4 Scout → answers with sources
├── store/
│   ├── qdrant_store.py  # local Qdrant client, nomic-embed-text embeddings
│   └── duckdb_store.py  # doc metadata: path, module, commit_hash, generated_at
├── models/
│   └── schemas.py       # Pydantic models: ChangeEvent, AnalysisResult, DocChunk
├── mcp_server/
│   └── server.py        # MCP server exposing query_docs() tool for IBM Bob
├── ui/
│   └── app.py           # Streamlit chat UI + doc browser sidebar
├── docs/                # Generated documentation output (gitignored)
├── .bob/                # IBM Bob configuration (rules, modes, MCP)
├── .env                 # OPENROUTER_API_KEY (never commit)
├── .bobignore           # Excludes: .env, docs/, .qdrant/, *.db
├── main.py              # Entry point: starts watcher + supervisor
└── requirements.txt
```

## Tech Stack

| Component | Package | Version |
|-----------|---------|---------|
| Agent orchestration | `langgraph` | 1.0.x |
| Agent harness | `deepagents` | latest |
| LLM access | `langchain-openai` | latest |
| File watching | `watchdog` | latest |
| Git integration | `gitpython` | latest |
| Vector database | `qdrant-client` | latest |
| Metadata store | `duckdb` | latest |
| Embeddings | `sentence-transformers` | latest |
| Data validation | `pydantic` | v2 |
| UI | `streamlit` | latest |

## LLM Model Assignments

```python
# All models accessed via the llm() factory in agents/supervisor.py
analyzer_llm   = llm("qwen/qwen3-coder:free")          # 480B, 262K ctx
supervisor_llm = llm("deepseek/deepseek-r1:free")       # best reasoning
writer_llm     = llm("deepseek/deepseek-chat-v3:free")  # best writing
query_llm      = llm("meta-llama/llama-4-scout:free")   # fast Q&A
fallback_llm   = llm("google/gemini-2.5-pro-exp:free")  # 1M ctx fallback
```

## Environment

```bash
# .env (required)
OPENROUTER_API_KEY=sk-or-...

# OpenRouter base URL
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Python: 3.11+
# Qdrant: local mode only (path=".qdrant") — no server
# DuckDB: in-process (import duckdb) — no server
```

## Core Data Models (models/schemas.py)

```python
class ChangeEvent(BaseModel):
    files_changed: list[str]
    diff: str
    commit_msg: str
    commit_hash: str
    timestamp: str
    author: str

class FunctionInfo(BaseModel):
    name: str
    signature: str
    docstring: str
    dependencies: list[str]

class AnalysisResult(BaseModel):
    module_name: str
    functions: list[FunctionInfo]
    classes: list[str]
    arch_summary: str
    dependencies: list[str]
    data_flows: list[str]

class DocChunk(BaseModel):
    content: str
    module_name: str
    section: str
    commit_hash: str
    doc_path: str
```

## Key Patterns

- **State**: `DocuMindState` TypedDict flows through all LangGraph nodes
- **Checkpointing**: `MemorySaver` on the supervisor graph for crash recovery
- **Caching**: File content hashed (SHA256) before analysis — skip unchanged files
- **Embedding**: `nomic-ai/nomic-embed-text-v1.5` via sentence-transformers (local, offline)
- **Error handling**: All agent nodes catch exceptions, log them, return partial results

## IBM Bob Session

This project is built with IBM Bob (BobShell). Export the session report from Bob Settings before submission. Every coding session should use Bob's Code or Advanced mode. Screenshot BobShell prompts for the demo video.
