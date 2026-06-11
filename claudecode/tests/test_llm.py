from unittest.mock import patch, MagicMock
from src.llm.client import complete
from src.llm.prompts import build_prompt


def test_build_prompt_contains_query():
    results = [{"title": "Title 1", "snippet": "Snippet 1", "url": "http://example.com"}]
    prompt = build_prompt("what is python", results)
    assert "what is python" in prompt


def test_build_prompt_contains_snippet():
    results = [{"title": "Title 1", "snippet": "Snippet 1", "url": "http://example.com"}]
    prompt = build_prompt("test", results)
    assert "Snippet 1" in prompt


def test_build_prompt_contains_url():
    results = [{"title": "T", "snippet": "S", "url": "http://example.com"}]
    prompt = build_prompt("test", results)
    assert "http://example.com" in prompt


def test_complete_returns_string():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "The answer is 42."}}]
    }
    with patch("src.llm.client.requests.post", return_value=mock_response):
        result = complete("What is the answer?")
    assert result == "The answer is 42."


def test_complete_raises_on_http_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP 401")
    with patch("src.llm.client.requests.post", return_value=mock_response):
        try:
            complete("anything")
            assert False, "should have raised"
        except Exception as e:
            assert "401" in str(e)
