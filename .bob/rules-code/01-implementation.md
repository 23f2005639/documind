# DocuMind — Code Mode Implementation Rules

## File Creation Pattern

When creating any new agent or store file:
1. Create Pydantic models first in `models/schemas.py`
2. Write the implementation file
3. Run the import check: `python -c "from <module> import <Class>; print('OK')"`
4. Wire into `agents/supervisor.py` StateGraph only after the module imports cleanly

## Agent Node Signature (LangGraph)

Every node function must follow this exact signature:

```python
def node_name(state: DocuMindState) -> dict:
    """Returns partial state update, never the full state."""
    try:
        # implementation
        return {"field_name": result}
    except Exception as e:
        logger.error(f"node_name failed: {e}")
        return {"error": str(e)}
```

## Doc Output Format

Generated documentation files must follow this exact structure:

```markdown
---
module: {module_name}
commit: {commit_hash}
generated_at: {iso_timestamp}
author: DocuMind
---

# {Module Name}

## Overview
{arch_summary}

## Architecture
{mermaid_flowchart if available}

## Functions

### `{function_name}({signature})`
{docstring}

**Dependencies:** {dep1}, {dep2}

## Usage Examples
{code_examples}

## Decision Log
{key_decisions}
```

## Qwen3 Coder Prompt Template

When calling the analyzer, use this exact prompt structure (do not deviate):

```python
ANALYZER_PROMPT = """You are analyzing a Python codebase for documentation purposes.

## Changed Files
{changed_files}

## Git Diff
{diff}

## Commit Message
{commit_msg}

## Full File Contents
{file_contents}

Respond with ONLY a JSON object matching this schema:
{schema_json}

Be precise. Include all function signatures, class names, and dependency relationships."""
```

## Streamlit UI Structure

```
st.sidebar → doc browser (tree view of docs/ directory)
main panel → chat interface
  - st.chat_input at bottom
  - st.chat_message for history
  - source citations as st.expander under each answer
```

## MCP Server Pattern

```python
# Uses mcp Python SDK (pip install mcp)
from mcp.server import Server
from mcp.server.stdio import stdio_server
import asyncio

server = Server("documind")

@server.list_tools()
async def list_tools():
    return [{"name": "query_docs", "description": "...", "inputSchema": {...}}]

@server.call_tool()
async def call_tool(name, arguments):
    if name == "query_docs":
        return query_agent.answer(arguments["question"])

asyncio.run(stdio_server(server))
```

## requirements.txt (exact content)

```
langgraph>=1.0
deepagents
langchain-openai
watchdog
gitpython
qdrant-client
duckdb
sentence-transformers
pydantic>=2.0
streamlit
python-dotenv
mcp
openai
```
