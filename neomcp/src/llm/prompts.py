"""Prompt building utilities."""


def build_prompt(query, results):
    """Build a prompt for the LLM from a user query and search results.

    Uses f-strings for string formatting.
    """
    context_parts = []
    for r in results:
        context_parts.append(f"{r['title']}\n{r['snippet']}\n")
    context = "".join(context_parts)

    prompt = (
        f"You are a helpful assistant. "
        f"The user asked: {query}\n\n"
        f"Here is some information from the web:\n"
        f"{context}"
        f"Please provide a concise answer based on the above information."
    )
    return prompt