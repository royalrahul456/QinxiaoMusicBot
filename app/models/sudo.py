from datetime import datetime
from sqlalchemy import BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SudoUserModel(Base):
    __tablename__ = "sudo_users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    added_by: Mapped[int] = mapped_column(BigInteger)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
