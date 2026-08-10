# locks for safety, timers for cleanup - no chaos allowed
from threading import Lock, Timer
import time

# remember processed albums so one post gets one clean reply
processed_media_groups: dict[str, float] = {}

# album lock keeps parallel handler threads from replying twice
media_group_lock = Lock()

# match each channel post with the admin who dropped it
post_signs: dict[int, tuple[str, float]] = {}

# signature lock keeps reads and writes thread-safe
post_signs_lock = Lock()

# keep the memory fresh and throw old notes away
CLEANUP_MAX_AGE = 24 * 60 * 60  # keep entries for 24 hours
CLEANUP_INTERVAL = 60 * 60      # run cleanup every hour

# album dedup checker - first call wins, every next call skips
def is_media_group_processed(media_group_id: str) -> bool:
    with media_group_lock:
        if media_group_id in processed_media_groups:
            return True
        processed_media_groups[media_group_id] = time.time()
        return False

# signature keeper - remember who published a specific channel post
def set_post_sign(message_id: int, sign: str) -> None:
    with post_signs_lock:
        post_signs[message_id] = (sign, time.time())

# signature reader - return a safe anonymous fallback after cache misses
def get_post_sign(message_id: int | None, default: str = "АНОНИМ") -> str:
    if message_id is None:
        return default
    with post_signs_lock:
        # cached signature and its creation timestamp travel together
        entry = post_signs.get(message_id)
    return entry[0] if entry else default

# state sweeper - remove stale album and signature records
def _cleanup() -> None:
    # everything older than this timestamp is ready to leave
    cutoff = time.time() - CLEANUP_MAX_AGE

    with media_group_lock:
        # old album keys no longer help with deduplication
        stale = [k for k, added_at in processed_media_groups.items() if added_at < cutoff]
        for k in stale:
            del processed_media_groups[k]

    with post_signs_lock:
        # old signature records no longer match fresh discussion forwards
        stale = [k for k, (_, added_at) in post_signs.items() if added_at < cutoff]
        for k in stale:
            del post_signs[k]

    _schedule_cleanup()

# cleanup scheduler - daemon timer keeps maintenance off the hot path
def _schedule_cleanup() -> None:
    # one lightweight timer schedules the next sweep
    timer = Timer(CLEANUP_INTERVAL, _cleanup)
    timer.daemon = True
    timer.start()

_schedule_cleanup()
