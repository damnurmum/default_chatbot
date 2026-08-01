# import markup and button for menu from telebot
from telebot.types import InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton

# vars for boolen func
from config import START_COMMAND_CUSTOM_EMOJI_MENU
from config import COMMENT_CUSTOM_EMOJI_MENU

# enable/disable custom emoji in start menu
def start_command_custom_emoji_menu_func(emoji_id: str):
    if START_COMMAND_CUSTOM_EMOJI_MENU:
        return emoji_id
    else:
        return None

# enable/disable custom emoji in comment menu
def comment_custom_emoji_menu_func(emoji_id: str):
    if COMMENT_CUSTOM_EMOJI_MENU:
        return emoji_id
    else:
        return None

# init menu for comment
menu = InlineKeyboardMarkup(row_width=1)
menu.add(
    InlineKeyboardButton("ПРЕДЛОЖКА", url="http://t.me/ely4plugg?direct", icon_custom_emoji_id=comment_custom_emoji_menu_func("5431471910888188907")),
)
menu.row_width = 2
menu.add(
    InlineKeyboardButton("ЧАТ", url="https://t.me/+LNYVSiGEVcJlMDFi", icon_custom_emoji_id=comment_custom_emoji_menu_func("5431861885328733737")),
    InlineKeyboardButton("БУСТ", url="http://t.me/boost/ely4plugg", icon_custom_emoji_id=comment_custom_emoji_menu_func("5429225887805515219"))
)
menu.row_width = 1
menu.add(
    InlineKeyboardButton("Владелец", url="https://t.me/ryaldum", icon_custom_emoji_id=comment_custom_emoji_menu_func("5397655168055544411"))
)

# init start menu for /start command
start_menu = InlineKeyboardMarkup(row_width=1)
start_menu.add(
    InlineKeyboardButton("Исходный код (GitHub)", url="https://github.com/damnurmum/default_chatbot", icon_custom_emoji_id=start_command_custom_emoji_menu_func("5431720954566844875"))
)
start_menu.row_width = 2
start_menu.add(
    InlineKeyboardButton("Канал", url="https://t.me/ely4plugg", icon_custom_emoji_id=start_command_custom_emoji_menu_func("5395485801549176028")),
    InlineKeyboardButton("Чат", url="https://t.me/+LNYVSiGEVcJlMDFi", icon_custom_emoji_id=start_command_custom_emoji_menu_func("5395746905495999058"))
)