from telebot.types import InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton

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