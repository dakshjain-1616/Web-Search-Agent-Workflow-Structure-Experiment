def build_prompt(query, results):
    context = "\n\n".join(
        f"{r['title']}\n{r['snippet']}\nSource: {r['url']}"
        for r in results
    )
    return (
        f"The user asked: {query}\n\n"
        f"Here is relevant information from the web:\n\n{context}\n\n"
        "Provide a concise, accurate answer based on the above sources."
    )
