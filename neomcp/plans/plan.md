# Web Search Agent — Rebuild & Optimize

## Goal
Recreate the full web search agent project inside `neo mcp/` with all 10 bugs fixed, proper type hints, error handling, retry logic, cache-read support, and tests that pass without real API keys.

## Research Summary
- Existing project uses: requests, pytest, python-dotenv (unused), SerpAPI, OpenRouter API
- All bug descriptions and required fixes were provided by the user in the task spec
- No external research needed — the fixes are well-specified architectural improvements

## Approach
Create a clean copy of the project structure under `neo mcp/` applying all fixes simultaneously:

1. **config.py**: Call `load_dotenv()` at module init, use `os.getenv` with defaults instead of `os.environ[]`, make LLM_MODEL and RESULT_LIMIT env-overridable
2. **search/client.py**: Use `requests.Session` with 10s timeout, add tenacity retry (3 attempts, exponential backoff on 429/5xx/timeout/connection errors)
3. **search/parser.py**: Safe key access with `.get()`, handle missing `organic_results` gracefully
4. **llm/client.py**: Same session+retry pattern, handle HTTP/JSON errors
5. **llm/prompts.py**: Use f-strings
6. **agent/runner.py**: Check `retrieve(query)` before calling search, wrap in error handling
7. **agent/memory.py**: Unchanged logic (already correct)
8. **main.py**: Add `load_dotenv()` before any imports
9. **tests/conftest.py**: Set dummy env vars before any imports
10. **tests/**: Update mock patch paths (`_session.get` / `_session.post`), add cache test

## Subtasks

1. Create directory structure `neo mcp/src/{search,llm,agent}/` and `neo mcp/tests/` with `__init__.py` files
2. Write `neo mcp/src/config.py` — lazy env reads, load_dotenv at module init, env-overridable model and result limit
3. Write `neo mcp/src/search/client.py` — Session-based, retry with tenacity, 10s timeout
4. Write `neo mcp/src/search/parser.py` — safe key access with .get()
5. Write `neo mcp/src/llm/client.py` — Session-based, retry, error handling
6. Write `neo mcp/src/llm/prompts.py` — f-strings
7. Write `neo mcp/src/agent/memory.py` — same as original (already correct)
8. Write `neo mcp/src/agent/runner.py` — check cache first, wrap in try/except
9. Write `neo mcp/main.py` — CLI entrypoint with load_dotenv()
10. Write `neo mcp/requirements.txt` — add tenacity
11. Write `neo mcp/.env.example` — two keys
12. Write `neo mcp/README.md` — updated with new features
13. Write `neo mcp/tests/conftest.py` — dummy env vars
14. Write `neo mcp/tests/test_search.py` — updated mock paths
15. Write `neo mcp/tests/test_llm.py` — updated mock paths, test cache retrieval
16. Write `neo mcp/tests/test_agent.py` — updated mock paths, test cache hit path
17. Run `pytest tests/` inside neo mcp/ and fix any failures

## Deliverables
| File Path | Description |
|-----------|-------------|
| neo mcp/main.py | CLI entrypoint |
| neo mcp/requirements.txt | deps incl. tenacity |
| neo mcp/.env.example | template |
| neo mcp/README.md | updated docs |
| neo mcp/src/__init__.py | package init |
| neo mcp/src/config.py | lazy env config |
| neo mcp/src/search/__init__.py | subpackage init |
| neo mcp/src/search/client.py | retry-capable search |
| neo mcp/src/search/parser.py | safe result parser |
| neo mcp/src/llm/__init__.py | subpackage init |
| neo mcp/src/llm/client.py | retry-capable LLM |
| neo mcp/src/llm/prompts.py | f-string prompts |
| neo mcp/src/agent/__init__.py | subpackage init |
| neo mcp/src/agent/memory.py | dict cache |
| neo mcp/src/agent/runner.py | cache-first orchestrator |
| neo mcp/tests/__init__.py | test package |
| neo mcp/tests/conftest.py | env setup |
| neo mcp/tests/test_search.py | search tests |
| neo mcp/tests/test_llm.py | LLM tests |
| neo mcp/tests/test_agent.py | agent tests |

## Evaluation Criteria
- All 20 files exist in `neo mcp/`
- `pytest tests/` from `neo mcp/` passes all tests without real API keys
- Cache is checked before search: repeated identical queries skip API calls
- Retry logic retries up to 3 times on 429/5xx/timeout
- LLM model overridable via `LLM_MODEL` env var
- `RESULT_LIMIT` overridable via env var
- No string concatenation in prompts — f-strings only
- `.env` loaded automatically via `load_dotenv()`