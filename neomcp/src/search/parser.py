"""Parse and extract structured results from SerpAPI responses."""

from ..config import RESULT_LIMIT


def parse_results(data):
    """Extract top results from a SerpAPI JSON response.

    Uses safe .get() access and returns an empty list when no results
    are available.
    """
    organic = data.get("organic_results")
    if not organic:
        return []

    top = organic[:RESULT_LIMIT]

    parsed = []
    for r in top:
        parsed.append({
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "url": r.get("link", ""),
        })
    return parsed