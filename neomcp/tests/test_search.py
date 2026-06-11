"""Tests for search client and parser."""

from unittest.mock import patch, MagicMock

from src.search.client import SearchClient
from src.search.parser import parse_results


def test_search_returns_data():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "organic_results": [
            {"title": "Result 1", "snippet": "Snippet 1", "link": "http://example.com/1"},
            {"title": "Result 2", "snippet": "Snippet 2", "link": "http://example.com/2"},
            {"title": "Result 3", "snippet": "Snippet 3", "link": "http://example.com/3"},
        ]
    }
    client = SearchClient()
    with patch.object(client._session, "get", return_value=mock_response):
        result = client.search("test query")
    assert result is not None


def test_parse_results_returns_three():
    data = {
        "organic_results": [
            {"title": "Result 1", "snippet": "Snippet 1", "link": "http://example.com/1"},
            {"title": "Result 2", "snippet": "Snippet 2", "link": "http://example.com/2"},
            {"title": "Result 3", "snippet": "Snippet 3", "link": "http://example.com/3"},
        ]
    }
    results = parse_results(data)
    assert len(results) == 3


def test_parse_results_has_expected_keys():
    data = {
        "organic_results": [
            {"title": "T", "snippet": "S", "link": "http://example.com"},
        ]
    }
    results = parse_results(data)
    assert "title" in results[0]
    assert "snippet" in results[0]
    assert "url" in results[0]