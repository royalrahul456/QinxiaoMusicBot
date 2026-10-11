from app.utils.time import format_uptime


def format_duration(seconds: int) -> str:
    """Format duration in seconds to mm:ss or hh:mm:ss string."""
    if seconds <= 0:
        return "00:00"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def build_progress_bar(current: int, total: int, length: int = 15) -> str:
    """Generate a visual progress bar string."""
    if total <= 0:
        return "🔘" + "▬" * (length - 1)

    percentage = min(1.0, max(0.0, current / total))
    filled_len = int(percentage * length)
    bar = "▬" * filled_len + "🔘" + "▬" * (length - filled_len - 1)
    return f"[{bar}] {format_duration(current)} / {format_duration(total)}"


def format_bytes(size: int) -> str:
    """Format byte size into human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size) < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def escape_markdown(text: str) -> str:
    """Sanitize brackets and backticks in user/track strings for Telegram Markdown."""
    if not text:
        return ""
    return text.replace("[", "(").replace("]", ")").replace("`", "'")

