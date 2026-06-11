import requests
from src.config import SERPAPI_KEY, SERPAPI_BASE_URL


def search(query):
    response = requests.get(SERPAPI_BASE_URL, params={
        "q": query,
        "api_key": SERPAPI_KEY,
        "engine": "google",
    })
    response.raise_for_status()
    return response.json()
