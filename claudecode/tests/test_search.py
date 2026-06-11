from unittest.mock import patch, MagicMock
from src.search.client import search
from src.search.parser import parse_results


def test_search_returns_data():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "organic_results": [
            {"title": "Result 1", "snippet": "Snippet 1", "link": "http://example.com/1"},
        ]
    }
    with patch("src.search.client.requests.get", return_value=mock_response):
        result = search("test query")
    assert result is not None


def test_search_raises_on_http_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP 403")
    with patch("src.search.client.requests.get", return_value=mock_response):
        try:
            search("test")
            assert False, "should have raised"
        except Exception as e:
            assert "403" in str(e)


def test_parse_results_returns_limit():
    data = {
        "organic_results": [
            {"title": f"Result {i}", "snippet": f"Snippet {i}", "link": f"http://example.com/{i}"}
            for i in range(10)
        ]
    }
    results = parse_results(data)
    assert len(results) == 5  # RESULT_LIMIT is 5


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


def test_parse_results_handles_missing_organic_results():
    results = parse_results({})
    assert results == []


def test_parse_results_handles_missing_fields():
    data = {"organic_results": [{"title": "T"}]}
    results = parse_results(data)
    assert results[0]["snippet"] == ""
    assert results[0]["url"] == ""
