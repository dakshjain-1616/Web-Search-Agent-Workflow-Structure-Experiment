import os
import requests

SERPAPI_KEY = os.environ["SERPAPI_KEY"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]


def search(query):
    response = requests.get("https://serpapi.com/search", params={
        "q": query,
        "api_key": SERPAPI_KEY,
    })
    results = response.json()["organic_results"]
    return results[:3]


def summarize(query, results):
    snippets = ""
    for r in results:
        snippets += r["title"] + ": " + r["snippet"] + " "

    prompt = "User asked: " + query + " Here are some search results: " + snippets + " Please summarize the answer."

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer " + OPENROUTER_API_KEY,
        },
        json={
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
        },
    )

    return response.json()["choices"][0]["message"]["content"]


def run(query):
    results = search(query)
    answer = summarize(query, results)
    print(answer)


if __name__ == "__main__":
    import sys
    run(sys.argv[1])
