# DocuMind — General Rules (All Modes)

## Code Style

- Python 3.11+ syntax only
- Type hints on every function signature and class attribute
- Pydantic v2 for all data models (use `model_dump_json()` not `.dict()`)
- 4 spaces for indentation, no tabs
- Max line length: 100 characters
- f-strings for string formatting, never `.format()` or `%`

## Naming Conventions

- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions and variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private helpers: `_single_leading_underscore`

## Environment Variables

- Never hardcode API keys — always use `os.getenv("OPENROUTER_API_KEY")`
- Load `.env` at the top of `main.py` using `python-dotenv` (`load_dotenv()`)
- All config through environment variables, no config files

## Error Handling

- Never use bare `except:` — always catch specific exceptions
- Log errors before handling: `logging.error(f"...: {e}")`
- LangGraph nodes must never raise — catch and return state with `error` field set
- External API calls: always wrap in try/except with informative error messages

## Logging

- Use `logging` module, not `print()` for agent output
- Set up at top of `main.py`: `logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")`
- Each agent file: `logger = logging.getLogger(__name__)`

## Imports

Order: (1) standard library, (2) third-party, (3) local. Blank line between each group.

## Tests / Verification

After writing any file, always run: `python -c "from <module> import <MainClass>; print('OK')"` to verify it imports cleanly.
