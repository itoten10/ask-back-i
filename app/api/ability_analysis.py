"""能力判定API（テスト用）"""
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.ability_analyzer_service import ability_analyzer_service, ABILITIES


router = APIRouter(prefix="/ability-analysis", tags=["ability-analysis"])


class AnalyzeRequest(BaseModel):
    """能力判定リクエスト"""
    problem: Optional[str] = Field(None, description="課題・問い")
    content: str = Field(..., min_length=1, description="やってみたこと")


class MatchedAbility(BaseModel):
    """マッチした能力"""
    code: str
    name: str
    level: int = Field(..., ge=1, le=5, description="5段階レベル評価（1〜5）")
    level_reason: str = Field(..., description="レベル判定の根拠（ルーブリック参照）")
    reason: str = Field(..., description="該当理由（具体的な活動内容の引用）")


class AnalyzeResponse(BaseModel):
    """能力判定レスポンス"""
    matched_abilities: list[MatchedAbility]
    analysis_summary: str
    error: Optional[str] = None


class AbilityInfo(BaseModel):
    """能力情報"""
    code: str
    name: str
    description: str


class AbilitiesListResponse(BaseModel):
    """能力一覧レスポンス"""
    abilities: list[AbilityInfo]


@router.get("/abilities", response_model=AbilitiesListResponse)
async def get_abilities():
    """非認知能力の一覧を取得"""
    return AbilitiesListResponse(
        abilities=[AbilityInfo(**a) for a in ABILITIES]
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_abilities(request: AnalyzeRequest):
    """
    投稿内容から該当する非認知能力をAIで判定する

    - **problem**: 課題・問い（任意）
    - **content**: やってみたこと（必須）

    AIが投稿内容を分析し、7つの非認知能力のうち該当するものを返します。
    """
    if not request.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="content is required"
        )

    result = await ability_analyzer_service.analyze_abilities(
        content=request.content,
        problem=request.problem
    )

    return AnalyzeResponse(
        matched_abilities=[
            MatchedAbility(**a) for a in result.get("matched_abilities", [])
        ],
        analysis_summary=result.get("analysis_summary", ""),
        error=result.get("error")
    )
