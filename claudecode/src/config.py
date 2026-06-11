import os
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

SERPAPI_BASE_URL = "https://serpapi.com/search"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LLM_MODEL = "anthropic/claude-haiku-4-5"
RESULT_LIMIT = 5
