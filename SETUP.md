# DocuMind — Setup Guide

## ✅ Completed Setup Steps

All 5 initial setup steps are complete:

### 1. Directory Structure ✓
```
documind/
├── agents/
│   ├── __init__.py
│   ├── watcher.py       # watchdog Observer + GitPython
│   ├── supervisor.py    # LangGraph StateGraph orchestrator
│   ├── analyzer.py      # Qwen3 Coder 480B analysis
│   ├── writer.py        # DeepAgents + DeepSeek V3 doc writer
│   └── query.py         # Qdrant RAG + Llama 4 Scout
├── store/
│   ├── __init__.py
│   ├── qdrant_store.py  # Vector database wrapper
│   └── duckdb_store.py  # Metadata store
├── models/
│   ├── __init__.py
│   └── schemas.py       # Pydantic v2 data models
├── mcp_server/
│   ├── __init__.py
│   └── server.py        # MCP server for IBM Bob
├── ui/
│   ├── __init__.py
│   └── app.py           # Streamlit chat interface
├── docs/                # Generated documentation (gitignored)
├── .bob/                # IBM Bob configuration
├── .venv/               # Python virtual environment
├── .env.example         # API key template
├── .bobignore           # Security exclusions
├── main.py              # Entry point
├── requirements.txt     # Dependencies
└── test_llms.py         # OpenRouter verification script
```

### 2. Dependencies (requirements.txt) ✓
```
langgraph>=1.0          # Agent orchestration
deepagents              # Agent harness with file tools
langchain-openai        # LLM access
watchdog                # File system monitoring
gitpython               # Git integration
qdrant-client           # Vector database
duckdb                  # Metadata store
sentence-transformers   # Local embeddings (nomic-embed-text)
pydantic>=2.0           # Data validation
streamlit               # UI framework
python-dotenv           # Environment variables
mcp                     # Model Context Protocol
openai                  # OpenAI SDK (for OpenRouter)
```

**Installation Status:** Currently installing (torch + CUDA dependencies downloading)

### 3. Security Configuration ✓

**`.env.example`** (template):
```bash
OPENROUTER_API_KEY=sk-or-your-key-here
```

**`.bobignore`** (excludes sensitive files):
```
.env
.qdrant/
docs/
__pycache__/
*.db
.venv/
*.pyc
.pytest_cache/
```

### 4. Data Models (models/schemas.py) ✓

Four Pydantic v2 models implemented:

```python
class ChangeEvent(BaseModel):
    """Git change event from watchdog"""
    files_changed: list[str]
    diff: str
    commit_msg: str
    commit_hash: str
    timestamp: str
    author: str

class FunctionInfo(BaseModel):
    """Analyzed function metadata"""
    name: str
    signature: str
    docstring: str
    dependencies: list[str]

class AnalysisResult(BaseModel):
    """Output from Analyzer agent"""
    module_name: str
    functions: list[FunctionInfo]
    classes: list[str]
    arch_summary: str
    dependencies: list[str]
    data_flows: list[str]

class DocChunk(BaseModel):
    """Embedded documentation chunk for Qdrant"""
    content: str
    module_name: str
    section: str
    commit_hash: str
    doc_path: str
```

### 5. LLM Verification Script (test_llms.py) ✓

Tests all 5 OpenRouter models:
- Analyzer: `qwen/qwen3-coder:free` (480B, 262K context)
- Supervisor: `deepseek/deepseek-r1:free` (best reasoning)
- Writer: `deepseek/deepseek-chat-v3:free` (best writing)
- Query: `meta-llama/llama-4-scout:free` (fast Q&A)
- Fallback: `google/gemini-2.5-pro-exp:free` (1M context)

---

## 🚀 Next Steps (Manual Verification)

### Step 1: Wait for pip installation to complete
The terminal is currently downloading large packages (torch 532MB, CUDA libraries 366MB). This may take 5-10 minutes depending on your internet speed.

### Step 2: Verify imports
Once installation completes, run:
```bash
.venv/bin/python -c "import langgraph, deepagents, qdrant_client, duckdb, watchdog, git, streamlit; print('✓ All imports OK')"
```

### Step 3: Verify Pydantic models
```bash
.venv/bin/python -c "from models.schemas import ChangeEvent, AnalysisResult, DocChunk, FunctionInfo; print('✓ Schemas OK')"
```

### Step 4: Set up OpenRouter API key
1. Get your API key from https://openrouter.ai/settings/keys
2. Create `.env` file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your key:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
   ```

### Step 5: Test LLM access
```bash
.venv/bin/python test_llms.py
```

Expected output:
```
Testing OpenRouter LLM access...

✓ Analyzer     (qwen/qwen3-coder:free): OK
✓ Supervisor   (deepseek/deepseek-r1:free): OK
✓ Writer       (deepseek/deepseek-chat-v3:free): OK
✓ Query        (meta-llama/llama-4-scout:free): OK
✓ Fallback     (google/gemini-2.5-pro-exp:free): OK

============================================================
Result: 5/5 models accessible
============================================================
✓ All models working! Ready to build DocuMind.
```

---

## 📋 Implementation Roadmap

### Phase 1: Core Pipeline (Hours 0-24)
- [ ] `agents/watcher.py` — File system monitoring + Git integration
- [ ] `agents/supervisor.py` — LangGraph StateGraph orchestrator
- [ ] `agents/analyzer.py` — Qwen3 Coder code analysis
- [ ] `agents/writer.py` — DeepAgents documentation generation
- [ ] `store/qdrant_store.py` — Vector storage wrapper
- [ ] `store/duckdb_store.py` — Metadata storage

### Phase 2: Query & UI (Hours 24-36)
- [ ] `agents/query.py` — RAG-based Q&A
- [ ] `ui/app.py` — Streamlit chat interface
- [ ] `main.py` — Entry point and CLI

### Phase 3: MCP Integration (Hours 36-42)
- [ ] `mcp_server/server.py` — IBM Bob integration
- [ ] Test with Bob IDE

### Phase 4: Polish (Hours 42-48)
- [ ] Mermaid diagram generation
- [ ] File hash caching
- [ ] Error handling improvements
- [ ] Demo video recording

---

## 🔧 Troubleshooting

### Import Errors
If any package fails to import, install individually:
```bash
.venv/bin/pip install <package-name>
```

### OpenRouter Rate Limits
- Free tier: 20 requests/minute, 200 requests/day per model
- Add 3-second delays between rapid calls
- Implement exponential backoff in supervisor

### Qdrant Permissions
If `.qdrant/` directory creation fails:
```bash
mkdir -p .qdrant
chmod 755 .qdrant
```

### sentence-transformers Model Download
First run downloads nomic-embed-text (1.5GB):
```bash
.venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('nomic-ai/nomic-embed-text-v1.5', trust_remote_code=True)"
```

---

## 📊 Project Status

**Setup Phase:** ✅ Complete  
**Core Implementation:** ⏳ Ready to start  
**Deadline:** May 17, 2026 (48 hours from now)  
**Budget:** 40 Bobcoins (efficient usage required)

---

## 🎯 Success Criteria

1. ✅ Directory structure created
2. ✅ Dependencies defined
3. ✅ Security configured
4. ✅ Data models implemented
5. ✅ LLM test script ready
6. ⏳ Dependencies installed (in progress)
7. ⏳ Imports verified (pending)
8. ⏳ OpenRouter access tested (pending)
9. ⏳ Core agents implemented (next phase)
10. ⏳ Demo ready (final phase)

**Current Status:** 5/10 complete (50%)