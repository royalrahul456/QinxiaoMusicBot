from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Integer, Boolean, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class UserModel(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Personal Settings
    default_quality: Mapped[str] = mapped_column(String(16), default="high")
    default_volume: Mapped[int] = mapped_column(Integer, default=100)
    preferred_source: Mapped[str] = mapped_column(String(32), default="youtube")
    autoplay: Mapped[bool] = mapped_column(Boolean, default=False)
    lyrics_pref: Mapped[str] = mapped_column(String(16), default="text")  # text, synced

    # Metrics
    total_play_count: Mapped[int] = mapped_column(Integer, default=0)
    total_listening_time: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
