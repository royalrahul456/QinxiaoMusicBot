import re
from typing import List
from app.lyrics.base import SyncedLine


def parse_lrc(lrc_text: str) -> List[SyncedLine]:
    """Parse raw LRC format text into timestamped SyncedLine objects."""
    pattern = re.compile(r"\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)")
    lines: List[SyncedLine] = []

    for line in lrc_text.splitlines():
        match = pattern.match(line.strip())
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            frac = match.group(3)
            ms_val = int(frac) * 10 if len(frac) == 2 else int(frac)
            total_ms = (minutes * 60 + seconds) * 1000 + ms_val
            text = match.group(4).strip()
            if text:
                lines.append(SyncedLine(timestamp_ms=total_ms, text=text))

    return lines
