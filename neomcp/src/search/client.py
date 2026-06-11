"""Search client using SerpAPI with retry logic."""

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config import SERPAPI_KEY, SERPAPI_BASE_URL


def _is_retryable_response(response):
    """Return True if the response status indicates a retryable error."""
    return response.status_code in (429,) or response.status_code >= 500


class SearchClient:
    """Session-based search client with automatic retry and timeout."""

    def __init__(self):
        self._session = requests.Session()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=(
            retry_if_exception_type((requests.ConnectionError, requests.Timeout))
        ),
    )
    def search(self, query):
        """Perform a web search for the given query.

        Returns parsed JSON response.
        """
        response = self._session.get(
            SERPAPI_BASE_URL,
            params={
                "q": query,
                "api_key": SERPAPI_KEY,
                "engine": "google",
            },
            timeout=10,
        )
        if _is_retryable_response(response):
            response.raise_for_status()
        return response.json()