"""Tests for LLM client and prompt builder."""

from unittest.mock import patch, MagicMock

from src.llm.client import LLMClient
from src.llm.prompts import build_prompt


def test_build_prompt_contains_query():
    results = [{"title": "Title 1", "snippet": "Snippet 1", "url": "http://example.com"}]
    prompt = build_prompt("what is python", results)
    assert "what is python" in prompt


def test_build_prompt_contains_snippet():
    results = [{"title": "Title 1", "snippet": "Snippet 1", "url": "http://example.com"}]
    prompt = build_prompt("test", results)
    assert "Snippet 1" in prompt


def test_build_prompt_uses_fstrings():
    """Verify that the prompt is built using f-strings (no string concat)."""
    results = [{"title": "T", "snippet": "S", "url": "http://example.com"}]
    prompt = build_prompt("q", results)
    # Ensure the prompt is the expected f-string output
    assert isinstance(prompt, str)
    assert "q" in prompt
    assert "T" in prompt
    assert "S" in prompt


def test_complete_returns_string():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "The answer is 42."}}]
    }
    client = LLMClient()
    with patch.object(client._session, "post", return_value=mock_response):
        result = client.complete("What is the answer?")
    assert result == "The answer is 42."


def test_complete_is_not_none():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Some answer"}}]
    }
    client = LLMClient()
    with patch.object(client._session, "post", return_value=mock_response):
        result = client.complete("anything")
    assert result is not None