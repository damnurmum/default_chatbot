# file work, but make it clean
from json import dump, load
from pathlib import Path

# local machinery
import config
from bot_instance import bot

# bundled animations mapped to their config keys
MEDIA_RESOURCES = {
    "START_COMMAND_GIF": config.BASE_DIR / "resources" / "start_gif.mp4",
    "COMMENT_GIF": config.BASE_DIR / "resources" / "comment_gif.mp4",
}

# Telegram update types the bot actually listens to
ALLOWED_UPDATES = [
    "message",
    "channel_post",
    "edited_channel_post",
    "message_reaction",
    "message_reaction_count",
    "chat_member",
    "my_chat_member",
    "chat_join_request",
    "chat_boost",
    "removed_chat_boost",
]

# media bootstrapper - upload each bundled animation only once
def initialize_media_ids(
    bot_client=bot,
    media_ids_path: Path = config.MEDIA_IDS_PATH,
):
    # cached IDs from disk or a clean slate for the first launch
    if media_ids_path.exists():
        with media_ids_path.open("r", encoding="utf-8") as file:
            media_ids = load(file)
    else:
        media_ids = {}

    # dirty flag decides whether the cache file needs a rewrite
    updated = False
    for setting_name, resource_path in MEDIA_RESOURCES.items():
        if media_ids.get(setting_name):
            continue

        with resource_path.open("rb") as resource:
            # Telegram response contains the reusable animation file ID
            message = bot_client.send_animation(
                config.ADMIN,
                resource,
                caption="ITS MESSAGE FOR GETTING ID OF MEDIA!!!",
            )
        media_ids[setting_name] = message.animation.file_id
        updated = True

    if updated:
        with media_ids_path.open("w", encoding="utf-8") as file:
            dump(media_ids, file, indent=4)
            file.write("\n")
        bot_client.send_message(config.ADMIN, "Success! Now bot is starting...")

    return media_ids


if __name__ == "__main__":
    # initialized IDs replace possible empty values from the first import
    initialized_media = initialize_media_ids()
    config.START_COMMAND_GIF = initialized_media["START_COMMAND_GIF"]
    config.COMMENT_GIF = initialized_media["COMMENT_GIF"]

    import handlers  # importing them registers every handler - tiny py magic

    # MTProto watcher runs beside TeleBot and catches deleted channel posts
    from mtproto_audit import start_deletion_audit

    start_deletion_audit()

    # listen only to updates we actually use; less noise, more speed
    bot.infinity_polling(allowed_updates=ALLOWED_UPDATES)
