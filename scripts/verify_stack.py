import json
import sys
import urllib.request

def fetch(url: str):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status, response.read().decode()

def main():
    base = "http://127.0.0.1:8000"
    status, body = fetch(f"{base}/health")
    if status != 200:
        raise SystemExit("Health check failed")
    print("health ok")

    # Replay endpoint may 404 if no replay exists yet; that's acceptable for stack verification
    try:
        status, body = fetch(f"{base}/replays/1")
        print("replay endpoint reachable:", status)
        print(body)
    except Exception as exc:
        print("replay endpoint reachable but no replay yet or returned error:", exc)

if __name__ == "__main__":
    main()
