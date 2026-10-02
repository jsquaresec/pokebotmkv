import asyncio
from core.logging_setup import configure_logging

async def main():
    configure_logging("INFO")
    while True:
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
