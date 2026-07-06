# import main libs
from dotenv import load_dotenv
import os

# init post sign
POST_SIGN = "by <a href=\"https://t.me/ely4plugg\">ELY4PLUGG</a>."

# init some texts for messages
start_command_text="""
Привет! Я - @default_chatbot. Бот, который создан для автоматизации <a href="https://t.me/ely4plugg">канала</a> и связанного с ним <a href="https://t.me/+LNYVSiGEVcJlMDFi">чата</a> обсуждений.

Буквально читаю тебе свои умения с репозитория...
<blockquote>Бот подписывает опубликованные посты именем администратора, добавляет инлайн-клавиатуру со ссылками в комментариях и наводит порядок в чате (открепление сообщений, удаление стикеров, дедупликация комментариев для медиа-альбомов).</blockquote>

Если ты сам захотел посмотреть на то, из чего я сделан - загляни на GitHub по кнопке ниже.

Спасибо, удачи!

by <a href="https://t.me/ely4plugg">ELY4PLUGG</a>.
"""
test_command_text="bot is working."

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