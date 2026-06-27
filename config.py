import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID_RAW = os.environ.get("CHAT_ID")
PORT = int(os.environ.get("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required")

if not CHAT_ID_RAW:
    raise RuntimeError("CHAT_ID environment variable is required")

try:
    CHAT_ID = int(CHAT_ID_RAW)
except ValueError:
    raise RuntimeError("CHAT_ID must be an integer (e.g. -1001234567890)")
