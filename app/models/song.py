from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SongModel(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    song_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256))
    artist: Mapped[str] = mapped_column(String(256), default="Unknown Artist")
    album: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    duration: Mapped[int] = mapped_column(Integer, default=0)
    url: Mapped[str] = mapped_column(String(512))
    source: Mapped[str] = mapped_column(String(32), default="youtube")
    thumbnail: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    play_count: Mapped[int] = mapped_column(Integer, default=1)
    last_played_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
