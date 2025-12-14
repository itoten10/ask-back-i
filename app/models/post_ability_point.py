"""投稿と非認知能力の関連モデル"""
from datetime import datetime
from sqlalchemy import BigInteger, Column, ForeignKey, Index, Integer, TIMESTAMP
from sqlalchemy.orm import relationship

from app.models.base import Base


class PostAbilityPoint(Base):
    """投稿と非認知能力の関連テーブル"""
    __tablename__ = "post_ability_points"
    __table_args__ = (
        Index("idx_post_ability_points_post_id", "post_id"),
        Index("idx_post_ability_points_ability_id", "ability_id"),
        {"extend_existing": True},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    post_id = Column(BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    ability_id = Column(BigInteger, ForeignKey("non_cog_abilities.id", ondelete="CASCADE"), nullable=False)
    action_index = Column(Integer, nullable=False, default=0)
    quality_level = Column(Integer, nullable=False, default=1)
    point = Column(Integer, nullable=False, default=1)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    # リレーション
    post = relationship("Post", back_populates="ability_points")
    ability = relationship("NonCogAbility")
