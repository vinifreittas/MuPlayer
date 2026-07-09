def format_time(time: int) -> str:
    """Formats a duration in seconds into a MM:SS string."""
    minutes, seconds = divmod(time, 60)
    return f"{minutes}:{seconds:02d}"
