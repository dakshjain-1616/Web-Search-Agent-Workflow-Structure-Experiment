from src.config import RESULT_LIMIT


def parse_results(data):
    raw_results = data.get("organic_results", [])
    return [
        {
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "url": r.get("link", ""),
        }
        for r in raw_results[:RESULT_LIMIT]
    ]
