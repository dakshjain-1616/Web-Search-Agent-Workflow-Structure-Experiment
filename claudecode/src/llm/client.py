import requests
from src.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, LLM_MODEL


def complete(prompt):
    response = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        },
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that answers questions concisely based on provided web search results."},
                {"role": "user", "content": prompt},
            ],
        },
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
