from core.env_validation import validate_environment
from core.logging_setup import configure_logging
from config import settings
from launcher import asyncio, run_bot

if __name__ == "__main__":
    configure_logging(settings.log_level)
    validate_environment()
    asyncio.run(run_bot())
