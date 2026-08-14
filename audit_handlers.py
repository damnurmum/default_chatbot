# Bot API audit room - every available channel event lives here
import io
from datetime import datetime, timezone

# ContinueHandling lets the signing handler run after the audit handler
from telebot.handler_backends import ContinueHandling
from telebot.util import content_type_media, content_type_service

# local bot, audit destination and tiny dedup brain
from bot_instance import bot
from config import CHANNEL, LOG_CHAT
from state import is_media_group_processed


# every regular channel post type worth sending to the audit room
CHANNEL_POST_CONTENT_TYPES = list(dict.fromkeys(content_type_media + ["paid_media"]))

# service events live separately so boosts do not get logged twice
CHANNEL_SERVICE_CONTENT_TYPES = [
    content_type for content_type in content_type_service if content_type != "boost_added"
]


# post link builder - public URL when possible, message ID as fallback
def _post_link(message) -> str:
    # public channel username makes a clickable Telegram link
    username = getattr(message.chat, "username", None)
    if username:
        return f"https://t.me/{username}/{message.message_id}"
    return f"message id: {message.message_id}"


# content picker - preserve Telegram HTML when the post has text
def _message_content(message) -> str:
    if message.text:
        return message.html_text
    if message.caption:
        return message.html_caption
    return f"[{message.content_type} without text]"


# entity formatter - turn users and chats into readable audit labels
def _display_entity(entity) -> str:
    if entity is None:
        return "anonymous"

    # identity pieces collected from both User and Chat objects
    username = getattr(entity, "username", None)
    title = getattr(entity, "title", None)
    full_name = " ".join(
        part
        for part in (
            getattr(entity, "first_name", None),
            getattr(entity, "last_name", None),
        )
        if part
    )

    # best available display name plus the stable Telegram ID
    name = f"@{username}" if username else title or full_name or "unknown"
    entity_id = getattr(entity, "id", "?")
    return f"{name} ({entity_id})"


# reaction formatter - support regular, custom and paid reactions
def _reaction_name(reaction) -> str:
    # regular emoji wins because humans can read it instantly
    emoji = getattr(reaction, "emoji", None)
    if emoji:
        return emoji

    # custom emoji falls back to its Telegram file-style ID
    custom_emoji_id = getattr(reaction, "custom_emoji_id", None)
    if custom_emoji_id:
        return f"custom:{custom_emoji_id}"

    return getattr(reaction, "type", "unknown")


# reaction list formatter - one compact line for the audit message
def _reaction_list(reactions) -> str:
    return ", ".join(_reaction_name(reaction) for reaction in reactions) or "none"


# timestamp formatter - UTC keeps every server on the same clock
def _format_time(timestamp) -> str | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


# permission diff builder - expose every meaningful member change
def _member_changes(old_member, new_member) -> str:
    # fields handled separately do not belong in the permission diff
    ignored = {"user", "status"}

    # raw snapshots and the final list of changed primitive values
    old_values = vars(old_member)
    new_values = vars(new_member)
    changes = []

    for field in sorted((old_values.keys() | new_values.keys()) - ignored):
        # old and new values placed side by side for clean receipts
        old_value = old_values.get(field)
        new_value = new_values.get(field)
        if old_value != new_value and isinstance(
            old_value if old_value is not None else new_value,
            (bool, int, str),
        ):
            changes.append(f"{field}: {old_value} -> {new_value}")

    return "; ".join(changes) or "status only"


# audit sender - one clean format for the whole audit universe
def _send_audit(
    title: str,
    details: list[tuple[str, object]],
    report_content: str | None = None,
    report_name: str | None = None,
) -> None:
    # final message body shared by text logs and report captions
    audit_text = "\n".join(
        [title, *(f"- {name}: {value}" for name, value in details if value is not None)]
    )

    if report_content is None:
        bot.send_message(LOG_CHAT, audit_text)
        return

    # in-memory report file - no temporary disk mess needed
    binary_stream = io.BytesIO(str(report_content).encode("utf-8"))
    binary_stream.name = report_name or "audit-report.txt"
    bot.send_document(LOG_CHAT, binary_stream, caption=audit_text)


# post audit builder - attach original content and basic post metadata
def _audit_post(message, title: str) -> None:
    _send_audit(
        title,
        [
            ("by", message.author_signature or "?"),
            ("type", message.content_type),
            ("link", _post_link(message)),
        ],
        report_content=_message_content(message),
        report_name=f"report-{message.message_id}.txt",
    )


# edited post handler - no sneaky edit gets past the audit squad
@bot.edited_channel_post_handler(
    func=lambda message: message.chat.id == CHANNEL,
    content_types=CHANNEL_POST_CONTENT_TYPES,
)
def audit_edited_post(message):
    _audit_post(message, "post got edited")


# new post handler - audit first, then pass the post to the signing handler
@bot.channel_post_handler(
    func=lambda message: message.chat.id == CHANNEL,
    content_types=CHANNEL_POST_CONTENT_TYPES,
)
def audit_channel_post(message):
    # album ID and namespaced key keep audit dedup away from discussion dedup
    audit_group_id = getattr(message, "media_group_id", None)
    audit_key = f"channel-audit:{audit_group_id}" if audit_group_id else None
    if not audit_key or not is_media_group_processed(audit_key):
        _audit_post(message, "fresh post just dropped")

    return ContinueHandling()


# service event handler - catch pins, titles and giveaway updates
@bot.channel_post_handler(
    func=lambda message: message.chat.id == CHANNEL,
    content_types=CHANNEL_SERVICE_CONTENT_TYPES,
)
def audit_channel_service_event(message):
    _send_audit(
        "channel settings got remixed",
        [
            ("event", message.content_type),
            ("by", message.author_signature or "?"),
            ("link", _post_link(message)),
        ],
    )


# reaction handler - track every emoji switch with receipts
@bot.message_reaction_handler(func=lambda update: update.chat.id == CHANNEL)
def audit_message_reaction(update):
    # actor can be a user or an anonymous channel identity
    actor = update.user or update.actor_chat
    _send_audit(
        "reaction switch detected",
        [
            ("by", _display_entity(actor)),
            ("from", _reaction_list(update.old_reaction)),
            ("to", _reaction_list(update.new_reaction)),
            ("link", _post_link(update)),
            ("at", _format_time(getattr(update, "date", None))),
        ],
    )


# member audit builder - shared by users and the bot itself
def _audit_member_update(update, title: str) -> None:
    # before and after snapshots straight from Telegram
    old_member = update.old_chat_member
    new_member = update.new_chat_member
    _send_audit(
        title,
        [
            ("by", _display_entity(update.from_user)),
            ("target", _display_entity(new_member.user)),
            ("status", f"{old_member.status} -> {new_member.status}"),
            ("changes", _member_changes(old_member, new_member)),
            ("at", _format_time(getattr(update, "date", None))),
        ],
    )


# member handler - joins, leaves and admin rights stay visible
@bot.chat_member_handler(func=lambda update: update.chat.id == CHANNEL)
def audit_chat_member(update):
    _audit_member_update(update, "member status got remixed!")


# bot status handler - watch our own access level
@bot.my_chat_member_handler(func=lambda update: update.chat.id == CHANNEL)
def audit_bot_member(update):
    _audit_member_update(update, "bot access got remixed!")


# join request handler - log everyone waiting at the door
@bot.chat_join_request_handler(func=lambda request: request.chat.id == CHANNEL)
def audit_join_request(request):
    # exact invite link shows which entrance the user picked
    invite_link = getattr(request.invite_link, "invite_link", None)
    _send_audit(
        "join request pulled up!",
        [
            ("from", _display_entity(request.from_user)),
            ("bio", request.bio),
            ("invite", invite_link),
            ("at", _format_time(getattr(request, "date", None))),
        ],
    )


# boost source formatter - show both the source type and supporter
def _boost_source(source) -> str:
    # boost metadata can include a real user or stay anonymous
    source_type = getattr(source, "source", "unknown")
    user = getattr(source, "user", None)
    if user:
        return f"{source_type} by {_display_entity(user)}"
    return source_type


# boost handler - fresh support just landed
@bot.chat_boost_handler(func=lambda update: update.chat.id == CHANNEL)
def audit_chat_boost(update):
    # boost payload carries its ID, source and lifetime
    boost = update.boost
    _send_audit(
        "new boost just landed",
        [
            ("id", boost.boost_id),
            ("source", _boost_source(boost.source)),
            ("added", _format_time(boost.add_date)),
            ("expires", _format_time(boost.expiration_date)),
        ],
    )


# removed boost handler - even lost boosts leave a trace
@bot.removed_chat_boost_handler(func=lambda update: update.chat.id == CHANNEL)
def audit_removed_chat_boost(update):
    _send_audit(
        "boost left the building",
        [
            ("id", update.boost_id),
            ("source", _boost_source(update.source)),
            ("removed", _format_time(update.remove_date)),
        ],
    )
