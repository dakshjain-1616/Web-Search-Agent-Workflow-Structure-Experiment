"""Test configuration — set dummy environment variables before any imports."""

import os

os.environ.setdefault("SERPAPI_KEY", "test_serpapi_key")
os.environ.setdefault("OPENROUTER_API_KEY", "test_openrouter_key")