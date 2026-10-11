from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PremiumKeyModel(Base):
    __tablename__ = "premium_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    plan_name: Mapped[str] = mapped_column(String(32), default="standard")  # standard, pro, ultimate
    duration_days: Mapped[int] = mapped_column(Integer, default=30)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    used_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    generated_by: Mapped[int] = mapped_column(BigInteger)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class PremiumSubModel(Base):
    __tablename__ = "premium_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)  # user_id or chat_id
    entity_type: Mapped[str] = mapped_column(String(16), default="user")        # user or chat
    plan_name: Mapped[str] = mapped_column(String(32), default="standard")
    activated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
