import logging
from typing import Optional, Dict, Any
try:
    from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
    from pytgcalls.types.input_stream.quality import HighQualityAudio
except ImportError:
    AudioPiped = None
    AudioVideoPiped = None
    HighQualityAudio = None

from app.audio.ffmpeg_filters import FFmpegFilterBuilder

logger = logging.getLogger("QinxiaoMusic.Audio.Processor")


class AudioProcessor:
    @staticmethod
    def build_ffmpeg_filter(
        equalizer: str = "off",
        bass_boost: int = 0,
        normalize: bool = False,
        volume: int = 100
    ) -> str:
        """Build an FFmpeg audio filter chain string (returns empty string if no filters are active)."""
        builder = FFmpegFilterBuilder()
        builder.set_volume(volume)
        builder.set_equalizer(equalizer)
        builder.set_bass_boost(bass_boost)
        builder.set_normalization(normalize)
        filter_str = builder.build_audio_filter_string()
        return "" if filter_str == "anull" else filter_str

    @staticmethod
    def build_ffmpeg_parameters(
        equalizer: str = "off",
        bass_boost: int = 0,
        normalize: bool = False,
        volume: int = 100,
        bitrate: str = "320k",
        seek_sec: Optional[int] = None
    ) -> str:
        """Build complete FFmpeg CLI parameters string for PyTgCalls MediaStream."""
        filter_str = AudioProcessor.build_ffmpeg_filter(
            equalizer=equalizer,
            bass_boost=bass_boost,
            normalize=normalize,
            volume=volume,
        )
        parts: list[str] = []
        if seek_sec is not None and seek_sec > 0:
            parts.append(f"-ss {int(seek_sec)}")
        if filter_str:
            parts.append(f'_-_end -af "{filter_str}"')
        return " ".join(parts)

    @staticmethod
    def create_input_stream(
        stream_url: str,
        volume: int = 100,
        equalizer: str = "off",
        bass_boost: int = 0,
        normalize: bool = False,
        bitrate: str = "320k",
        seek_sec: Optional[int] = None
    ):
        """Build PyTgCalls AudioPiped input stream with custom FFmpeg filters."""
        builder = FFmpegFilterBuilder()
        builder.set_volume(volume)
        builder.set_equalizer(equalizer)
        builder.set_bass_boost(bass_boost)
        builder.set_normalization(normalize)
        builder.set_bitrate(bitrate)

        ff_args = builder.build_ffmpeg_parameters(seek_sec=seek_sec)
        filter_str = builder.build_audio_filter_string()

        logger.debug(f"Creating AudioPiped stream with filters: '{filter_str}', bitrate: {bitrate}")

        if AudioPiped is None:
            return None

        try:
            return AudioPiped(
                stream_url,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=" ".join(ff_args) if ff_args else None
            )
        except Exception as e:
            logger.error(f"Error creating AudioPiped stream: {e}. Falling back to default AudioPiped.")
            return AudioPiped(stream_url, audio_parameters=HighQualityAudio())

