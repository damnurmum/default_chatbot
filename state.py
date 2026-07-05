from threading import Lock, Timer
import time

# --- дедупликация альбомов (media_group_id) ---
# значение = время добавления, чтобы можно было чистить старые записи
processed_media_groups: dict[str, float] = {}
media_group_lock = Lock()

# --- подпись админа для конкретного поста в канале ---
# key = id сообщения в канале, value = (подпись, время добавления)
post_signs: dict[int, tuple[str, float]] = {}
post_signs_lock = Lock()

# сколько секунд хранить записи, прежде чем считать их устаревшими
CLEANUP_MAX_AGE = 24 * 60 * 60  # 24 часа
CLEANUP_INTERVAL = 60 * 60      # запускать очистку раз в час


def is_media_group_processed(media_group_id: str) -> bool:
    """Проверяет и сразу помечает media_group_id как обработанный (атомарно)."""
    with media_group_lock:
        if media_group_id in processed_media_groups:
            return True
        processed_media_groups[media_group_id] = time.time()
        return False


def set_post_sign(message_id: int, sign: str) -> None:
    with post_signs_lock:
        post_signs[message_id] = (sign, time.time())


def get_post_sign(message_id: int | None, default: str = "АНОНИМ") -> str:
    if message_id is None:
        return default
    with post_signs_lock:
        entry = post_signs.get(message_id)
    return entry[0] if entry else default


def _cleanup() -> None:
    cutoff = time.time() - CLEANUP_MAX_AGE

    with media_group_lock:
        stale = [k for k, added_at in processed_media_groups.items() if added_at < cutoff]
        for k in stale:
            del processed_media_groups[k]

    with post_signs_lock:
        stale = [k for k, (_, added_at) in post_signs.items() if added_at < cutoff]
        for k in stale:
            del post_signs[k]

    _schedule_cleanup()


def _schedule_cleanup() -> None:
    timer = Timer(CLEANUP_INTERVAL, _cleanup)
    timer.daemon = True
    timer.start()


# запускаем периодическую очистку сразу при импорте модуля
_schedule_cleanup()