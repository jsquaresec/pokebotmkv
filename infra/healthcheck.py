import urllib.request
import sys

def main():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5) as response:
            if response.status != 200:
                raise RuntimeError(f"Bad status: {response.status}")
        print("ok")
    except Exception as exc:
        print(f"healthcheck failed: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
