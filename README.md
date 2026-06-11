# Web Search Agent: Workflow Structure Experiment

Same prompt, two workflow structures, measurably different results. This repo contains the full experiment: the broken baseline, both refactored outputs, and the technical comparison in `REPORT.md`. The narrative write-up is in `BLOG.md`.

**Headline result:** Claude Code solo fixed 13/18 catalogued defects in a broken web search agent. Claude Code orchestrating Neo MCP fixed 15/18. The missed sets don't overlap — each workflow is blind to a different class of problem.

---

## Repo Map

```
agent_v1.py         — The original broken 46-line script (18 defects, the starting point)
claudecode/         — Run A: Claude Code solo refactor (13/18 defects fixed)
neomcp/             — Run B: Claude Code + Neo MCP orchestrated rewrite (15/18 defects fixed)
  plans/plan.md     — Neo's pre-coding plan (17 subtasks, 7-point checklist)
REPORT.md           — Full technical comparison with file:line citations throughout
BLOG.md             — Narrative write-up (~10 min read)
infographic-scoreboard.svg  — Defect map visual (embedded in BLOG.md)
infographic-insight.svg     — Missed-defect pattern visual (embedded in BLOG.md)
```

---

## How to Reproduce

### Requirements

- Python 3.8+
- A [SerpAPI](https://serpapi.com/) API key
- An [OpenRouter](https://openrouter.ai/) API key

### Setup (Run A — Claude Code solo)

```bash
cd claudecode
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in SERPAPI_KEY and OPENROUTER_API_KEY
python main.py "your question here"
```

### Setup (Run B — Claude Code + Neo MCP)

```bash
cd neomcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in SERPAPI_KEY and OPENROUTER_API_KEY
python main.py "your question here"
```

### Run tests (no API keys required — all HTTP mocked)

```bash
# Run A
cd claudecode && SERPAPI_KEY=test OPENROUTER_API_KEY=test python3 -m pytest tests/ -v

# Run B
cd neomcp && python3 -m pytest tests/ -v
```

---

## Evidence Integrity

| Artifact | Status | Notes |
|----------|--------|-------|
| `agent_v1.py` | Present | The unmodified broken 46-line starting point |
| `claudecode/` | Present | Run A result (13/18 defects fixed) |
| `neomcp/` | Present | Run B result (15/18 defects fixed) |
| `neomcp/plans/plan.md` | Present | Neo's pre-coding plan (43 lines, 17 subtasks) |
| Session transcripts | **Absent** | No transcript preserved for either run; all behavioral reconstruction in REPORT.md is from code diffs |

`REPORT.md` cites every claim with `file:line-number`. The defect inventory in Section 2 is the scoring rubric; all fix classifications in Section 4 trace to specific file locations in `claudecode/` and `neomcp/`.
