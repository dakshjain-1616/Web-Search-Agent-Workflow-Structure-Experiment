"""Configuration module - loads .env and provides application settings."""

import os
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

SERPAPI_BASE_URL = "https://serpapi.com/search"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-3.5-turbo")
RESULT_LIMIT = int(os.getenv("RESULT_LIMIT", "3"))