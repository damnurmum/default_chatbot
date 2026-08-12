# text and HTML magic
from html import escape

# grab every discussion content type without writing a whole novel
from telebot.util import content_type_media

# our local bot engine
from bot_instance import bot

# channel settings and media IDs - the secret sauce
from config import CHAT, CHANNEL, POST_SIGN
from config import COMMENT_GIF, START_COMMAND_GIF
from config import START_COMMAND_TEXT

# keyboards and tiny in-memory brain
from keyboard import menu, start_menu
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
    result = f"Пост был отправлен админом: {admin_sign}.\n\nt.me/ely4plugg"
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
