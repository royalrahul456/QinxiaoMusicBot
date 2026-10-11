from typing import Dict

QUALITY_PROFILES: Dict[str, str] = {
    "low": "64k",
    "medium": "128k",
    "high": "320k",
}

VALID_BITRATES = ["64k", "128k", "192k", "256k", "320k"]

EQUALIZER_PRESETS: Dict[str, str] = {
    "off": "",
    "flat": "equalizer=f=1000:width_type=h:width=200:g=0",
    "rock": "equalizer=f=60:width_type=h:width=40:g=4,equalizer=f=1000:width_type=h:width=200:g=-2,equalizer=f=10000:width_type=h:width=2000:g=5",
    "pop": "equalizer=f=100:width_type=h:width=50:g=2,equalizer=f=1000:width_type=h:width=200:g=3,equalizer=f=10000:width_type=h:width=2000:g=1",
    "jazz": "equalizer=f=100:width_type=h:width=50:g=3,equalizer=f=1000:width_type=h:width=200:g=1,equalizer=f=5000:width_type=h:width=1000:g=3",
    "classical": "equalizer=f=100:width_type=h:width=50:g=4,equalizer=f=1000:width_type=h:width=200:g=0,equalizer=f=10000:width_type=h:width=2000:g=3",
    "bass": "equalizer=f=60:width_type=h:width=40:g=8",
}


def normalize_bitrate(bitrate_str: str) -> str:
    val = bitrate_str.lower().strip()
    if not val.endswith("k"):
        val += "k"
    return val if val in VALID_BITRATES else "320k"
