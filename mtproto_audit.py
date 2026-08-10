# async MTProto engine wrapped in one quiet background thread
import asyncio
import io
import json
import logging
from pathlib import Path
from threading import Thread

# local config and the regular Bot API sender
import config
from bot_instance import bot


# module logger keeps startup failures visible in systemd journal
logger = logging.getLogger(__name__)

# short polling interval catches deletions without hammering Telegram
POLL_INTERVAL = 5


# state reader - None means this is the very first watcher launch
def _load_last_event_id(state_path: Path) -> int | None:
    try:
        with state_path.open("r", encoding="utf-8") as file:
            state = json.load(file)
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as error:
        raise RuntimeError(f"invalid deletion audit state: {state_path}") from error

    last_event_id = state.get("last_event_id")
    if not isinstance(last_event_id, int) or last_event_id < 0:
        raise RuntimeError(f"invalid deletion audit state: {state_path}")
    return last_event_id


# atomic state writer - a crash cannot leave half a JSON file behind
def _save_last_event_id(state_path: Path, event_id: int) -> None:
    temporary_path = state_path.with_suffix(f"{state_path.suffix}.tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump({"last_event_id": event_id}, file, indent=4)
        file.write("\n")
    temporary_path.replace(state_path)


# identity formatter - show a readable admin name and stable Telegram ID
def _display_admin(user) -> str:
    username = getattr(user, "username", None)
    full_name = " ".join(
        part
        for part in (
            getattr(user, "first_name", None),
            getattr(user, "last_name", None),
        )
        if part
    )
    name = f"@{username}" if username else full_name or "unknown"
    return f"{name} ({getattr(user, 'id', '?')})"


# media formatter - turn raw MTProto class names into compact audit labels
def _media_type(message) -> str:
    media = getattr(message, "media", None)
    if media is None:
        return "text"

    media_name = type(media).__name__
    return media_name.removeprefix("MessageMedia").lower() or "media"


# deleted message formatter - keep content readable even after the post is gone
def _message_report(message) -> str:
    message_id = getattr(message, "id", "?")
    post_author = getattr(message, "post_author", None) or "?"
    message_date = getattr(message, "date", None)
    message_text = getattr(message, "message", None) or "[no text]"

    return (
        f"message id: {message_id}\n"
        f"posted by: {post_author}\n"
        f"posted at: {message_date}\n"
        f"media: {_media_type(message)}\n\n"
        f"{message_text}"
    )


# batch builder - consecutive album items become one clean audit report
def _batch_deleted_events(events) -> list[list]:
    batches = []
    for event in sorted(events, key=lambda item: item.id):
        grouped_id = getattr(event.old, "grouped_id", None)
        previous_grouped_id = (
            getattr(batches[-1][0].old, "grouped_id", None) if batches else None
        )

        if grouped_id is not None and grouped_id == previous_grouped_id:
            batches[-1].append(event)
        else:
            batches.append([event])
    return batches


# report sender - Bot API delivers the MTProto receipts to the regular log chat
def _send_deleted_batch(bot_client, events) -> None:
    messages = [event.old for event in events]
    message_ids = ", ".join(str(message.id) for message in messages)
    deleted_by = _display_admin(events[0].user)
    deleted_at = events[-1].date
    event_id = max(event.id for event in events)
    title = "album got deleted" if len(messages) > 1 else "post got deleted"

    report_text = "\n\n".join(_message_report(message) for message in messages)
    report = io.BytesIO(report_text.encode("utf-8"))
    report.name = f"deleted-{message_ids.replace(', ', '-')}.txt"

    audit_text = (
        f"{title}\n"
        f"- by: {deleted_by}\n"
        f"- message ids: {message_ids}\n"
        f"- deleted at: {deleted_at}\n"
        f"- admin log event: {event_id}"
    )
    bot_client.send_document(config.LOG_CHAT, report, caption=audit_text)


# channel resolver - warm the entity cache when a raw numeric ID is not enough
async def _resolve_channel(client):
    try:
        return await client.get_entity(config.CHANNEL)
    except ValueError:
        async for dialog in client.iter_dialogs():
            if dialog.id == config.CHANNEL:
                return dialog.entity
    raise RuntimeError(f"MTProto cannot resolve channel {config.CHANNEL}")


# first-run baseline - skip old deletions and remember the newest event
async def _initialize_baseline(client, channel, state_path: Path) -> int:
    latest_event_id = 0
    async for event in client.iter_admin_log(channel, limit=1, delete=True):
        latest_event_id = event.id
    _save_last_event_id(state_path, latest_event_id)
    return latest_event_id


# one polling pass - fetch, send and checkpoint every unseen deletion
async def _poll_deletions(client, channel, bot_client, state_path, last_event_id):
    events = [
        event
        async for event in client.iter_admin_log(
            channel,
            limit=None,
            min_id=last_event_id,
            delete=True,
        )
        if event.id > last_event_id and event.deleted_message
    ]

    for batch in _batch_deleted_events(events):
        _send_deleted_batch(bot_client, batch)
        last_event_id = max(event.id for event in batch)
        _save_last_event_id(state_path, last_event_id)
    return last_event_id


# admin notifier - best effort only, because audit errors must not kill the bot
def _notify_admin(bot_client, text: str) -> None:
    logger.warning(text)
    try:
        bot_client.send_message(config.ADMIN, text)
    except Exception:
        logger.exception("failed to notify admin about MTProto audit")


# status sender - confirm a healthy watcher without marking it as a warning
def _send_admin_status(bot_client, text: str) -> None:
    logger.info(text)
    try:
        bot_client.send_message(config.ADMIN, text)
    except Exception:
        logger.exception("failed to send MTProto audit status")


# async watcher - own the authorized user session and reconnect loop
async def _run_deletion_audit(bot_client) -> None:
    try:
        from telethon import TelegramClient
    except ImportError as error:
        raise RuntimeError("Telethon is not installed") from error

    client = TelegramClient(
        config.DELETION_AUDIT_SESSION_PATH,
        config.API_ID,
        config.API_HASH,
    )

    try:
        await client.connect()
        if not await client.is_user_authorized():
            raise RuntimeError(
                "MTProto user session is not authorized; "
                "run create_mtproto_session.py"
            )

        current_user = await client.get_me()
        if getattr(current_user, "bot", False):
            raise RuntimeError("MTProto deletion audit requires a user session")

        channel = await _resolve_channel(client)
        last_event_id = _load_last_event_id(config.DELETION_AUDIT_STATE_PATH)

        if last_event_id is None:
            last_event_id = await _initialize_baseline(
                client,
                channel,
                config.DELETION_AUDIT_STATE_PATH,
            )

        _send_admin_status(bot_client, "MTProto deletion audit is online")
        # repeated network failures get one alert instead of endless spam
        last_error_text = None
        while True:
            try:
                last_event_id = await _poll_deletions(
                    client,
                    channel,
                    bot_client,
                    config.DELETION_AUDIT_STATE_PATH,
                    last_event_id,
                )
                if last_error_text is not None:
                    _send_admin_status(
                        bot_client,
                        "MTProto deletion audit is online again",
                    )
                    last_error_text = None
            except Exception as error:
                error_text = f"{type(error).__name__}: {error}"
                if error_text != last_error_text:
                    _notify_admin(
                        bot_client,
                        f"MTProto deletion audit error: {error_text}",
                    )
                    last_error_text = error_text
            await asyncio.sleep(POLL_INTERVAL)
    finally:
        await client.disconnect()


# thread target - isolate the asyncio loop from synchronous TeleBot polling
def _run_deletion_audit_thread(bot_client) -> None:
    try:
        asyncio.run(_run_deletion_audit(bot_client))
    except Exception as error:
        _notify_admin(bot_client, f"MTProto deletion audit stopped: {error}")


# public starter - missing setup disables only this optional watcher
def start_deletion_audit(bot_client=bot) -> Thread | None:
    if config.API_ID is None or config.API_HASH is None:
        _notify_admin(
            bot_client,
            "MTProto deletion audit is disabled: add API_ID and API_HASH to .env",
        )
        return None

    if not config.DELETION_AUDIT_SESSION_PATH.exists():
        _notify_admin(
            bot_client,
            "MTProto deletion audit is disabled: run create_mtproto_session.py",
        )
        return None

    thread = Thread(
        target=_run_deletion_audit_thread,
        args=(bot_client,),
        name="mtproto-deletion-audit",
        daemon=True,
    )
    thread.start()
    return thread
