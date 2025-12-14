"""非認知能力モデル"""
from sqlalchemy import BigInteger, Column, String, Text

from app.models.base import Base


class NonCogAbility(Base):
    """非認知能力マスターテーブル"""
    __tablename__ = "non_cog_abilities"
    __table_args__ = {"extend_existing": True}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
