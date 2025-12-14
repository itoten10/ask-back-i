"""投稿システムのモデル定義"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    DECIMAL,
    TIMESTAMP,
    Date,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# BigInteger for MySQL, Integer for SQLite
PKType = BigInteger().with_variant(Integer, "sqlite")


class QuestionStateChangeType(str, enum.Enum):
    """問いの状態変更タイプ"""
    none = "none"
    deepened = "deepened"
    changed = "changed"


class SignalColor(str, enum.Enum):
    """信号色"""
    red = "red"
    yellow = "yellow"
    green = "green"


class EvaluationPeriod(Base):
    """評価期間"""
    __tablename__ = "evaluation_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class AbilityRubric(Base):
    """能力ルーブリック"""
    __tablename__ = "ability_rubrics"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    ability_id: Mapped[int] = mapped_column(Integer, ForeignKey("non_cog_abilities.id"), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    coefficient: Mapped[float] = mapped_column(DECIMAL(3, 1), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class AbilityScoreBand(Base):
    """能力スコアバンド"""
    __tablename__ = "ability_score_bands"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    ability_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    band_order: Mapped[int] = mapped_column(Integer, nullable=False)
    signal_color: Mapped[SignalColor] = mapped_column(Enum(SignalColor), nullable=False)
    band_label: Mapped[str] = mapped_column(String(50), nullable=False)
    percentile_min: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=False)
    percentile_max: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)


class Post(Base):
    """投稿（やってみた）"""
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(PKType, ForeignKey("users.id"), nullable=False)
    problem: Mapped[str] = mapped_column(Text, nullable=False)
    content_1: Mapped[str] = mapped_column(Text, nullable=False)
    content_2: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_3: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    question_state_change_type: Mapped[QuestionStateChangeType] = mapped_column(
        Enum(QuestionStateChangeType),
        nullable=False,
        default=QuestionStateChangeType.none
    )
    phase_label: Mapped[str] = mapped_column(String(50), nullable=False)
    ai_raw_label: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)

    # リレーション
    user: Mapped["User"] = relationship("User", back_populates="posts")  # type: ignore
    ability_points: Mapped[list["PostAbilityPoint"]] = relationship("PostAbilityPoint", back_populates="post")  # type: ignore


class UserPeriodPostsCache(Base):
    """期間別投稿キャッシュ"""
    __tablename__ = "user_period_posts_cache"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(PKType, ForeignKey("users.id"), nullable=False)
    period_id: Mapped[int] = mapped_column(Integer, ForeignKey("evaluation_periods.id"), nullable=False)
    combined_post_text: Mapped[str] = mapped_column(Text, nullable=False)
    last_aggregated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
