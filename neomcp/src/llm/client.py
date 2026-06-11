"""LLM client using OpenRouter API with retry logic."""

import json

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, LLM_MODEL


def _is_retryable_response(response):
    """Return True if the response status indicates a retryable error."""
    return response.status_code in (429,) or response.status_code >= 500


class LLMClient:
    """Session-based LLM completion client with automatic retry and timeout."""

    def __init__(self):
        self._session = requests.Session()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=(
            retry_if_exception_type((requests.ConnectionError, requests.Timeout))
        ),
    )
    def complete(self, prompt):
        """Send a prompt to the LLM and return the text response.

        Returns the generated text from the model, or a fallback message
        if parsing fails.
        """
        response = self._session.post(
            OPENROUTER_BASE_URL + "/chat/completions",
            headers={
                "Authorization": "Bearer " + OPENROUTER_API_KEY,
            },
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=10,
        )
        if _is_retryable_response(response):
            response.raise_for_status()

        try:
            body = response.json()
        except json.JSONDecodeError:
            return ""

        choices = body.get("choices")
        if not choices:
            return ""

        return choices[0].get("message", {}).get("content", "")