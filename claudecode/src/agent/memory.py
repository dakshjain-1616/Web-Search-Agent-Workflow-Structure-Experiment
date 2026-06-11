_cache = {}


def store(query, answer):
    _cache[query] = answer


def retrieve(query):
    return _cache.get(query)


def get_all():
    return dict(_cache)
