# DocuMind — Technology Conventions (All Modes)

## OpenRouter LLM Access

- ALWAYS use the `llm()` factory function from `agents/supervisor.py` — never instantiate `ChatOpenAI` directly
- Model IDs (exact strings, copy-paste):
  - Analyzer: `"qwen/qwen3-coder:free"`
  - Supervisor: `"deepseek/deepseek-r1:free"`
  - Writer: `"deepseek/deepseek-chat-v3:free"`
  - Query: `"meta-llama/llama-4-scout:free"`
  - Fallback: `"google/gemini-2.5-pro-exp:free"`
- Temperature: `0.1` for code/analysis, `0.3` for documentation writing
- Rate limit awareness: add 1-second sleep between rapid successive calls

## LangGraph 1.0

- State class: always `TypedDict`, never `dataclass` or Pydantic
- List fields in state that accumulate: use `Annotated[list[str], operator.add]`
- Checkpointer: `MemorySaver()` for development (saves to RAM)
- Thread ID for checkpointing: `{"configurable": {"thread_id": commit_hash}}`
- Never use deprecated `graph.set_finish_point()` — use `graph.add_edge("node", END)`
- Compile: `app = graph.compile(checkpointer=MemorySaver())`

## Qdrant

- ALWAYS use local mode: `QdrantClient(path=".qdrant")` — never connect to a server
- Collection name: `"documind_docs"` (constant in `store/qdrant_store.py`)
- Vector dimension: `768` (nomic-embed-text output size)
- Distance metric: `Distance.COSINE`
- Upsert, never insert: use `client.upsert()` for idempotency
- Payload fields to always include: `module_name`, `section`, `commit_hash`, `doc_path`, `text`

## nomic-embed-text

- Model: `"nomic-ai/nomic-embed-text-v1.5"` with `trust_remote_code=True`
- Document prefix: `"search_document: "` prepended to all docs being indexed
- Query prefix: `"search_query: "` prepended to user questions at query time
- Always normalize embeddings: `normalize_embeddings=True`
- Initialize once (module-level singleton), not per call

## DuckDB

- Connection: `duckdb.connect("documind.db")` — single file, no server
- Always use parametrized queries: `con.execute("SELECT * FROM docs WHERE module = ?", [module])`
- Schema: `docs(id VARCHAR PK, path VARCHAR, module VARCHAR, commit_hash VARCHAR, generated_at TIMESTAMP, word_count INTEGER)`
- Use `INSERT OR REPLACE` for upserts

## DeepAgents

- Import: `from deepagents import create_deep_agent`
- Tools for writer: `[write_file, read_file, list_files]`
- Pass structured context as JSON string in the task description
- The agent will write files autonomously — check the output directory after invocation

## GitPython

- Repo: `git.Repo(search_parent_directories=True)`
- Latest diff: `repo.git.diff("HEAD~1", "HEAD")`
- Latest commit: `repo.head.commit` → `.hexsha`, `.message`, `.author.name`
- Changed files: `[item.a_path for item in repo.head.commit.diff("HEAD~1")]`

## Watchdog

- Observer: `watchdog.observers.Observer()`
- Handler: subclass `watchdog.events.FileSystemEventHandler`
- Watch: `observer.schedule(handler, path=watched_dir, recursive=True)`
- Ignore: `.git/`, `docs/`, `__pycache__/`, `.qdrant/`
