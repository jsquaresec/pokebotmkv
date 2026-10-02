from core.env_validation import validate_environment
from core.logging_setup import configure_logging
from config import settings
import uvicorn

if __name__ == "__main__":
    configure_logging(settings.log_level)
    validate_environment()
    uvicorn.run("api.dashboard:app", host="0.0.0.0", port=8000, reload=False)
