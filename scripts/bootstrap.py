import asyncio
import subprocess
import sys

def run(cmd):
    if subprocess.run(cmd).returncode != 0:
        raise SystemExit(1)

async def main():
    tests = [
        "tests/test_season_service.py",
        "tests/test_event_effect_service.py",
        "tests/test_battle_ui_service.py",
        "tests/test_leaderboard_season_api.py",
    ]
    for t in tests:
        run([sys.executable, t])
    print("Bootstrap complete")

if __name__ == "__main__":
    asyncio.run(main())
