# standard library toolkit
from json import JSONDecodeError, load
from os import getenv
from pathlib import Path

# pull secrets from .env without leaking the sauce
from dotenv import load_dotenv

# absolute paths, so the bot works from any directory
BASE_DIR = Path(__file__).resolve().parent
MEDIA_IDS_PATH = BASE_DIR / "media_ids.json"

# post signature template; [SIGN_ADMIN] is where the artist signs
POST_SIGN = (
    "by <b>[SIGN_ADMIN]</b> / "
    "<a href=\"https://t.me/ely4plugg\">it's ely4plugg</a>"
)

# words shown when someone hits /start
START_COMMAND_TEXT = """
Привет! Я - @default_chatbot. Бот, который создан для автоматизации <a href="https://t.me/ely4plugg">канала</a> и связанного с ним <a href="https://t.me/+LNYVSiGEVcJlMDFi">чата</a> обсуждений.

Буквально читаю тебе свои умения с репозитория...
<blockquote>Бот подписывает опубликованные посты именем администратора, добавляет инлайн-клавиатуру со ссылками в комментариях и наводит порядок в чате (открепление сообщений, удаление стикеров, дедупликация комментариев для медиа-альбомов).</blockquote>

Если ты сам захотел посмотреть на то, из чего я сделан - загляни на GitHub по кнопке ниже.

Спасибо, удачи!

<tg-emoji emoji-id=\"5427344232568368005\">👺</tg-emoji> by <a href="https://t.me/ely4plugg">ELY4PLUGG</a>.
"""

# premium emoji drip - works only when the bot owner has Telegram Premium
START_COMMAND_CUSTOM_EMOJI_MENU = True
COMMENT_CUSTOM_EMOJI_MENU = True

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

# tg ids are numbers, so keep them that way
CHAT = int(CHAT)
CHANNEL = int(CHANNEL)
ADMIN = int(ADMIN)
LOG_CHAT = int(LOG_CHAT)
