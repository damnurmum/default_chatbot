# import content type from telebot
from telebot.util import content_type_media

# import vars from local libs
from bot_instance import bot

# config vars
from config import CHAT, CHANNEL, POST_SIGN
from config import COMMENT_GIF, START_COMMAND_GIF
from config import START_COMMAND_TEXT

# other
from keyboard import menu, start_menu
from state import is_media_group_processed, set_post_sign, get_post_sign

# gen text for comment
def text_for_comment(admin_sign: str | None) -> str:
    if admin_sign is None:
        admin_sign = "АНОНИМ"

    result = (
        f"Пост был отправлен админом: {admin_sign}.\n\n" +
        "t.me/ely4plugg"
    )
    return result

# /start command
@bot.message_handler(commands=["start"])
def handler_start(message):
    bot.send_animation(message.chat.id, START_COMMAND_GIF, caption=START_COMMAND_TEXT, reply_markup=start_menu, parse_mode="HTML")

# edit channel post
@bot.channel_post_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'animation', 'voice'])
def handler_channel_post(message):
    if message.chat.id != CHANNEL:
        return

    sign = message.author_signature or "АНОНИМ"
    set_post_sign(message.id, sign)

    channel_text = message.text or message.caption or None

    if channel_text:
        if message.text:
            bot.edit_message_text(
                f"{message.html_text}\n\n{POST_SIGN}",
                message.chat.id,
                message.id,
                disable_web_page_preview=True,
                parse_mode="HTML",
            )
        elif message.caption:
            bot.edit_message_caption(
                f"{message.html_caption}\n\n{POST_SIGN}",
                message.chat.id,
                message.id,
                parse_mode="HTML",
            )
    else:
        bot.edit_message_caption(POST_SIGN, message.chat.id, message.id, parse_mode="HTML")

# auto unpin and reply in discussion chat, dedup albums
@bot.message_handler(content_types=content_type_media)
def handler_send_message(message):
    if message.chat.id != CHAT:
        return
    if not message.forward_from_chat:
        return
    if message.forward_from_chat.type != 'channel':
        return

    if message.content_type == "sticker":
        bot.delete_message(message.chat.id, message.id)
        return

    if message.media_group_id:
        if is_media_group_processed(message.media_group_id):
            return

    sign = get_post_sign(message.forward_from_message_id)

    bot.send_animation(message.chat.id, COMMENT_GIF, caption=text_for_comment(sign), reply_markup=menu, reply_to_message_id=message.id)
    bot.unpin_chat_message(CHAT, message.id)