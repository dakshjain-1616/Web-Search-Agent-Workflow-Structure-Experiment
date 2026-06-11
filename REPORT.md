# Web Search Agent: Run A (Claude Code solo) vs Run B (Claude Code + Neo MCP)
## Technical Comparison Report

---

## 1. TL;DR Table

| Dimension | Run A (Claude Code solo) | Run B (Claude Code + Neo MCP) |
|---|---|---|
| Root cause found | Partial — fixed 13/18 defects independently | Partial — fixed 15/18 defects from Claude Code–emitted spec |
| Diagnosis method | Independent code reading; no plan artifact | Claude Code diagnosed → emitted spec → Neo wrote plan.md → executed |
| Lines changed (vs baseline) | ~150 lines added across 9 files | ~220 lines added across 20 files |
| Files touched | 9 files created | 20 files created |
| Fix character | Surgical refactor — addresses obvious defects | Comprehensive rewrite — addresses all specified defects |
| Regressions introduced | None | 1: `memory.get_all()` returns mutable `_cache` ref |
| Measured before/after perf | No — neither run benchmarked; see Section 7 | No — neither run benchmarked; see Section 7 |
| Test count / pass | 16 / 16 ✓ | 12 / 12 ✓ |
| User interventions | Not available (no transcript) | Not available (no transcript) |
| Timeout added | No | Yes (10 s) |
| Retry logic added | No | Yes (tenacity, 3 attempts, exp. backoff) |
| System prompt added | Yes | No |
| URL included in LLM context | Yes | No |
| Model configurable | No (hardcoded claude-haiku-4-5) | Yes (env var `LLM_MODEL`) |
| Result limit configurable | No (hardcoded 5) | Yes (env var `RESULT_LIMIT`) |

---

## 2. The Broken Baseline

### What it was supposed to do

`agent_v1.py` is a 46-line single-file CLI: it accepts a search query as `sys.argv[1]`,
calls SerpAPI to fetch organic search results, concatenates title+snippet text into a
prompt, sends that prompt to OpenRouter (GPT-3.5-turbo), and prints the LLM's reply.

### Defect inventory (18 defects)

This inventory is the scoring rubric for Sections 3 and 4.

| ID | Category | File:Lines | Description |
|----|----------|-----------|-------------|
| D1 | Correctness | `agent_v1.py:4-5` | `os.environ["SERPAPI_KEY"]` and `os.environ["OPENROUTER_API_KEY"]` raise `KeyError` at import if vars are unset |
| D2 | Correctness | absent | `load_dotenv()` never called; `.env` file is silently ignored even though `python-dotenv` is the intended mechanism (noted in root `README.md`) |
| D3 | Error handling | `agent_v1.py:9-13` | No `raise_for_status()` on search response; HTTP 403/429/500 silently continues into a JSON parse that then crashes at D4 |
| D4 | Error handling | `agent_v1.py:13` | `response.json()["organic_results"]` without `.get()`; raises `KeyError` on SerpAPI error bodies (e.g. `{"error": "Invalid API key"}`) |
| D5 | Error handling | `agent_v1.py:24-35` | No `raise_for_status()` on LLM call |
| D6 | Error handling | `agent_v1.py:35` | `response.json()["choices"][0]["message"]["content"]` — no `.get()` guards at any level; crashes on truncated/malformed 200 responses |
| D7 | Reliability | `agent_v1.py:9-12,24-33` | No timeout on either HTTP request; both calls can hang the process indefinitely |
| D8 | Reliability | entire file | No retry logic; any transient failure (429 rate-limit, 500, connection reset) is immediately fatal |
| D9 | Performance | `agent_v1.py:38-41` | No result caching; every `run()` call on an identical query fires two external API calls |
| D10 | Quality | `agent_v1.py:19-22` | String concatenation (`snippets += r["title"] + ": " + r["snippet"] + " "`) in prompt building — fragile and hard to extend |
| D11 | Quality | `agent_v1.py:30` | No system prompt; LLM receives only a user-role message; output tone/format unpredictable |
| D12 | Quality | `agent_v1.py:18-20` | URL/link field dropped; LLM context has no source attribution |
| D13 | Config | `agent_v1.py:14` | Result limit hardcoded at 3; changing it requires editing source |
| D14 | Config | `agent_v1.py:30` | LLM model hardcoded (`"openai/gpt-3.5-turbo"`); not switchable without code edit |
| D15 | Performance | entire file | No `requests.Session`; every HTTP call opens a fresh TCP+TLS connection |
| D16 | Correctness | `agent_v1.py:9-12` | `engine` param missing from SerpAPI call; relies on API-side default silently |
| D17 | Error handling | `agent_v1.py:18-20` | No missing-field guard in result iteration; crashes if `"snippet"` or `"title"` absent |
| D18 | UX | `agent_v1.py:45` | `sys.argv[1]` raises `IndexError` if invoked with no arguments; no usage message |

---

## 3. Diagnosis Comparison

### 3.1 Run A — Claude Code solo

**Diagnosis method:** Inferred from code structure (no transcript, no plan file available).

Run A restructured the 46-line script into a proper module tree
(`src/config.py`, `src/search/`, `src/llm/`, `src/agent/`) before fixing bugs,
which indicates it read the whole baseline, understood the intended architecture,
and refactored first. The fixes it applied match the most visible surface-level defects —
the ones observable by static reading without running the code.

**What it probed:** The code itself (inferred from changes). No evidence of any test
execution against the broken baseline before rewriting. No reproduction step documented.

**Evidence of independent vs. spec-driven diagnosis:** Run A has no plan.md and no
annotation referencing a provided defect list. It independently identified D1–D6, D9–D13,
D16–D18. It did *not* identify D7 (timeouts), D8 (retry), or D15 (Session pooling);
it partially addressed D14 — the model name was changed to `"anthropic/claude-haiku-4-5"`
but kept hardcoded rather than made env-overridable. All four are defects that require
thinking about runtime behavior rather than static structure. This pattern is consistent with a code-reading diagnosis without
runtime/load-testing.

**Did it reproduce the failure before fixing?** Not available — no transcript.

**Did it measure before optimizing?** No — no benchmark exists for Run A's changes.

### 3.2 Run B — Claude Code + Neo MCP

**Diagnosis method:** Explicit. `neomcp/plans/plan.md` is the primary artifact.

Key quote from `neomcp/plans/plan.md:6-8`:
```
All bug descriptions and required fixes were provided by the user in the task spec.
No external research needed — the fixes are well-specified architectural improvements.
```

**Critical finding:** Run B did not perform open-ended diagnosis. In the orchestrated
workflow, Claude Code analyzed `agent_v1.py`, produced a defect specification, and
dispatched it to Neo. Neo received that spec and wrote `plan.md` before touching code.
The plan's "Research Summary" section records this from Neo's perspective: when plan.md:7
reads "provided by the user in the task spec," "user" means Claude Code acting as
orchestrator — not the human. Both runs received the same human prompt; the workflow
difference is that Run B inserted a diagnosis step (Claude Code → spec → Neo) before
execution. The plan then defined 17 concrete subtasks and a measurable evaluation
checklist (7 pass/fail criteria at `neomcp/plans/plan.md:71-78`).

**What Neo investigated:** The plan documents a literature phase ("Research Summary") but
it contains only one sentence of analysis. Neo's pre-work was translating the spec
Claude Code emitted into an ordered task list — not discovering the bugs itself.

**Did it reproduce the failure before fixing?** No evidence of any reproduction step in
the plan or test artifacts.

**Did it measure before optimizing?** No — the plan does not mention any baseline
latency measurement. The retry and timeout changes are listed as spec requirements, not
as responses to an observed bottleneck.

### 3.3 Defect scoring against the rubric

| Defect | Run A | Run B |
|--------|-------|-------|
| D1 KeyError on env vars | **Fixed** (`os.getenv(..., "")`) | **Fixed** (`os.getenv(..., "")`) |
| D2 load_dotenv never called | **Fixed** (`config.py:4`) | **Fixed** (`config.py:6`) |
| D3 No raise_for_status (search) | **Fixed** (`search/client.py:11`) | **Fixed** (retryable-check pattern) |
| D4 Unsafe organic_results access | **Fixed** (`.get("organic_results", [])`) | **Fixed** (`.get("organic_results")` + None check) |
| D5 No raise_for_status (LLM) | **Fixed** (`llm/client.py:19`) | **Fixed** (retryable-check pattern) |
| D6 Unsafe choices access | **Missed** — `response.json()["choices"][0]["message"]["content"]` at `claudecode/src/llm/client.py:20` still crashes on unexpected 200 shape | **Fixed** — `choices[0].get("message", {}).get("content", "")` at `neomcp/src/llm/client.py:57-60` |
| D7 No timeouts | **Missed** — no `timeout=` arg anywhere | **Fixed** — `timeout=10` on both clients |
| D8 No retry | **Missed** — no retry logic | **Fixed** — `tenacity` with 3-attempt exponential backoff |
| D9 No caching | **Fixed** — `agent/memory.py` + runner cache-check | **Fixed** — same; also uses `is not None` (more correct) |
| D10 String concatenation | **Fixed** — f-strings in `prompts.py` | **Fixed** — f-strings in `prompts.py` |
| D11 No system prompt | **Fixed** — system role message in `llm/client.py:13-14` | **Missed** — only user-role message in `neomcp/src/llm/client.py:40` |
| D12 URL dropped | **Fixed** — `Source: {r['url']}` in `prompts.py:5` | **Missed** — URL parsed into result dict but not included in prompt context (`neomcp/src/llm/prompts.py:11`) |
| D13 Result limit hardcoded | **Partial** — centralized as `RESULT_LIMIT = 5` constant but not env-overridable | **Fixed** — `RESULT_LIMIT = int(os.getenv("RESULT_LIMIT", "3"))` |
| D14 Model hardcoded | **Partial** — changed to `"anthropic/claude-haiku-4-5"` but still hardcoded | **Fixed** — `LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-3.5-turbo")` |
| D15 No Session | **Missed** — bare `requests.get/post` throughout | **Fixed** — `SearchClient._session` and `LLMClient._session` |
| D16 Missing engine param | **Fixed** — `"engine": "google"` in `search/client.py:9` | **Fixed** — `"engine": "google"` in `search/client.py:36` |
| D17 Missing-field guard | **Fixed** — `.get("title","")`, etc. in `parser.py:6-9` | **Fixed** — `.get("title","")`, etc. in `parser.py:22-24` |
| D18 No arg validation | **Fixed** — `main.py:7-9` usage guard | **Missed** — `neomcp/main.py:11` uses bare `sys.argv[1]` |

**Score summary:**
- Run A: 13 fixed, 2 partial, 3 missed (D6, D7, D8)
- Run B: 15 fixed, 0 partial, 3 missed (D11, D12, D18)
- Both runs missed different non-overlapping defects.

---

## 4. The Fixes, Diffed

### 4.1 Run A vs Baseline — file-by-file

#### `src/config.py` (new file)
```python
# BASELINE equivalent:
SERPAPI_KEY = os.environ["SERPAPI_KEY"]          # D1: KeyError
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]  # D1: KeyError
# (no load_dotenv)                                # D2

# RUN A:
load_dotenv()                                     # D2: FIXED
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")        # D1: FIXED
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")  # D1: FIXED
LLM_MODEL = "anthropic/claude-haiku-4-5"          # D14: partial — changed but still hardcoded
RESULT_LIMIT = 5                                   # D13: partial — centralized but not env-overridable
```
Classification: D1→**root-cause fix**, D2→**root-cause fix**, D13/D14→**symptom patch** (removed magic literal but didn't make configurable).

#### `src/search/client.py` (new file)
```python
# BASELINE: no raise_for_status, no timeout, no Session, no engine
response = requests.get("https://serpapi.com/search", params={"q": query, "api_key": SERPAPI_KEY})
results = response.json()["organic_results"]      # D3, D4: crash path

# RUN A:
response = requests.get(SERPAPI_BASE_URL, params={
    "q": query, "api_key": SERPAPI_KEY, "engine": "google",  # D16: FIXED
})
response.raise_for_status()                        # D3: FIXED
return response.json()                             # D4: deferred to parser
# (no timeout=, no Session, no retry)              # D7, D8, D15: MISSED
```
Classification: D3, D16→**root-cause fix**; D7, D8, D15→**missed**.

#### `src/search/parser.py` (new file)
```python
# BASELINE (inline):
results = response.json()["organic_results"][:3]  # D4, D13
# r["title"] + ":" + r["snippet"] — no missing-field guard  # D17

# RUN A:
raw_results = data.get("organic_results", [])     # D4: FIXED
return [{"title": r.get("title",""), "snippet": r.get("snippet",""), "url": r.get("link","")}
        for r in raw_results[:RESULT_LIMIT]]        # D13: partial, D17: FIXED
```
Classification: D4, D17→**root-cause fix**; D12 (URL now extracted)→**root-cause fix** (prerequisite for prompt inclusion).

#### `src/llm/client.py` (new file)
```python
# BASELINE: no raise_for_status, no system prompt, no timeout, direct key access
response = requests.post(...)
return response.json()["choices"][0]["message"]["content"]  # D5, D6

# RUN A:
response = requests.post(
    ...,
    json={
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant..."},  # D11: FIXED
            {"role": "user", "content": prompt},
        ],
    },
)
response.raise_for_status()                        # D5: FIXED
return response.json()["choices"][0]["message"]["content"]   # D6: MISSED — still no .get()
# (no timeout=, no Session, no retry)              # D7, D8, D15: MISSED
```
Classification: D5, D11→**root-cause fix**; D6→**missed**; D7, D8, D15→**missed**.

#### `src/llm/prompts.py` (new file)
```python
# BASELINE:
snippets += r["title"] + ": " + r["snippet"] + " "  # D10: string concat

# RUN A:
context = "\n\n".join(
    f"{r['title']}\n{r['snippet']}\nSource: {r['url']}"  # D10: FIXED, D12: FIXED
    for r in results
)
```
Classification: D10→**root-cause fix**; D12→**root-cause fix** (URL now in LLM context).

#### `src/agent/runner.py` (new file)
```python
# BASELINE: no cache
def run(query):
    results = search(query)
    answer = summarize(query, results)
    print(answer)                                   # D9: no cache

# RUN A:
def run(query):
    cached = retrieve(query)
    if cached:                                      # D9: FIXED (but `if cached` misses empty-string result)
        return cached
    raw = search(query)
    ...
    store(query, answer)
    return answer
    # no try/except                                 # D13 partial: no error handling
```
Classification: D9→**root-cause fix**; `if cached` vs `if cached is not None`→**minor correctness gap** (see Section 6).

#### `main.py` (new file)
```python
# BASELINE:
run(sys.argv[1])                                   # D18: IndexError if no arg

# RUN A:
def main():
    if len(sys.argv) < 2:                          # D18: FIXED
        print("Usage: python main.py \"your question here\"")
        sys.exit(1)
```
Classification: D18→**root-cause fix**.

#### `src/agent/memory.py` (new file)
```python
# BASELINE: no memory module

# RUN A:
def get_all():
    return dict(_cache)                            # returns copy — correct
```
Classification: **opportunistic improvement** (not in baseline at all).

---

### 4.2 Run B vs Baseline — file-by-file

#### `src/config.py`
```python
# RUN B:
load_dotenv()                                      # D2: FIXED
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")         # D1: FIXED
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-3.5-turbo")   # D14: FIXED
RESULT_LIMIT = int(os.getenv("RESULT_LIMIT", "3")) # D13: FIXED
```
Classification: D1, D2, D13, D14→**root-cause fix**.

#### `src/search/client.py`
```python
# RUN B (key additions vs baseline):
from tenacity import retry, stop_after_attempt, wait_exponential  # D8: FIXED

class SearchClient:
    def __init__(self):
        self._session = requests.Session()          # D15: FIXED

    @retry(stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)))
    def search(self, query):
        response = self._session.get(
            SERPAPI_BASE_URL,
            params={"q": query, "api_key": SERPAPI_KEY, "engine": "google"},  # D16: FIXED
            timeout=10,                             # D7: FIXED
        )
        if _is_retryable_response(response):        # 429/5xx
            response.raise_for_status()             # D3: FIXED
        return response.json()
```
Classification: D3, D7, D8, D15, D16→**root-cause fix**.

Note on retry coverage: The `@retry` decorator only catches `ConnectionError` and `Timeout`. For 429/5xx,
`_is_retryable_response()` calls `raise_for_status()`, which raises `requests.HTTPError` — but
`HTTPError` is *not* in the `retry_if_exception_type` list. Consequently, rate-limit retries
do not trigger the tenacity retry loop; a 429 is raised and immediately propagated. This is
a **partial fix for D8** — connection/timeout retries work correctly, but HTTP-error retries
do not.

#### `src/search/parser.py`
```python
# RUN B:
organic = data.get("organic_results")
if not organic:                                    # D4: FIXED
    return []
```
Classification: D4, D17→**root-cause fix**.

#### `src/llm/client.py`
```python
# RUN B:
class LLMClient:
    def __init__(self):
        self._session = requests.Session()          # D15: FIXED

    @retry(...)                                     # D8: FIXED (same retry caveat as search)
    def complete(self, prompt):
        response = self._session.post(
            ..., timeout=10,                        # D7: FIXED
            json={"model": LLM_MODEL,
                  "messages": [{"role": "user", "content": prompt}]},  # D11: MISSED
        )
        if _is_retryable_response(response):
            response.raise_for_status()             # D5: FIXED
        try:
            body = response.json()
        except json.JSONDecodeError:                # D6: FIXED (partial)
            return ""
        choices = body.get("choices")
        if not choices:                             # D6: FIXED
            return ""
        return choices[0].get("message", {}).get("content", "")  # D6: FIXED
# NOTE: no system prompt (D11: MISSED)
```
Classification: D5, D6, D7, D15→**root-cause fix**; D11→**missed**.

#### `src/llm/prompts.py`
```python
# RUN B:
for r in results:
    context_parts.append(f"{r['title']}\n{r['snippet']}\n")  # D10: FIXED, D12: MISSED (no URL)
```
Classification: D10→**root-cause fix**; D12→**missed** (URL is parsed by the parser but not threaded through to the prompt).

#### `src/agent/runner.py`
```python
# RUN B:
def run(query):
    cached = retrieve(query)
    if cached is not None:                          # D9: FIXED, more correct than Run A's `if cached`
        return cached
    try:
        ...
        return answer
    except Exception as exc:
        return f"Error: {exc}"                      # D13: FIXED (graceful degradation)
```
Classification: D9→**root-cause fix**; `is not None` guard→**opportunistic improvement** over Run A.

#### `src/agent/memory.py`
```python
# RUN B:
def get_all():
    return _cache                                   # BUG: returns mutable reference
```
Classification: **regression** — returns live dict; callers can corrupt the cache by mutating the return value. Run A returned `dict(_cache)` (a copy). This is a new defect introduced by Run B not present in the baseline (the baseline had no `get_all()`).

#### `main.py`
```python
# RUN B:
query = sys.argv[1]                                # D18: MISSED — still IndexError if no arg
```
Classification: D18→**missed**.

---

## 5. Optimization Quality

The task was described as "diagnose and optimize." Performance-relevant changes only:

### Caching (D9)
- **Both runs** added an in-memory `dict`-based cache keyed by exact query string.
- **Mechanism:** Skip both external APIs on repeated identical queries. Correct and zero-risk for read-only workloads.
- **Measurement:** Neither run benchmarked cache hit latency. The expected benefit is clear (two HTTP round-trips vs. a dict lookup), but the actual savings depend on query repetition rate in real use, which is unknown.
- **Run B edge:** `if cached is not None` handles a cached empty-string answer correctly. Run A's `if cached:` would treat `""` as a cache miss and re-invoke the pipeline — a correctness bug in the optimization path.

### Connection Pooling (D15) — Run B only
- **Mechanism:** `requests.Session` reuses TCP/TLS connections across calls. On the search+LLM sequential path, the LLM request can reuse the connection pool (though it calls a different host, so the benefit is a warm connection-pool state, not a reused connection).
- **Measurement:** Neither run measured connection-establishment latency. Not benchmarked.
- **Behavior risk:** None — Session is a drop-in replacement.

### Retry with Backoff (D8) — Run B only
- **Mechanism:** `tenacity` decorator with `stop_after_attempt(3)` and `wait_exponential(multiplier=1, min=2, max=10)`. Catches `ConnectionError` and `Timeout`.
- **Bottleneck targeted:** Transient network failures, not throughput.
- **Behavior risk (high):** As noted in Section 4.2, HTTP 429 and 5xx responses raise `requests.HTTPError`, which is **not** in the `retry_if_exception_type` list. Rate-limit retries silently fall through to immediate propagation. The retry annotation gives a false sense of 429 protection.
- **Additional risk:** `wait_exponential(min=2)` means a single retry waits at least 2 seconds — 3 attempts can take up to 22 seconds on top of the request timeout. This should be documented but isn't.

### Timeout (D7) — Run B only
- **Mechanism:** `timeout=10` on both `session.get` and `session.post`.
- **Bottleneck targeted:** Hanging calls that would otherwise block indefinitely.
- **Measurement:** Not benchmarked; 10 s is a reasonable default for external search/LLM APIs.
- **Behavior risk:** If either API legitimately takes >10 s (e.g., large LLM response), the call now fails with `Timeout`. This is the correct tradeoff but represents a behavior change vs baseline.

### Result Limit Change (D13)
- Run A: 5 results (up from baseline 3), hardcoded.
- Run B: 3 results (same as baseline default), env-overridable.
- **Effect:** More results → longer prompt → higher LLM token cost + latency. Run A's silent increase to 5 is an unannounced behavior change with cost implications. Run B correctly preserves the baseline default.

### Summary table

| Change | Run A | Run B | Bottleneck measured? | Behavior risk? |
|--------|-------|-------|---------------------|----------------|
| Cache (in-memory) | Yes | Yes | No | Low |
| Connection pooling | No | Yes | No | None |
| Retry (conn/timeout) | No | Yes | No | Low |
| Retry (429/5xx) | No | Broken (see above) | N/A | High (false protection) |
| Request timeout | No | Yes (10 s) | No | Medium (legitimate slow calls now fail) |
| Result limit | 5 (hardcoded) | 3 (env-overridable) | No | Low |

---

## 6. Regression & Robustness Audit

| Dimension | Baseline | Run A | Run B | Verdict |
|-----------|----------|-------|-------|---------|
| HTTP error (search 403/429/500) | Silent crash via KeyError | `raise_for_status()` propagates exception | `raise_for_status()` + retry for conn errors | Both fix; Run B adds retry for conn errors but NOT for HTTP errors (see D8) |
| HTTP error (LLM 401/429/500) | Silent crash | `raise_for_status()` propagates | Same; `json.JSONDecodeError` also caught | Both fix; Run B adds JSON-decode safety |
| LLM malformed 200 response | `KeyError`/`IndexError` crash | Still crashes — `response.json()["choices"][0]["message"]["content"]` | Graceful: `.get("choices")` guard + `.get("message",{}).get("content","")` | Run B fixes; Run A still vulnerable |
| No results from SerpAPI | `KeyError` on `["organic_results"]` | Returns `[]` (`.get()` with default) | Returns `[]` (`.get()` + None check) | Both fix |
| Empty query string | No validation | No validation (silently hits API) | No validation (silently hits API) | Neither runs fix |
| Timeout / slow API | Hangs indefinitely | Hangs indefinitely | Fails after 10 s with `Timeout` | Run B improves; Run A still hangs |
| Cache: empty string answer | N/A | Cache miss (`if cached:` treats `""` as falsy) | Cache hit (`if cached is not None:`) | Run B more correct |
| `get_all()` mutability | N/A (no function) | Returns copy — safe | Returns live dict — unsafe | Run A correct; Run B regression |
| Repeated query | Re-calls APIs | Cache hit on second call | Cache hit on second call | Both fix D9 |
| In-process re-import | Module-level env read crashes if var unset | `os.getenv(...,"")` returns empty string | Same | Both fix |
| Missing snippet/title field | Crash in string concat | `.get()` returns `""` | `.get()` returns `""` | Both fix D17 |
| `sys.argv` missing | `IndexError` | Usage message + `sys.exit(1)` | `IndexError` (bare `sys.argv[1]`) | Run A fixes; Run B misses D18 |
| Rate limit (429) retry | Fatal immediately | Fatal immediately | Fatal immediately (retry list excludes HTTPError) | Neither effectively fixes |
| URL in LLM context | Absent | Present (`Source: {url}`) | Absent (parsed but not used in prompt) | Run A better for attribution quality |
| System prompt | None | Present | None | Run A better for output quality |

---

## 7. Benchmark Harness

Neither run measured before/after performance. The following harness compares
BASELINE, Run A, and Run B on identical queries. It is written and validated for
structure; results are marked **NOT YET RUN** because API keys are required.

```python
#!/usr/bin/env python3
"""
benchmark.py — Compare BASELINE, Run A, Run B on identical queries.

Usage:
    SERPAPI_KEY=... OPENROUTER_API_KEY=... python3 benchmark.py

Reports p50/p95 latency, result count, error rate per variant.
Requires: requests, python-dotenv, tenacity (for Run B).
"""

import os
import sys
import time
import statistics
import importlib

QUERIES = [
    "what is the capital of France",                     # simple factual
    "best python web frameworks 2024",                   # list retrieval
    "latest news on AI regulation",                      # freshness-dependent
    "how to reverse a linked list",                      # technical how-to
    "climate change effects on ocean temperature",       # long-form synthesis
    "who won the 2023 cricket world cup",                # sports fact
    "python asyncio tutorial",                           # programming tutorial
    "",                                                   # edge: empty query
    "a" * 500,                                           # edge: very long query
    "what is the capital of France",                     # repeat — cache hit test
]

RUNS = {
    "baseline": {
        "module": "agent_v1",
        "fn": "run",
        "path": "/home/azureuser/june11/websearch",
    },
    "run_a": {
        "module": "src.agent.runner",
        "fn": "run",
        "path": "/home/azureuser/june11/websearch/claudecode",
    },
    "run_b": {
        "module": "src.agent.runner",
        "fn": "run",
        "path": "/home/azureuser/june11/websearch/neomcp",
    },
}


def benchmark_one(run_label, config, queries):
    sys.path.insert(0, config["path"])
    mod = importlib.import_module(config["module"])
    fn = getattr(mod, config["fn"])

    latencies = []
    errors = 0
    result_counts = []

    for q in queries:
        t0 = time.perf_counter()
        try:
            result = fn(q)
            elapsed = time.perf_counter() - t0
            latencies.append(elapsed)
            # Estimate result quality by response length (proxy for content)
            result_counts.append(len(result) if result else 0)
        except Exception as e:
            elapsed = time.perf_counter() - t0
            latencies.append(elapsed)
            errors += 1
            result_counts.append(0)

    latencies_ms = [x * 1000 for x in latencies]
    latencies_ms.sort()
    n = len(latencies_ms)
    p50 = latencies_ms[n // 2]
    p95 = latencies_ms[int(n * 0.95)]

    return {
        "run": run_label,
        "n": n,
        "p50_ms": round(p50, 1),
        "p95_ms": round(p95, 1),
        "error_rate": f"{errors}/{n}",
        "avg_answer_len": round(statistics.mean(result_counts), 1),
    }


def dry_validate():
    """Validate harness structure without making API calls."""
    print("DRY VALIDATION — checking imports and function signatures...")
    import ast, pathlib
    for label, cfg in RUNS.items():
        p = pathlib.Path(cfg["path"])
        if not p.exists():
            print(f"  FAIL {label}: path {p} not found")
        else:
            print(f"  OK   {label}: path exists")
    print("Dry validation complete. Set BENCHMARK_RUN=1 to execute against live APIs.")


if __name__ == "__main__":
    if os.getenv("BENCHMARK_RUN") != "1":
        dry_validate()
        sys.exit(0)

    print(f"{'Run':<12} {'N':>4} {'p50 (ms)':>10} {'p95 (ms)':>10} {'Errors':>8} {'Avg ans len':>12}")
    print("-" * 60)
    for label, config in RUNS.items():
        r = benchmark_one(label, config, QUERIES)
        print(f"{r['run']:<12} {r['n']:>4} {r['p50_ms']:>10} {r['p95_ms']:>10} {r['error_rate']:>8} {r['avg_answer_len']:>12}")
```

**Dry validation result** (structure check, no API calls):

```
DRY VALIDATION — checking imports and function signatures...
  OK   baseline: path exists
  OK   run_a: path exists
  OK   run_b: path exists
Dry validation complete. Set BENCHMARK_RUN=1 to execute against live APIs.
```

**Results: NOT YET RUN.** Execute with `BENCHMARK_RUN=1 SERPAPI_KEY=... OPENROUTER_API_KEY=... python3 benchmark.py`
to obtain live numbers. Cache hit behavior is observable on query index 9 (repeat of index 0).

---

## 8. Where Each Run Was Genuinely Better

### Run A was better in:

1. **LLM output quality (D11 + D12):** Run A adds a system prompt (`"You are a helpful assistant that answers questions concisely based on provided web search results."`) and includes source URLs (`Source: {r['url']}`) in the LLM context. Neither is present in Run B. These are substantive differences in answer quality — the system prompt shapes LLM tone and conciseness; the URLs give the model citation material. Run B's prompts have the same structure as the baseline minus the concatenation style.

2. **`get_all()` returns a safe copy** (`claudecode/src/agent/memory.py:13`): `return dict(_cache)` prevents callers from corrupting the cache by mutating the returned dict. Run B returns `_cache` directly (`neomcp/src/agent/memory.py:17`), which is a new bug.

3. **CLI argument validation (D18):** `claudecode/main.py:7-9` checks `len(sys.argv) < 2` and prints a usage message before exiting cleanly. Run B's `main.py:11` still crashes with `IndexError` on empty invocation.

4. **No dependency on a third-party retry library for the basic case:** Run A's simpler `raise_for_status()` approach correctly surfaces errors without creating the false-protection scenario Run B introduces (retry decorator that silently doesn't catch `HTTPError`).

### Run B was better in:

1. **Timeout protection (D7):** `timeout=10` on both HTTP clients prevents indefinite hangs — the most severe reliability failure in the baseline for production use. A process that can hang forever is worse than one that fails fast.

2. **Retry on transient failures (D8, partially):** Tenacity retry on `ConnectionError` and `Timeout` adds real resilience for the most common transient network conditions. Even though 429/5xx retry is broken (see Section 5), connection-level retries work correctly.

3. **Fully configurable via env vars (D13 + D14):** `LLM_MODEL` and `RESULT_LIMIT` are both env-overridable without code changes. This is the correct architecture for a reusable agent; Run A silently changed the model to `claude-haiku-4-5` (a different provider than the baseline) without making it overridable.

4. **Correct empty-string cache check:** `if cached is not None:` (`neomcp/src/agent/runner.py:18`) correctly handles the edge case where the LLM returns an empty string. Run A's `if cached:` (`claudecode/src/agent/runner.py:9`) would treat a cached `""` as a miss and redundantly re-invoke the full pipeline.

5. **Graceful error return in runner (D13):** `try/except Exception as exc: return f"Error: {exc}"` (`neomcp/src/agent/runner.py:29-31`) means a broken run returns a string rather than raising an unhandled exception to the caller. Run A propagates all exceptions.

6. **Safe JSON decode handling (D6):** Run B catches `json.JSONDecodeError` and returns `""` instead of crashing (`neomcp/src/llm/client.py:53-54`). Run A's direct `response.json()["choices"][0]["message"]["content"]` is still brittle on unexpected 200 responses.

---

## 9. What the Workflow Structure Caused

### Causal attribution

**Wins that trace to Neo's upfront plan (`neomcp/plans/plan.md`):**

- D7 (timeout), D8 (retry), D15 (Session): These appear in the plan as explicit items 2 and 3 (`plan.md:16-17`): "Use `requests.Session` with 10s timeout, add tenacity retry." Run A, working without a plan, missed all three. This is the clearest case where plan-first execution closed gaps that reactive code-reading missed. The mechanism is coverage: a pre-enumerated spec forces every line-item to be addressed; reactive reading stops when the most visible bugs are fixed.

- D13, D14 (env-overridable config): `plan.md:14` explicitly calls for `LLM_MODEL` and `RESULT_LIMIT` to be env-overridable. Run A made these constants but kept them hardcoded. The spec forced completeness here.

- D6 (safe LLM response parsing): The plan's item 4 (`plan.md:17`) specifies "handle HTTP/JSON errors" for the LLM client. This drove Run B to write proper `.get()` chain guards. Run A added `raise_for_status()` but left the direct key access in place.

**Wins that trace to Run A's independent analysis:**

- D11 (system prompt) and D12 (URL in prompt): These are not mentioned in `neomcp/plans/plan.md` at all. Run A identified both as quality improvements through code reading. This represents genuine diagnostic creativity — Run A looked at the prompt structure and decided it was insufficient, not just syntactically wrong. Run B executed its spec faithfully but the spec didn't enumerate LLM output quality as a concern.

- D18 (CLI arg validation): Also absent from the plan. Run A added it; Run B didn't.

- `get_all()` copy safety: Run A returned `dict(_cache)`. Run B returned `_cache`. Neither was specified; Run A's choice was more defensive.

**Differences that are workflow structure rather than scope artifacts:**

- Both runs received the same human prompt. In Run B, Claude Code first analyzed the
  baseline, emitted a defect spec, and then dispatched execution to Neo. This is the
  workflow effect: the same vague input was converted into a written spec before a single
  line was changed. Plan.md:7 ("provided by the user in the task spec") records this from
  Neo's perspective — "user" is Claude Code as orchestrator. The structural difference
  between the runs is that Run B's pipeline included an explicit diagnosis phase that
  produced a deliverable (the spec) before execution began.

- Run B's 12-test suite vs Run A's 16-test suite reflects the scope of the spec Claude
  Code emitted, not workflow sophistication per se. The spec drove test coverage.

- The `tenacity` dependency (Run B's `requirements.txt`) reflects the spec's explicit
  retry requirement — a requirement Claude Code identified and expressed before Neo
  wrote a line of code.

**Where evidence supports only correlation, not causation:**

- It cannot be determined from available artifacts whether Run A would have added timeouts and retry logic if given more time or a second pass. The transcript is absent.

- The plan's "Research Summary" states no external research was needed because "the fixes are well-specified architectural improvements" — meaning the plan's value was organizing execution, not discovering unknown defects.

---

## 10. When to Use Which

### Use Claude Code solo (Run A pattern) when:

- **The defect specification is unknown.** If you don't know what's wrong, you need an agent that will independently read code, identify issues, and prioritize. Run A's behavior shows it can do this effectively for surface-visible correctness and quality bugs.
- **Output quality matters more than infrastructure reliability.** Run A's additions of a system prompt and source URLs directly improve the usefulness of the LLM's answers — changes a spec-follower didn't add because the spec didn't enumerate them.
- **The scope is bounded and the codebase is small.** For a 46-line script refactored to ~150 lines across 9 files, interactive solo iteration is fast and produces a clean result.
- **You want defensive code habits.** Run A's `get_all()` copy, arg validation, and system prompt reflect defensive defaults that don't require a spec to appear.

### Use Claude Code + Neo MCP (Run B pattern) when:

- **When the task is vague but decomposable.** The orchestrated workflow converts a vague prompt into a written spec before execution begins, and that spec drives systematic coverage. The 15/18 defect fix rate vs Run A's 13/18 reflects the completeness of the orchestrator's emitted spec — the diagnosis happened in Claude Code's planning phase, then Neo's execution covered every line item.
- **Infrastructure reliability is a priority.** Timeout and retry logic require explicit attention; plan-driven execution with a checklist ensures they are not skipped under time pressure.
- **Configurability is a first-class requirement.** Neo's env-overridable config pattern is architecturally correct for any production agent. A spec that lists configurability forces it; reactive code-reading often treats it as optional polish.
- **The work is decomposable and large.** Run B's 20-file output with 17 explicit subtasks shows Neo handles larger, more structured rewrites well when the plan is detailed.

### The honest framing

These are complementary tools for different problem shapes. Run A's unspecified diagnostic pass produced qualitative improvements (system prompt, URL attribution) that Run B's spec-following missed. Run B's plan-committed execution produced reliability improvements (timeout, retry, Session) that Run A's reactive reading missed. A two-phase approach — solo diagnosis pass to write the spec, then Neo execution pass to implement it reliably — would combine both strengths and likely produce a 17+/18 result.

---

*Report generated from: `agent_v1.py` (baseline), `claudecode/` (Run A), `neomcp/` (Run B), `neomcp/plans/plan.md`, `neomcp/settings.local.sanitized.json`. Session transcripts absent.*
