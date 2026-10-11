from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ChatModel(Base):
    __tablename__ = "chats"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Group Audio Settings
    default_volume: Mapped[int] = mapped_column(Integer, default=100)
    default_quality: Mapped[str] = mapped_column(String(16), default="high")
    is_247: Mapped[bool] = mapped_column(Boolean, default=False)
    autoleave: Mapped[bool] = mapped_column(Boolean, default=True)
    autoleave_delay: Mapped[int] = mapped_column(Integer, default=180)
    vote_skip_percent: Mapped[int] = mapped_column(Integer, default=50)

    total_plays: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
