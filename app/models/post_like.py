"""投稿いいねのモデル定義"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Integer,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# BigInteger for MySQL, Integer for SQLite
PKType = BigInteger().with_variant(Integer, "sqlite")


class PostLike(Base):
    """投稿のいいね"""
    __tablename__ = "post_likes"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_like_post_user"),
    )

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(PKType, ForeignKey("posts.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(PKType, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)

    # リレーション
    post: Mapped["Post"] = relationship("Post", back_populates="likes")  # type: ignore
    user: Mapped["User"] = relationship("User")  # type: ignore
