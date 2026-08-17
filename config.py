# standard library toolkit
from json import JSONDecodeError, load
from os import getenv
from pathlib import Path

# read config.yaml lib
import yaml

# pull secrets from .env without leaking the sauce
from dotenv import load_dotenv

# load config.yaml file with all vars
try:
    with open("config.yaml", encoding="utf-8") as file:
        yaml_config = yaml.safe_load(file)
except yaml.scanner.ScannerError as error:
    raise RuntimeError(f"invalid YAML in config.yaml") from error

# absolute paths, so the bot works from any directory
BASE_DIR = Path(__file__).resolve().parent
MEDIA_IDS_PATH = BASE_DIR / yaml_config["files"]["media_ids"]

# MTProto session and checkpoint files stay beside the bot code
DELETION_AUDIT_MTPROTO = yaml_config["audit"]["deletion"]["enable"]
DELETION_AUDIT_SESSION_PATH = BASE_DIR / yaml_config["files"]["audit"]["session"]
DELETION_AUDIT_STATE_PATH = BASE_DIR / yaml_config["files"]["audit"]["state"]

# post, comment signature templates;
# placeholders: [SIGN_ADMIN] is where the artist signs
POST_SIGN = yaml_config["signs"]["post"]["text"]
COMMENT_SIGN = yaml_config["signs"]["comment"]["text"]

# enable/disable tg channel audit for log chat
AUDIT_FOR_LOG_CHAT = yaml_config["audit"]["all"]["enable"]

# words shown when someone hits /start
START_COMMAND_TEXT = yaml_config["commands"]["start"]["text"]

# premium emoji drip - works only when the bot owner has Telegram Premium
START_COMMAND_CUSTOM_EMOJI_MENU = yaml_config["commands"]["start"]["custom_emoji"]
COMMENT_CUSTOM_EMOJI_MENU = yaml_config["signs"]["comment"]["custom_emoji"]

# reuse Telegram file IDs instead of uploading the same GIFs forever
try:
    # cached media IDs loaded from the local stash
    with MEDIA_IDS_PATH.open("r", encoding="utf-8") as file:
        media_files = load(file)
except FileNotFoundError:
    # first launch is handled by main.py - smooth and automatic
    media_files = {}
except JSONDecodeError as error:
    raise RuntimeError(f"invalid JSON in {MEDIA_IDS_PATH}") from error

# ready-to-send Telegram IDs for both animations
START_COMMAND_GIF = media_files.get("START_COMMAND_GIF")
COMMENT_GIF = media_files.get("COMMENT_GIF")

# load the private stuff
load_dotenv(BASE_DIR / ".env")

# raw environment values before Telegram IDs become integers
BOT_TOKEN = getenv("BOT_TOKEN")
CHAT = getenv("CHAT")
CHANNEL = getenv("CHANNEL")
ADMIN = getenv("ADMIN")
LOG_CHAT = getenv("LOG_CHAT")

# optional MTProto credentials unlock deleted post audit
API_ID_RAW = getenv("API_ID")
API_HASH = getenv("API_HASH")

# fail fast when the setup is missing something important
# the full setup checklist - every key must be present
required = {
    "BOT_TOKEN": BOT_TOKEN,
    "CHAT": CHAT,
    "CHANNEL": CHANNEL,
    "ADMIN": ADMIN,
    "LOG_CHAT": LOG_CHAT,
}
# missing keys get caught before the bot tries anything funny
missing = [name for name, value in required.items() if value is None]
if missing:
    raise RuntimeError(f"no vars: {', '.join(missing)}")

# API ID becomes an integer only when MTProto audit is configured
try:
    API_ID = int(API_ID_RAW) if API_ID_RAW else None
except ValueError as error:
    raise RuntimeError("API_ID must be an integer") from error

# tg ids are numbers, so keep them that way
CHAT = int(CHAT)
CHANNEL = int(CHANNEL)
ADMIN = int(ADMIN)
LOG_CHAT = int(LOG_CHAT)
