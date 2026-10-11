from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class HistoryModel(Base):
    __tablename__ = "play_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    song_id: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(256))
    artist: Mapped[str] = mapped_column(String(256), default="Unknown Artist")
    duration: Mapped[int] = mapped_column(Integer, default=0)
    url: Mapped[str] = mapped_column(String(512))
    thumbnail: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    played_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
