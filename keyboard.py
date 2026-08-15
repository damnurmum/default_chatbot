# buttons and layouts - the visual drip
from telebot.types import InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton

# emoji switches from the config
from config import START_COMMAND_CUSTOM_EMOJI_MENU
from config import COMMENT_CUSTOM_EMOJI_MENU

# toggle premium emoji in the start menu
def start_command_custom_emoji_menu_func(emoji_id: str):
    if START_COMMAND_CUSTOM_EMOJI_MENU:
        return emoji_id
    else:
        return None

# toggle premium emoji under channel posts
def comment_custom_emoji_menu_func(emoji_id: str):
    if COMMENT_CUSTOM_EMOJI_MENU:
        return emoji_id
    else:
        return None

# build the comment menu
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

# build the /start menu
start_menu = InlineKeyboardMarkup(row_width=1)
start_menu.add(
    InlineKeyboardButton("Исходный код (GitHub)", url="https://github.com/damnurmum/default_chatbot", icon_custom_emoji_id=start_command_custom_emoji_menu_func("5431720954566844875"))
)
start_menu.row_width = 2
start_menu.add(
    InlineKeyboardButton("Канал", url="https://t.me/ely4plugg", icon_custom_emoji_id=start_command_custom_emoji_menu_func("5395485801549176028")),
    InlineKeyboardButton("Чат", url="https://t.me/+LNYVSiGEVcJlMDFi", icon_custom_emoji_id=start_command_custom_emoji_menu_func("5395746905495999058"))
)

admin_menu = InlineKeyboardMarkup(row_width=1)
admin_menu.add(
    InlineKeyboardButton("Пост с кнопками", callback_data="admin_menu_post_buttons")
)