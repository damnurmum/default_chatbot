# import markup and button for menu from telebot
from telebot.types import InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton

# init menu for comment
menu = InlineKeyboardMarkup(row_width=3)
menu.add(
    InlineKeyboardButton("ПРЕДЛОЖКА", url="http://t.me/ely4plugg?direct"),
    InlineKeyboardButton("ЧАТ", url="https://t.me/+LNYVSiGEVcJlMDFi"),
    InlineKeyboardButton("БУСТ", url="http://t.me/boost/ely4plugg")
)
menu.row_width = 2
menu.add(
    InlineKeyboardButton("Владелец", url="https://t.me/aIt_hub"),
    InlineKeyboardButton("Депка", url="https://t.me/ryaldum")
)

# init start menu for /start command
start_menu = InlineKeyboardMarkup(row_width=1)
start_menu.add(
    InlineKeyboardButton("Исходный код (GitHub)", url="https://github.com/damnurmum/default_chatbot")
)
start_menu.row_width = 2
start_menu.add(
    InlineKeyboardButton("Канал", url="https://t.me/ely4plugg"),
    InlineKeyboardButton("Чат", url="https://t.me/+LNYVSiGEVcJlMDFi")
)