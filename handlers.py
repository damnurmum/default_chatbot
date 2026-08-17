# text and HTML magic
from html import escape

# grab every discussion content type without writing a whole novel
from telebot.util import content_type_media
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import re

# our local bot engine
from bot_instance import bot

# channel settings and media IDs - the secret sauce
from config import CHAT, CHANNEL, POST_SIGN, COMMENT_SIGN
from config import COMMENT_GIF, START_COMMAND_GIF
from config import START_COMMAND_TEXT, ADMIN

# keyboards and tiny in-memory brain
from keyboard import menu, start_menu, admin_menu
from state import is_media_group_processed, set_post_sign, get_post_sign


# magic suffix that asks the bot to remove itself without adding a footer
NO_EDIT_SUFFIX = "\n\n[NO_EDIT]"

# content types that support text or caption edits
SIGNABLE_CONTENT_TYPES = [
    "text",
    "photo",
    "video",
    "document",
    "audio",
    "animation",
    "voice",
]

# for admin panel: post parse with buttons
BUTTONS_BLOCK_RE = re.compile(r'\[BUTTONS\s+RAW=(\d+)\](.*?)\[/BUTTONS\]', re.DOTALL)
BTN_RE = re.compile(r'\[BTN\s+LINK="([^"]+)"\](.*?)\[/BTN\]', re.DOTALL)
pending_posts = {}  # admin_chat_id -> {"from_chat_id": int, "message_id": int, "markup": InlineKeyboardMarkup | None}


# footer builder - safe HTML goes in, clean signature comes out
def _post_sign(author_signature: str | None) -> str:
    # sanitized admin name ready for the HTML template
    author = escape(author_signature or "АНОНИМ")
    return POST_SIGN.replace("[SIGN_ADMIN]", author)


# marker cleaner - remove only the suffix at the very end
def _strip_no_edit_suffix(text: str) -> str:
    if text.endswith(NO_EDIT_SUFFIX):
        return text[:-len(NO_EDIT_SUFFIX)]
    return text


# discussion text builder - remember who dropped the channel post
def _text_for_comment(admin_sign: str | None) -> str:
    if admin_sign is None:
        admin_sign = "АНОНИМ"

    # final caption ready for the discussion GIF
    result = COMMENT_SIGN.replace("[SIGN_ADMIN]", admin_sign)
    return result


# /start handler - enter with style
@bot.message_handler(commands=["start"])
def handler_start(message):
    bot.send_animation(
        message.chat.id,
        START_COMMAND_GIF,
        caption=START_COMMAND_TEXT,
        reply_markup=start_menu,
        parse_mode="HTML",
    )


# /admin handler - admin panel with buttons
@bot.message_handler(commands=["admin"])
def handler_admin(message):
    if message.from_user.id != ADMIN: return
    if message.chat.id != ADMIN: return

    bot.send_message(message.chat.id, "Админ-панель. Используйте кнопки ниже для навигации.", reply_markup=admin_menu)

# callback query handler for buttons
@bot.callback_query_handler(func=lambda callback: True)
def admin_menu_post_buttons_cb(call):
    if call.data == "admin_menu_post_buttons":
        bot.answer_callback_query(call.id, text="...")
        bot.clear_step_handler_by_chat_id(call.message.chat.id)

        bot_msg = bot.edit_message_text(
            "Перешлите или отправьте пост (текст/медиа с подписью):",
            call.message.chat.id, call.message.id,
            reply_markup=None
        )
        bot.register_next_step_handler(bot_msg, admin_menu_post_content_step, bot_msg)

    elif call.data == "admin_menu_post_buttons_send":
        chat_id = call.message.chat.id
        draft = pending_posts.pop(chat_id, None)

        if draft is None:
            bot.answer_callback_query(call.id, text="Черновик не найден, начните заново", show_alert=True)
            return

        bot.copy_message(
            CHANNEL,
            from_chat_id=draft["from_chat_id"],
            message_id=draft["message_id"],
            reply_markup=draft["markup"]
        )

        bot.answer_callback_query(call.id, text="Опубликовано!")
        bot.send_message(chat_id, "Пост отправлен в канал!")

    elif call.data == "admin_menu_post_buttons_skip":
        chat_id = call.message.chat.id
        draft = pending_posts.get(chat_id)

        if draft is None:
            bot.answer_callback_query(call.id, text="Черновик не найден, начните заново", show_alert=True)
            return

        draft["markup"] = None
        show_send_confirmation(chat_id, call.message.id, draft)

# post with buttons: wait text for posting
def admin_menu_post_content_step(message, bot_msg):
    chat_id = bot_msg.chat.id

    pending_posts[chat_id] = {
        "from_chat_id": message.chat.id,
        "message_id": message.message_id,
        "markup": None,
    }

    example = '[BUTTONS RAW=1][BTN LINK="https://t.me/durov"]ME[/BTN][/BUTTONS][BUTTONS RAW=2][BTN LINK="https://t.me/durov"]FRIEND 1[/BTN][BTN LINK="https://t.me/durov"]FRIEND 2[/BTN][/BUTTONS]'

    skip_markup = InlineKeyboardMarkup()
    skip_markup.row(InlineKeyboardButton("Без кнопок", callback_data="admin_menu_post_buttons_skip"))

    bot_msg2 = bot.send_message(
        chat_id,
        f"Пост принят. Теперь отправьте разметку кнопок или нажмите \"Без кнопок\".\n\nПример...\n```\n{example}```",
        reply_markup=skip_markup,
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(bot_msg2, admin_menu_post_buttons_step, chat_id)

# post with buttons: preview text with buttons, button "send", part #1
def admin_menu_post_buttons_step(message, chat_id):
    buttons_text = message.text
    markup = parse_buttons_only(buttons_text)

    if markup is None:
        bot.send_message(chat_id, "Не удалось распознать разметку кнопок, попробуйте ещё раз или нажмите \"Без кнопок\".")
        return

    draft = pending_posts[chat_id]
    draft["markup"] = markup

    show_send_confirmation(chat_id, None, draft)

# post with buttons: preview text with buttons, button "send", part #2
def show_send_confirmation(chat_id, message_id, draft):
    preview_markup = InlineKeyboardMarkup(row_width=1)
    if draft["markup"] is not None:
        for row in draft["markup"].keyboard:
            preview_markup.row(*row)
    preview_markup.row(InlineKeyboardButton("ОТПРАВИТЬ", callback_data="admin_menu_post_buttons_send"))

    bot.copy_message(
        chat_id,
        from_chat_id=draft["from_chat_id"],
        message_id=draft["message_id"],
        reply_markup=preview_markup
    )

# post with buttons: func for parse buttons
def parse_buttons_only(text: str):
    matches = BUTTONS_BLOCK_RE.finditer(text)
    rows = []
    for m in matches:
        buttons_in_block = BTN_RE.findall(m.group(2))
        row = [
            InlineKeyboardButton(text=btn_text.strip(), url=btn_url.strip())
            for btn_url, btn_text in buttons_in_block
        ]
        if row:
            rows.append(row)

    if not rows:
        return None

    markup = InlineKeyboardMarkup()
    for row in rows:
        markup.row(*row)
    return markup


# new post handler - sign it and keep it clean
@bot.channel_post_handler(content_types=SIGNABLE_CONTENT_TYPES)
def handler_channel_post(message):
    if message.chat.id != CHANNEL:
        return

    # post author cached for the future discussion reply
    sign = message.author_signature or "АНОНИМ"
    set_post_sign(message.id, sign)

    # touch only the shared album caption; Telegram gets weird otherwise
    if message.media_group_id and not message.caption:
        return

    # rendered footer ready for Telegram HTML mode
    post_sign = _post_sign(sign)

    if message.text:
        if message.text.endswith(NO_EDIT_SUFFIX):
            # clean text after the control marker disappears
            new_text = _strip_no_edit_suffix(message.html_text)
        else:
            # signed text ready to replace the original post
            new_text = f"{message.html_text}\n\n{post_sign}"
        bot.edit_message_text(
            new_text,
            message.chat.id,
            message.id,
            disable_web_page_preview=True,
            parse_mode="HTML",
        )
        return

    if message.caption:
        if message.caption.endswith(NO_EDIT_SUFFIX):
            # clean caption after the control marker disappears
            new_caption = _strip_no_edit_suffix(message.html_caption)
        else:
            # signed caption ready to replace the original media caption
            new_caption = f"{message.html_caption}\n\n{post_sign}"
    else:
        # media without text gets a footer as its first caption
        new_caption = post_sign

    bot.edit_message_caption(
        new_caption,
        message.chat.id,
        message.id,
        parse_mode="HTML",
    )


# discussion handler - one reply per album, zero random pins
@bot.message_handler(content_types=content_type_media)
def handler_send_message(message):
    if message.chat.id != CHAT:
        return
    if not message.forward_from_chat:
        return
    if message.forward_from_chat.type != "channel":
        return

    if message.content_type == "sticker":
        bot.delete_message(message.chat.id, message.id)
        return

    if message.media_group_id:
        if is_media_group_processed(message.media_group_id):
            return

    # cached post author used in the automatic discussion reply
    sign = get_post_sign(message.forward_from_message_id)

    bot.send_animation(
        message.chat.id,
        COMMENT_GIF,
        caption=_text_for_comment(sign),
        reply_markup=menu,
        reply_to_message_id=message.id,
    )
    bot.unpin_chat_message(CHAT, message.id)