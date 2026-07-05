# load libs
from dotenv import load_dotenv
import os

# init post sign
POST_SIGN = "by <a href=\"https://t.me/ely4plugg\">ELY4PLUGG</a>."

# load .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT = os.getenv("CHAT")
CHANNEL = os.getenv("CHANNEL")
ADMIN = os.getenv("ADMIN")

# check .env vars
required = {
    "BOT_TOKEN": BOT_TOKEN,
    "CHAT": CHAT,
    "CHANNEL": CHANNEL,
    "ADMIN": ADMIN,
}
missing = [name for name, value in required.items() if value is None]
if missing:
    raise RuntimeError(f"no vars: {', '.join(missing)}")

# turn to int type + init admin sign var
CHAT = int(CHAT)
CHANNEL = int(CHANNEL)
ADMIN = int(ADMIN)