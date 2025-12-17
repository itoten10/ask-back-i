"""感謝の手紙のスキーマ定義"""
from datetime import datetime
from pydantic import BaseModel, Field


class ThanksLetterCreate(BaseModel):
    """感謝の手紙作成リクエスト"""
    receiver_user_id: int = Field(..., description="受信者のユーザーID")
    content_1: str = Field(..., min_length=1, max_length=5000, description="内容1")
    content_2: str | None = Field(None, max_length=5000, description="内容2")
    ability_codes: list[str] = Field(default_factory=list, description="非認知能力コードのリスト")


class ThanksLetterUpdate(BaseModel):
    """感謝の手紙更新リクエスト"""
    content_1: str = Field(..., min_length=1, max_length=5000, description="内容1")
    content_2: str | None = Field(None, max_length=5000, description="内容2")
    ability_codes: list[str] = Field(default_factory=list, description="非認知能力コードのリスト")


class ThanksLetterResponse(BaseModel):
    """感謝の手紙レスポンス"""
    id: int
    sender_user_id: int
    sender_name: str
    sender_avatar_url: str | None
    receiver_user_id: int
    receiver_name: str
    receiver_avatar_url: str | None
    content_1: str
    content_2: str | None
    created_at: datetime

    class Config:
        from_attributes = True
