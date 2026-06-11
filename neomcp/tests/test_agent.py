"""Tests for the agent runner and memory cache."""

from unittest.mock import patch

from src.agent.runner import run
from src.agent.memory import store, retrieve, get_all


def test_run_returns_answer():
    with patch("src.agent.runner.SearchClient") as mock_search_cls, \
         patch("src.agent.runner.LLMClient") as mock_llm_cls, \
         patch("src.agent.runner.parse_results") as mock_parse:

        mock_search_client = mock_search_cls.return_value
        mock_search_client.search.return_value = {}

        mock_llm_client = mock_llm_cls.return_value
        mock_llm_client.complete.return_value = "Some answer"

        mock_parse.return_value = [{"title": "T", "snippet": "S", "url": "U"}]

        result = run("what is python?")

    assert result == "Some answer"


def test_memory_store_and_retrieve():
    store("hello", "world")
    assert retrieve("hello") == "world"


def test_memory_accumulates():
    store("q1", "a1")
    store("q2", "a2")
    all_entries = get_all()
    assert "q1" in all_entries
    assert "q2" in all_entries


def test_cache_hit_skips_search():
    """When cache has an entry for the query, no search/LLM calls are made."""
    store("cached query", "cached answer")

    # Patch search and LLM - if cache is checked first, these won't be called
    with patch("src.agent.runner.SearchClient") as mock_search_cls, \
         patch("src.agent.runner.LLMClient") as mock_llm_cls:

        result = run("cached query")

    assert result == "cached answer"
    mock_search_cls.assert_not_called()
    mock_llm_cls.assert_not_called()