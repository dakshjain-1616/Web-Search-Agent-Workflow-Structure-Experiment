# Web Search Agent

A lightweight web search agent that uses SerpAPI to fetch search results and
OpenRouter (LLM) to produce concise answers.

## Features

- 🔍 **Web search** via SerpAPI with automatic retry on failures
- 🤖 **LLM completion** via OpenRouter API with automatic retry on failures
- 📦 **In-memory result caching** — identical queries return cached answers
  instantly without calling external APIs
- 🔄 **Retry logic** with exponential backoff (3 attempts) on connection errors,
  timeouts, rate limits (429), and server errors (5xx)
- ⚙️ **Configurable via environment variables** — no hard-coded secrets
- 🧪 **Test suite** that runs without real API keys (all HTTP calls mocked)

## Requirements

- Python 3.8+
- A [SerpAPI](https://serpapi.com/) API key
- An [OpenRouter](https://openrouter.ai/) API key

## Setup

1. Clone the repository and navigate to the project folder:

    ```bash
    cd websearch
    ```

2. (Recommended) Create and activate a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate   # Linux / macOS
    venv\Scripts\activate      # Windows
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Copy the environment template and fill in your API keys:

    ```bash
    cp .env.example .env
    ```

    Edit `.env` and set your keys:

    ```env
    SERPAPI_KEY=your_actual_serpapi_key
    OPENROUTER_API_KEY=your_actual_openrouter_key
    ```

    The `.env` file is loaded automatically on every run.

## Usage

Run the agent with a query:

```bash
python main.py "What is the capital of France?"
```

The agent will:
1. Check its in-memory cache — if this query was asked before, the cached
   answer is returned immediately.
2. Search the web via SerpAPI (with up to 3 automatic retries on failure).
3. Parse the top results (customizable via `RESULT_LIMIT`).
4. Build a prompt that includes the query and search snippets.
5. Send the prompt to an LLM via OpenRouter.
6. Cache and return the answer.

## Environment Variables

| Variable             | Required | Default               | Description                            |
|----------------------|----------|-----------------------|----------------------------------------|
| `SERPAPI_KEY`        | Yes      | —                     | Your SerpAPI API key                   |
| `OPENROUTER_API_KEY` | Yes      | —                     | Your OpenRouter API key                |
| `LLM_MODEL`          | No       | `openai/gpt-3.5-turbo`| Model identifier for OpenRouter        |
| `RESULT_LIMIT`       | No       | `3`                   | Number of search results to use        |

## Running Tests

All tests use mocked HTTP calls, so no API keys are required.

```bash
pytest tests/ -v
```

## Project Structure

```
neo mcp/
├── main.py                 # CLI entrypoint
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── README.md               # This file
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuration (env vars, defaults)
│   ├── search/
│   │   ├── __init__.py
│   │   ├── client.py       # SerpAPI search client with retry
│   │   └── parser.py       # Search result parser
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py       # OpenRouter LLM client with retry
│   │   └── prompts.py      # Prompt builder (f-strings)
│   └── agent/
│       ├── __init__.py
│       ├── memory.py       # In-memory cache
│       └── runner.py       # Agent orchestrator
└── tests/
    ├── __init__.py
    ├── conftest.py          # Test fixtures (dummy env vars)
    ├── test_search.py       # Search client & parser tests
    ├── test_llm.py         # LLM client & prompt tests
    └── test_agent.py       # Agent runner & cache tests
```