# Watcher Agent + LangGraph Supervisor — Implementation Plan

## Requirements Confirmation ✓

**Watcher Agent:**
- ✓ Uses watchdog `Observer` + GitPython (no LLM)
- ✓ Emits [`ChangeEvent`](models/schemas.py:7) Pydantic model on every filesystem change
- ✓ Extracts git diff, commit metadata, changed files list

**LangGraph Supervisor:**
- ✓ LangGraph 1.0 `StateGraph` with `MemorySaver` checkpointing
- ✓ Node flow: `watcher → analyzer → writer → indexer → END`
- ✓ `DocuMindState` TypedDict shared across all nodes
- ✓ Uses `llm()` factory for all OpenRouter model access

---

## 4-Step Implementation Plan

### Step 1: Implement Watcher Agent (`agents/watcher.py`)

**Goal:** File-system monitoring that emits [`ChangeEvent`](models/schemas.py:7) on git commits.

**Components:**
```python
class DocuMindEventHandler(FileSystemEventHandler):
    """Watchdog handler that filters for .py files, ignores .git/docs/"""
    
class GitWatcher:
    """Main watcher class with Observer + GitPython integration"""
    - __init__(repo_path: str, callback: Callable[[ChangeEvent], None])
    - start() → starts Observer thread
    - stop() → graceful shutdown
    - _on_file_change() → builds ChangeEvent from git diff
```

**Key Logic:**
1. Watchdog detects file modification → triggers handler
2. Handler checks if file is `.py` and not in ignore list
3. GitPython extracts: `repo.git.diff("HEAD~1", "HEAD")`, `repo.head.commit`
4. Build [`ChangeEvent`](models/schemas.py:7) with all metadata
5. Invoke callback (supervisor's `process_change()` method)

**Integration Points:**
- Callback receives [`ChangeEvent`](models/schemas.py:7) → triggers supervisor graph
- Ignore patterns: `.git/`, `docs/`, `__pycache__/`, `.qdrant/`, `*.db`

**Tricky Parts:**
- ⚠️ **Race condition:** File change detected before git commit completes
  - **Solution:** Add 2-second debounce delay before extracting git diff
- ⚠️ **Initial commit:** `HEAD~1` doesn't exist on first commit
  - **Solution:** Catch `GitCommandError`, use `repo.git.diff("HEAD")` as fallback
- ⚠️ **Multiple rapid changes:** Watchdog fires multiple events for same commit
  - **Solution:** Track last processed `commit_hash`, skip duplicates

---

### Step 2: Define `DocuMindState` TypedDict + `llm()` Factory (`agents/supervisor.py`)

**Goal:** Shared state contract and LLM access pattern for all nodes.

**DocuMindState TypedDict:**
```python
from typing import TypedDict, Annotated
import operator

class DocuMindState(TypedDict):
    # Input from watcher
    change_event: ChangeEvent
    
    # Analyzer output
    analysis_result: AnalysisResult | None
    
    # Writer output
    doc_path: str | None
    doc_content: str | None
    
    # Indexer output
    indexed: bool
    
    # Error tracking (accumulates across nodes)
    errors: Annotated[list[str], operator.add]
    
    # Metadata
    commit_hash: str  # Used as thread_id for checkpointing
```

**llm() Factory Function:**
```python
def llm(model_id: str, temperature: float = 0.1) -> ChatOpenAI:
    """Factory for OpenRouter LLM access. All agents use this."""
    return ChatOpenAI(
        model=model_id,
        temperature=temperature,
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
    )
```

**Model Constants:**
```python
ANALYZER_MODEL = "qwen/qwen3-coder:free"
SUPERVISOR_MODEL = "deepseek/deepseek-r1:free"
WRITER_MODEL = "deepseek/deepseek-chat-v3:free"
QUERY_MODEL = "meta-llama/llama-4-scout:free"
FALLBACK_MODEL = "google/gemini-2.5-pro-exp:free"
```

**Integration Points:**
- All nodes receive `DocuMindState`, return modified `DocuMindState`
- `commit_hash` used as LangGraph thread ID for checkpointing
- `errors` list accumulates across nodes (never crashes pipeline)

**Tricky Parts:**
- ⚠️ **TypedDict vs Pydantic:** LangGraph 1.0 requires TypedDict, not Pydantic
  - **Solution:** Use `TypedDict` for state, Pydantic for data models only
- ⚠️ **Optional fields:** `analysis_result`, `doc_path` start as `None`
  - **Solution:** Nodes check for `None` before accessing nested fields

---

### Step 3: Build LangGraph StateGraph with Nodes (`agents/supervisor.py`)

**Goal:** Orchestrate watcher → analyzer → writer → indexer flow.

**Node Functions:**
```python
def watcher_node(state: DocuMindState) -> DocuMindState:
    """Entry point: receives ChangeEvent from GitWatcher callback"""
    # Already populated by process_change(), just pass through
    return state

def analyzer_node(state: DocuMindState) -> DocuMindState:
    """Calls analyzer.py analyze_code() with Qwen3 Coder"""
    try:
        from agents.analyzer import analyze_code
        result = analyze_code(state["change_event"])
        return {**state, "analysis_result": result}
    except Exception as e:
        logger.error(f"Analyzer failed: {e}")
        return {**state, "errors": [f"Analyzer: {e}"]}

def writer_node(state: DocuMindState) -> DocuMindState:
    """Calls writer.py generate_docs() with DeepAgents + DeepSeek V3"""
    try:
        from agents.writer import generate_docs
        doc_path, content = generate_docs(state["analysis_result"])
        return {**state, "doc_path": doc_path, "doc_content": content}
    except Exception as e:
        logger.error(f"Writer failed: {e}")
        return {**state, "errors": [f"Writer: {e}"]}

def indexer_node(state: DocuMindState) -> DocuMindState:
    """Embeds + upserts to Qdrant + DuckDB"""
    try:
        from store.qdrant_store import index_document
        from store.duckdb_store import save_metadata
        index_document(state["doc_content"], state["commit_hash"])
        save_metadata(state["doc_path"], state["commit_hash"])
        return {**state, "indexed": True}
    except Exception as e:
        logger.error(f"Indexer failed: {e}")
        return {**state, "errors": [f"Indexer: {e}"]}
```

**Graph Construction:**
```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

def create_supervisor_graph() -> StateGraph:
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
```

**Integration Points:**
- `GitWatcher` callback invokes `app.invoke(initial_state, config={"configurable": {"thread_id": commit_hash}})`
- Each node imports its agent module (analyzer, writer, store modules)
- Checkpointer saves state after each node (crash recovery)

**Tricky Parts:**
- ⚠️ **Circular imports:** supervisor imports analyzer/writer, they might import supervisor
  - **Solution:** Import agent functions inside node functions (lazy import)
- ⚠️ **Node exceptions:** Must never raise, always return state with error
  - **Solution:** Wrap every node body in try/except, append to `errors` list
- ⚠️ **Checkpointing thread_id:** Must be unique per commit
  - **Solution:** Use `commit_hash` from [`ChangeEvent`](models/schemas.py:7) as thread_id

---

### Step 4: Wire Up MemorySaver + Test End-to-End (`main.py`)

**Goal:** Entry point that starts watcher, processes events through supervisor.

**main.py Structure:**
```python
import logging
from dotenv import load_dotenv
from agents.watcher import GitWatcher
from agents.supervisor import create_supervisor_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

def main(repo_path: str = "."):
    load_dotenv()
    
    # Create supervisor graph
    app = create_supervisor_graph()
    
    # Define callback for watcher
    def process_change(event: ChangeEvent):
        logger.info(f"Processing commit {event.commit_hash[:8]}")
        initial_state = {
            "change_event": event,
            "analysis_result": None,
            "doc_path": None,
            "doc_content": None,
            "indexed": False,
            "errors": [],
            "commit_hash": event.commit_hash,
        }
        config = {"configurable": {"thread_id": event.commit_hash}}
        
        # Run graph
        final_state = app.invoke(initial_state, config)
        
        if final_state["errors"]:
            logger.error(f"Errors: {final_state['errors']}")
        else:
            logger.info(f"✓ Doc generated: {final_state['doc_path']}")
    
    # Start watcher
    watcher = GitWatcher(repo_path, process_change)
    watcher.start()
    
    logger.info(f"Watching {repo_path} for changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        watcher.stop()

if __name__ == "__main__":
    import sys
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    main(repo_path)
```

**Integration Points:**
- `GitWatcher` callback receives [`ChangeEvent`](models/schemas.py:7) → builds initial state
- `app.invoke()` runs entire graph synchronously (watcher → analyzer → writer → indexer)
- Logs progress and errors to console

**Tricky Parts:**
- ⚠️ **Blocking callback:** `app.invoke()` blocks watcher thread during processing
  - **Solution:** Acceptable for MVP (one commit at a time). Future: use `asyncio` + `app.ainvoke()`
- ⚠️ **Missing .env:** OpenRouter API key not loaded
  - **Solution:** Check `os.getenv("OPENROUTER_API_KEY")` at startup, exit with error if missing
- ⚠️ **First run:** No git history, `HEAD~1` fails
  - **Solution:** Watcher handles this in Step 1 (fallback to `HEAD` diff)

---

## Integration Risk Matrix

| Risk | Severity | Mitigation |
|------|----------|------------|
| Watchdog fires before git commit completes | HIGH | 2-second debounce delay in watcher |
| Circular imports (supervisor ↔ analyzer/writer) | MEDIUM | Lazy imports inside node functions |
| LangGraph 1.0 TypedDict requirement | MEDIUM | Use TypedDict for state, Pydantic for data models |
| Node exceptions crash pipeline | HIGH | Wrap all nodes in try/except, return state with errors |
| OpenRouter rate limits (20 req/min) | LOW | 1-second sleep between LLM calls, exponential backoff |
| MemorySaver RAM usage on long sessions | LOW | Acceptable for hackathon (48 hours max runtime) |
| Multiple rapid commits (same file) | MEDIUM | Track last `commit_hash`, skip duplicates |
| Initial commit (`HEAD~1` doesn't exist) | MEDIUM | Fallback to `HEAD` diff in GitPython error handler |

---

## Testing Strategy

**Unit Tests (per step):**
1. Watcher: Mock git repo, trigger file change, verify [`ChangeEvent`](models/schemas.py:7) emitted
2. Supervisor: Mock nodes, verify state flows through graph correctly
3. Nodes: Mock LLM responses, verify state transformations
4. End-to-end: Real git repo, commit change, verify doc generated

**Manual Test (Step 4):**
```bash
# Terminal 1: Start watcher
python main.py /path/to/test-repo

# Terminal 2: Make a change
cd /path/to/test-repo
echo "def hello(): pass" >> test.py
git add test.py
git commit -m "add hello function"

# Terminal 1: Should see:
# INFO Processing commit abc12345
# INFO ✓ Doc generated: docs/test/index.md
```

---

## Next Steps After This Plan

1. Switch to **DocuMind Dev** mode (or Code mode)
2. Implement Step 1 (watcher.py)
3. Verify watcher emits [`ChangeEvent`](models/schemas.py:7) correctly
4. Implement Step 2 (supervisor.py state + llm factory)
5. Implement Step 3 (supervisor.py graph nodes)
6. Implement Step 4 (main.py entry point)
7. Run manual test with real git repo
8. Fix any integration issues discovered during testing

**Estimated Time:** 3–4 hours for all 4 steps + testing.