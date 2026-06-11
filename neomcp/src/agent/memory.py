"""In-memory cache for query→answer pairs."""

_cache = {}


def store(query, answer):
    """Store an answer for the given query."""
    _cache[query] = answer


def retrieve(query):
    """Return cached answer for the query, or None if not cached."""
    return _cache.get(query)


def get_all():
    """Return the entire cache dictionary."""
    return _cache