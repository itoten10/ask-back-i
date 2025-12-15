"""感謝の手紙と非認知能力の関連モデル"""
from sqlalchemy import BigInteger, Column, ForeignKey, Index, DECIMAL
from sqlalchemy.orm import relationship

from app.models.base import Base


class ThanksLetterAbilityPoint(Base):
    """感謝の手紙と非認知能力の関連テーブル"""
    __tablename__ = "thanks_letter_ability_points"
    __table_args__ = (
        Index("idx_thanks_letter_ability_points_thanks_letter_id", "thanks_letter_id"),
        Index("idx_thanks_letter_ability_points_ability_id", "ability_id"),
        {"extend_existing": True},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    thanks_letter_id = Column(BigInteger, ForeignKey("thanks_letters.id", ondelete="CASCADE"), nullable=False)
    ability_id = Column(BigInteger, ForeignKey("non_cog_abilities.id", ondelete="CASCADE"), nullable=False)
    points = Column(DECIMAL(5, 1), nullable=False, default=1.5, server_default="1.5")

    # リレーション
    thanks_letter = relationship("ThanksLetter", back_populates="ability_points")
    ability = relationship("NonCogAbility")
