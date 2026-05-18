"""
Transcript Cache
Simple in-memory store — holds transcript data per video_id.
Lives as long as the server is running.
No Redis, no DB, no complexity.
"""

# Simple dict: { video_id: { transcript, word_count } }
_cache: dict = {}


def save(video_id: str, transcript: str, word_count: int) -> None:
    """Store transcript data for a video."""
    _cache[video_id] = {
        "video_id": video_id,
        "transcript": transcript,
        "word_count": word_count,
    }


def get(video_id: str) -> dict | None:
    """Return cached transcript data or None if not found."""
    return _cache.get(video_id)


def exists(video_id: str) -> bool:
    """Check if transcript is already cached."""
    return video_id in _cache


def all_ids() -> list[str]:
    """Return list of all cached video IDs."""
    return list(_cache.keys())


def clear(video_id: str = None) -> None:
    """Clear one video or entire cache."""
    if video_id:
        _cache.pop(video_id, None)
    else:
        _cache.clear()