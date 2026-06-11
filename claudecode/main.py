import sys
from src.agent.runner import run


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py \"your question here\"")
        sys.exit(1)
    query = sys.argv[1]
    answer = run(query)
    print(answer)


if __name__ == "__main__":
    main()
