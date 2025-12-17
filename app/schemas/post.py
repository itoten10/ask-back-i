"""投稿システムのスキーマ定義"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.post import QuestionStateChangeType


class PostCreate(BaseModel):
    """投稿作成リクエスト"""
    problem: str = Field(..., min_length=1, max_length=1000)
    content_1: str = Field(..., min_length=1)
    content_2: Optional[str] = None
    content_3: Optional[str] = None
    question_state_change_type: QuestionStateChangeType = QuestionStateChangeType.none
    phase_label: str = Field(..., min_length=1, max_length=50)
    ability_codes: list[str] = Field(default_factory=list)


class PostUpdate(BaseModel):
    """投稿更新リクエスト"""
    problem: str = Field(..., min_length=1, max_length=1000)
    content_1: str = Field(..., min_length=1)
    content_2: Optional[str] = None
    content_3: Optional[str] = None
    question_state_change_type: QuestionStateChangeType = QuestionStateChangeType.none
    phase_label: str = Field(..., min_length=1, max_length=50)
    ability_codes: list[str] = Field(default_factory=list)


class PostResponse(BaseModel):
    """投稿レスポンス"""
    id: int
    user_id: int
    problem: str
    content_1: str
    content_2: Optional[str]
    content_3: Optional[str]
    question_state_change_type: QuestionStateChangeType
    phase_label: str
    created_at: datetime
    updated_at: datetime

    # ユーザー情報も含める（フロントエンドで表示用）
    user_name: Optional[str] = None
    user_avatar_url: Optional[str] = None

    # いいね情報
    like_count: int = 0
    liked_by_me: bool = False

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    """投稿一覧レスポンス"""
    posts: list[PostResponse]
    total: int
