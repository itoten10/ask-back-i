"""感謝の手紙モデル定義"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Integer, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# BigInteger for MySQL
PKType = BigInteger().with_variant(Integer, "sqlite")


class ThanksLetter(Base):
    """感謝の手紙"""
    __tablename__ = "thanks_letters"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    sender_user_id: Mapped[int] = mapped_column(PKType, ForeignKey("users.id"), nullable=False)
    receiver_user_id: Mapped[int] = mapped_column(PKType, ForeignKey("users.id"), nullable=False)
    content_1: Mapped[str] = mapped_column(Text, nullable=False)
    content_2: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)

    # リレーション
    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_user_id], back_populates="sent_letters")  # type: ignore
    receiver: Mapped["User"] = relationship("User", foreign_keys=[receiver_user_id], back_populates="received_letters")  # type: ignore
    ability_points: Mapped[list["ThanksLetterAbilityPoint"]] = relationship("ThanksLetterAbilityPoint", back_populates="thanks_letter")  # type: ignore
