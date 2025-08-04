import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MODEL = os.getenv("MODEL")  # or gemini/..., anthropic/..., etc.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///message_history.db")  # Default to SQLite if not set
print("DATABASE_URL =", repr(DATABASE_URL))  # for debugging
