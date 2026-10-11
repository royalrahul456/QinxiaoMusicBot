from typing import List, Optional
from app.audio.quality import EQUALIZER_PRESETS, normalize_bitrate


class FFmpegFilterBuilder:
    def __init__(self):
        self._volume: float = 1.0  # 0.0 - 2.0
        self._bass_boost: int = 0   # 0 - 10
        self._equalizer: str = "off"
        self._normalize: bool = False
        self._bitrate: str = "320k"

    def set_volume(self, vol_percent: int) -> "FFmpegFilterBuilder":
        # 0 to 200 -> 0.0 to 2.0
        clamped = max(0, min(200, vol_percent))
        self._volume = clamped / 100.0
        return self

    def set_bass_boost(self, level: int) -> "FFmpegFilterBuilder":
        self._bass_boost = max(0, min(10, level))
        return self

    def set_equalizer(self, preset: str) -> "FFmpegFilterBuilder":
        if preset in EQUALIZER_PRESETS:
            self._equalizer = preset
        return self

    def set_normalization(self, enabled: bool) -> "FFmpegFilterBuilder":
        self._normalize = enabled
        return self

    def set_bitrate(self, bitrate: str) -> "FFmpegFilterBuilder":
        self._bitrate = normalize_bitrate(bitrate)
        return self

    def build_audio_filter_string(self) -> str:
        filters: List[str] = []

        # Volume filter
        if self._volume != 1.0:
            filters.append(f"volume={self._volume:.2f}")

        # Bass boost filter
        if self._bass_boost > 0:
            gain = self._bass_boost * 2
            filters.append(f"equalizer=f=60:width_type=h:width=40:g={gain}")

        # Equalizer preset filter
        eq_filter = EQUALIZER_PRESETS.get(self._equalizer)
        if eq_filter:
            filters.append(eq_filter)

        # Normalization filter (loudnorm)
        if self._normalize:
            filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

        return ",".join(filters) if filters else "anull"

    def build_ffmpeg_parameters(self, seek_sec: Optional[int] = None) -> List[str]:
        args: List[str] = []

        if seek_sec and seek_sec > 0:
            args.extend(["-ss", str(seek_sec)])

        af = self.build_audio_filter_string()
        if af != "anull":
            args.extend(["-af", af])

        args.extend(["-b:a", self._bitrate])
        args.extend(["-ar", "48000", "-ac", "2"])

        return args
