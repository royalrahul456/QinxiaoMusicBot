import os
import json
from typing import Annotated, List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Bot Identity (STRICT)
    BOT_NAME: str = "Qinxiao Music"
    BOT_USERNAME: str = "@QinxiaoMusicBot"

    # Telegram Credentials (Loaded from private .env)
    BOT_TOKEN: str = Field(default="")
    API_ID: int = Field(default=0)
    API_HASH: str = Field(default="")

    # Assistant User Session String (for Voice Chat WebRTC streaming)
    ASSISTANT_SESSION: Optional[str] = Field(default=None)

    # Permissions
    OWNER_ID: int = Field(default=0)
    SUDO_USERS: Annotated[List[int], NoDecode] = Field(default_factory=list)

    @field_validator("SUDO_USERS", mode="before")
    @classmethod
    def parse_sudo_users(cls, v):
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        return v

    # System & Execution
    FFMPEG_PATH: str = Field(default="ffmpeg")
    LOG_LEVEL: str = Field(default="INFO")

    # Database & Cache
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///qinxiao_music.db")
    REDIS_URL: Optional[str] = Field(default=None)
    USE_REDIS: bool = Field(default=False)

    # Music & Lyrics Credentials
    SPOTIFY_CLIENT_ID: Optional[str] = Field(default=None)
    SPOTIFY_CLIENT_SECRET: Optional[str] = Field(default=None)
    LYRICS_API_KEY: Optional[str] = Field(default=None)

    # Playback Defaults & Limits
    MAX_QUEUE_SIZE: int = Field(default=50)
    DEFAULT_VOLUME: int = Field(default=100)
    DEFAULT_QUALITY: str = Field(default="high")  # low, medium, high
    DEFAULT_BITRATE: str = Field(default="320k")  # 64k, 128k, 192k, 256k, 320k
    AUTO_LEAVE_TIMEOUT: int = Field(default=180)  # seconds
    VOTE_SKIP_PERCENTAGE: int = Field(default=50)  # percent

    # Rate Limiting & Anti-Spam
    COMMAND_RATE_LIMIT: float = Field(default=1.5)  # seconds between commands
    SEARCH_RATE_LIMIT: float = Field(default=3.0)   # seconds between searches


# Global settings instance
settings = Settings()
