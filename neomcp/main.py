"""CLI entrypoint for the web search agent.

Usage:
    python main.py "your search query"
"""

import sys
from dotenv import load_dotenv

load_dotenv()

from src.agent.runner import run

query = sys.argv[1]
answer = run(query)
print(answer)