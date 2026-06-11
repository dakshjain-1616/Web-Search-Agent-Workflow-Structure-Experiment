from src.search.client import search
from src.search.parser import parse_results
from src.llm.client import complete
from src.llm.prompts import build_prompt
from src.agent.memory import store, retrieve


def run(query):
    cached = retrieve(query)
    if cached:
        return cached

    raw = search(query)
    results = parse_results(raw)
    prompt = build_prompt(query, results)
    answer = complete(prompt)
    store(query, answer)
    return answer
