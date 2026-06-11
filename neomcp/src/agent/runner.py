"""Agent runner — orchestrates search, parse, prompt, complete with caching."""

from ..search.client import SearchClient
from ..search.parser import parse_results
from ..llm.client import LLMClient
from ..llm.prompts import build_prompt
from ..agent.memory import store, retrieve


def run(query):
    """Execute the full agent pipeline for the given query.

    Checks the cache first. On a cache miss, it searches the web,
    parses results, builds a prompt, completes with the LLM, stores
    the answer, and returns it.
    """
    cached = retrieve(query)
    if cached is not None:
        return cached

    try:
        search_client = SearchClient()
        llm_client = LLMClient()

        raw = search_client.search(query)
        results = parse_results(raw)
        prompt = build_prompt(query, results)
        answer = llm_client.complete(prompt)
        store(query, answer)
        return answer
    except Exception as exc:
        return f"Error: {exc}"