"""感謝の手紙API"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.thanks_letter import ThanksLetter
from app.models.thanks_letter_ability_point import ThanksLetterAbilityPoint
from app.models.non_cog_ability import NonCogAbility
from app.models.user import User, RoleEnum
from app.schemas.thanks_letter import ThanksLetterCreate, ThanksLetterUpdate, ThanksLetterResponse

router = APIRouter()


@router.post("", response_model=ThanksLetterResponse, status_code=201)
async def create_thanks_letter(
    letter_data: ThanksLetterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ThanksLetterResponse:
    """感謝の手紙を作成"""
    # 受信者が存在するか確認
    receiver = await db.get(User, letter_data.receiver_user_id)
    if not receiver or receiver.is_deleted or not receiver.is_active:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # 管理者には感謝の手紙を送れない
    if receiver.role == RoleEnum.admin:
        raise HTTPException(status_code=400, detail="管理者には感謝の手紙を送ることはできません")

    # 感謝の手紙を作成
    letter = ThanksLetter(
        sender_user_id=current_user.id,
        receiver_user_id=letter_data.receiver_user_id,
        content_1=letter_data.content_1,
        content_2=letter_data.content_2,
        created_at=datetime.utcnow(),
    )

    db.add(letter)
    await db.commit()
    await db.refresh(letter)

    # 非認知能力の関連を保存（受信者の能力として記録）
    if letter_data.ability_codes:
        abilities_stmt = select(NonCogAbility).where(NonCogAbility.code.in_(letter_data.ability_codes))
        abilities_result = await db.execute(abilities_stmt)
        abilities = abilities_result.scalars().all()

        for ability in abilities:
            letter_ability_point = ThanksLetterAbilityPoint(
                thanks_letter_id=letter.id,
                ability_id=ability.id,
                points=1
            )
            db.add(letter_ability_point)

        await db.commit()

    # リレーションをロード
    await db.refresh(letter, ["sender", "receiver"])

    return ThanksLetterResponse(
        id=letter.id,
        sender_user_id=letter.sender_user_id,
        sender_name=letter.sender.full_name,
        receiver_user_id=letter.receiver_user_id,
        receiver_name=letter.receiver.full_name,
        content_1=letter.content_1,
        content_2=letter.content_2,
        created_at=letter.created_at,
    )


@router.get("", response_model=List[ThanksLetterResponse])
async def get_thanks_letters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ThanksLetterResponse]:
    """感謝の手紙一覧を取得（管理者・教師は全件、それ以外は自分の送受信のみ）"""
    # 管理者・教師は全ての手紙を閲覧可能
    if current_user.role in [RoleEnum.admin, RoleEnum.teacher]:
        stmt = (
            select(ThanksLetter)
            .options(joinedload(ThanksLetter.sender), joinedload(ThanksLetter.receiver))
            .order_by(ThanksLetter.created_at.desc())
        )
    else:
        stmt = (
            select(ThanksLetter)
            .options(joinedload(ThanksLetter.sender), joinedload(ThanksLetter.receiver))
            .where(
                (ThanksLetter.sender_user_id == current_user.id)
                | (ThanksLetter.receiver_user_id == current_user.id)
            )
            .order_by(ThanksLetter.created_at.desc())
        )

    result = await db.execute(stmt)
    letters = result.unique().scalars().all()

    return [
        ThanksLetterResponse(
            id=letter.id,
            sender_user_id=letter.sender_user_id,
            sender_name=letter.sender.full_name,
            receiver_user_id=letter.receiver_user_id,
            receiver_name=letter.receiver.full_name,
            content_1=letter.content_1,
            content_2=letter.content_2,
            created_at=letter.created_at,
        )
        for letter in letters
    ]


@router.get("/received", response_model=List[ThanksLetterResponse])
async def get_received_letters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ThanksLetterResponse]:
    """自分が受信した感謝の手紙一覧を取得"""
    stmt = (
        select(ThanksLetter)
        .options(joinedload(ThanksLetter.sender), joinedload(ThanksLetter.receiver))
        .where(ThanksLetter.receiver_user_id == current_user.id)
        .order_by(ThanksLetter.created_at.desc())
    )

    result = await db.execute(stmt)
    letters = result.unique().scalars().all()

    return [
        ThanksLetterResponse(
            id=letter.id,
            sender_user_id=letter.sender_user_id,
            sender_name=letter.sender.full_name,
            receiver_user_id=letter.receiver_user_id,
            receiver_name=letter.receiver.full_name,
            content_1=letter.content_1,
            content_2=letter.content_2,
            created_at=letter.created_at,
        )
        for letter in letters
    ]


@router.get("/sent", response_model=List[ThanksLetterResponse])
async def get_sent_letters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ThanksLetterResponse]:
    """自分が送信した感謝の手紙一覧を取得"""
    stmt = (
        select(ThanksLetter)
        .options(joinedload(ThanksLetter.sender), joinedload(ThanksLetter.receiver))
        .where(ThanksLetter.sender_user_id == current_user.id)
        .order_by(ThanksLetter.created_at.desc())
    )

    result = await db.execute(stmt)
    letters = result.unique().scalars().all()

    return [
        ThanksLetterResponse(
            id=letter.id,
            sender_user_id=letter.sender_user_id,
            sender_name=letter.sender.full_name,
            receiver_user_id=letter.receiver_user_id,
            receiver_name=letter.receiver.full_name,
            content_1=letter.content_1,
            content_2=letter.content_2,
            created_at=letter.created_at,
        )
        for letter in letters
    ]


@router.get("/users", response_model=List[dict])
async def get_users_for_letter(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[dict]:
    """感謝の手紙を送信できるユーザー一覧を取得（自分以外の有効なユーザー、管理者を除く）"""
    stmt = (
        select(User)
        .where(
            User.id != current_user.id,
            User.is_active == True,
            User.is_deleted == False,
            User.role != RoleEnum.admin,  # 管理者を除外
        )
        .order_by(User.full_name)
    )

    result = await db.execute(stmt)
    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "full_name": user.full_name,
            "role": user.role.value,
            "grade": user.grade,
            "class_name": user.class_name,
        }
        for user in users
    ]


@router.put("/{letter_id}", response_model=ThanksLetterResponse)
async def update_thanks_letter(
    letter_id: int,
    letter_data: ThanksLetterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ThanksLetterResponse:
    """感謝の手紙を更新（送信者本人のみ）"""
    # 手紙を取得
    stmt = select(ThanksLetter).where(ThanksLetter.id == letter_id)
    result = await db.execute(stmt)
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(status_code=404, detail="Thanks letter not found")

    # 送信者本人のみ更新可能
    if letter.sender_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own letters")

    # 手紙内容を更新
    letter.content_1 = letter_data.content_1
    letter.content_2 = letter_data.content_2

    # 既存の能力関連を削除
    delete_stmt = select(ThanksLetterAbilityPoint).where(ThanksLetterAbilityPoint.thanks_letter_id == letter_id)
    delete_result = await db.execute(delete_stmt)
    existing_points = delete_result.scalars().all()
    for point in existing_points:
        await db.delete(point)

    await db.commit()

    # 新しい能力関連を保存
    if letter_data.ability_codes:
        abilities_stmt = select(NonCogAbility).where(NonCogAbility.code.in_(letter_data.ability_codes))
        abilities_result = await db.execute(abilities_stmt)
        abilities = abilities_result.scalars().all()

        for ability in abilities:
            letter_ability_point = ThanksLetterAbilityPoint(
                thanks_letter_id=letter.id,
                ability_id=ability.id,
                points=1
            )
            db.add(letter_ability_point)

    await db.commit()
    await db.refresh(letter, ["sender", "receiver"])

    return ThanksLetterResponse(
        id=letter.id,
        sender_user_id=letter.sender_user_id,
        sender_name=letter.sender.full_name,
        receiver_user_id=letter.receiver_user_id,
        receiver_name=letter.receiver.full_name,
        content_1=letter.content_1,
        content_2=letter.content_2,
        created_at=letter.created_at,
    )
