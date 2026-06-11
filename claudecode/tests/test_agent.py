from unittest.mock import patch
from src.agent.runner import run
from src.agent import memory


def setup_function():
    memory._cache.clear()


def test_run_returns_answer():
    with patch("src.agent.runner.search") as mock_search, \
         patch("src.agent.runner.parse_results") as mock_parse, \
         patch("src.agent.runner.complete") as mock_complete:

        mock_search.return_value = {}
        mock_parse.return_value = [{"title": "T", "snippet": "S", "url": "U"}]
        mock_complete.return_value = "Some answer"

        result = run("what is python?")

    assert result == "Some answer"


def test_run_uses_cache_on_second_call():
    with patch("src.agent.runner.search") as mock_search, \
         patch("src.agent.runner.parse_results") as mock_parse, \
         patch("src.agent.runner.complete") as mock_complete:

        mock_search.return_value = {}
        mock_parse.return_value = [{"title": "T", "snippet": "S", "url": "U"}]
        mock_complete.return_value = "Cached answer"

        run("cached query")
        result = run("cached query")

    assert result == "Cached answer"
    assert mock_complete.call_count == 1  # only called once, second hit was cached


def test_memory_store_and_retrieve():
    memory.store("hello", "world")
    assert memory.retrieve("hello") == "world"


def test_memory_accumulates():
    memory.store("q1", "a1")
    memory.store("q2", "a2")
    all_entries = memory.get_all()
    assert "q1" in all_entries
    assert "q2" in all_entries


def test_memory_get_all_returns_copy():
    memory.store("k", "v")
    snapshot = memory.get_all()
    snapshot["k"] = "tampered"
    assert memory.retrieve("k") == "v"
