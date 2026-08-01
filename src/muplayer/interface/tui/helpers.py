def format_time(seconds: int) -> str:
    """
    Formats a duration in seconds into a human-readable string. (DT-14)

    - Less than 1 hour:  MM:SS  (e.g. "3:07")
    - 1 hour or more:   H:MM:SS (e.g. "1:15:30")
    - Negative values are clamped to 0.
    """
    if seconds < 0:
        seconds = 0
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
