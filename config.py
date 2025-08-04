import os
import re
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def clean_env_var(value: str | None) -> str | None:
    if not value:
        return value
    # Strip leading/trailing single or double quotes (only if the entire string is wrapped)
    return re.sub(r"^['\"](.*)['\"]$", r"\1", value)

OPENROUTER_API_KEY = clean_env_var(os.getenv("OPENROUTER_API_KEY"))
BOT_TOKEN = clean_env_var(os.getenv("BOT_TOKEN"))
MODEL = clean_env_var(os.getenv("MODEL"))  # e.g. gemini/..., anthropic/...
DATABASE_URL = clean_env_var(os.getenv("DATABASE_URL")) or "sqlite:///message_history.db"
