# DocuMind — Plan Mode Context

> Loaded by Bob in Plan mode. Use this mode for architecture decisions before writing code.

## Architecture Decisions (Already Made)

| Decision | Choice | Reason |
|----------|--------|--------|
| Agent framework | LangGraph 1.0 StateGraph | Stable, checkpointing, streaming |
| Agent harness | DeepAgents | Built-in file tools, task planning |
| Code analysis LLM | qwen/qwen3-coder:free | 262K context, SOTA coding, free |
| Supervisor LLM | deepseek/deepseek-r1:free | Best free reasoning |
| Writing LLM | deepseek/deepseek-chat-v3:free | Best free writing quality |
| Query LLM | meta-llama/llama-4-scout:free | Fast, low latency |
| Vector DB | Qdrant local mode | No server, Rust-based, 3× faster than ChromaDB |
| Metadata DB | DuckDB | In-process, no server, SQL analytics |
| Embeddings | nomic-embed-text-v1.5 | Best local model, free, offline |
| File watching | watchdog + GitPython | Cross-platform, rich git context |
| UI | Streamlit | Demo-ready in hours |
| MCP transport | STDIO | Simplest, works locally |

## Constraints

- 48-hour hackathon deadline
- 40 Bobcoins total (be efficient)
- OpenRouter free tier: 20 req/min, 200 req/day per model
- All LLMs free — no cost for API calls
- Local-only: no cloud databases, no external services required to run demo

## MVP vs SHOULD vs NICE (Scope Discipline)

**MUST ship (hours 0–34):**
- watcher.py → supervisor.py → analyzer.py → writer.py
- qdrant_store.py + duckdb_store.py
- query.py + ui/app.py

**SHOULD ship (hours 34–42):**
- Mermaid diagrams in docs
- File hash cache (incremental analysis)
- MCP server for IBM Bob

**NICE if time (hours 42+):**
- Slack/Discord notifications
- Notion export

## Key Data Flows

```
1. INGESTION FLOW
   File change detected (watchdog) 
   → git diff extracted (GitPython)
   → ChangeEvent built
   → Supervisor routes to Analyzer
   → Qwen3 Coder 480B analyzes full context
   → AnalysisResult Pydantic model
   → Supervisor routes to Writer
   → DeepAgents + DeepSeek V3 generates doc
   → Written to docs/{module}/index.md
   → Embedded with nomic-embed-text
   → Upserted to Qdrant + DuckDB

2. QUERY FLOW
   User question (Streamlit chat)
   → Embedded with nomic-embed-text (query prefix)
   → Qdrant search: top-5 chunks
   → Llama 4 Scout synthesizes answer
   → Answer + source citations returned
```

## Error Handling Strategy

- All LangGraph nodes: catch exceptions, log, return partial state (never crash the pipeline)
- OpenRouter rate limits: exponential backoff with jitter, fallback to Gemini 2.5 Pro
- Qdrant: idempotent upserts (same doc can be indexed twice safely)
- DuckDB: upsert pattern (INSERT OR REPLACE)

## Demo Sequence (3 minutes)

1. Show terminal: `python main.py --watch /path/to/demo-repo` (watcher starts)
2. Edit a Python file in demo-repo (add a function)
3. `git commit -m "add authenticate function"`
4. Watch terminal: ChangeEvent → Analyzer → Writer → "Doc generated: docs/auth/index.md"
5. Open Streamlit: ask "What does the authenticate function do?"
6. Show answer with sources, click source → doc opens
7. Switch to IBM Bob IDE: ask Bob "How does authentication work in this project?"
8. Bob uses DocuMind MCP → answers from our docs (DEMO MONEY SHOT)
9. Show generated doc file, show Mermaid diagram rendering
