# one-time interactive login for the user account behind deletion audit
from telethon import TelegramClient

# local paths and Telegram application credentials
import config


# setup runner - ask for phone, login code and optional 2FA password
def create_mtproto_session() -> None:
    if config.API_ID is None or config.API_HASH is None:
        raise RuntimeError("add API_ID and API_HASH to .env first")

    # Telethon stores the authorized account in this ignored local file
    client = TelegramClient(
        config.DELETION_AUDIT_SESSION_PATH,
        config.API_ID,
        config.API_HASH,
    )
    client.start()

    # final identity check makes accidental account selection obvious
    current_user = client.get_me()
    if getattr(current_user, "bot", False):
        client.disconnect()
        raise RuntimeError("use a regular Telegram user account, not a bot token")

    username = getattr(current_user, "username", None)
    display_name = f"@{username}" if username else current_user.first_name
    client.disconnect()
    print(f"MTProto session is ready for {display_name} ({current_user.id})")
    print(f"session file: {config.DELETION_AUDIT_SESSION_PATH}")


# direct script launch - keep interactive auth away from systemd startup
if __name__ == "__main__":
    create_mtproto_session()
