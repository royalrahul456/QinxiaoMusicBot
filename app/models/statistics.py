from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class BotStatsModel(Base):
    __tablename__ = "bot_stats"

    stat_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    stat_value: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GroupStatsModel(Base):
    __tablename__ = "group_stats"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    total_plays: Mapped[int] = mapped_column(Integer, default=0)
    total_skips: Mapped[int] = mapped_column(Integer, default=0)
    total_time_seconds: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
