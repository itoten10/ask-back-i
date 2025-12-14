"""ダッシュボードAPI（管理者・教師用）"""
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.post import Post, QuestionStateChangeType
from app.models.post_ability_point import PostAbilityPoint
from app.models.thanks_letter import ThanksLetter
from app.models.thanks_letter_ability_point import ThanksLetterAbilityPoint
from app.models.non_cog_ability import NonCogAbility
from app.models.user import User, RoleEnum

# 介入フラグの閾値（投稿がない日数）
INTERVENTION_DAYS_THRESHOLD = 14

# フェーズラベルの変換マッピング（英語→日本語）
PHASE_LABEL_MAP = {
    # 旧英語フェーズ名
    "theme_setting": "テーマ設定",
    "problem_setting": "課題設定",
    "information_gathering": "情報収集",
    "analysis": "整理・分析",
    "summary": "まとめ・表現",
    "presentation": "発表準備",
    # 別の旧英語フェーズ名
    "planning": "課題設定",
    "execution": "情報収集",
    "verification": "整理・分析",
    # 日本語はそのまま返す
    "テーマ設定": "テーマ設定",
    "課題設定": "課題設定",
    "情報収集": "情報収集",
    "整理・分析": "整理・分析",
    "まとめ・表現": "まとめ・表現",
    "発表準備": "発表準備",
}

router = APIRouter()


@router.get("/learning-progress")
async def get_learning_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """探求学習の進捗状況を取得（生徒ごと）"""
    # 管理者と教師のみアクセス可能
    if current_user.role not in [RoleEnum.admin, RoleEnum.teacher]:
        raise HTTPException(status_code=403, detail="管理者または教師のみアクセス可能です")

    # 生徒一覧を取得
    students_stmt = select(User).where(
        User.role == RoleEnum.student,
        User.is_active == True,
        User.is_deleted == False
    ).order_by(User.full_name)

    students_result = await db.execute(students_stmt)
    students = students_result.scalars().all()

    progress_data = []

    # 介入判定用の閾値日時（現在から2週間前）
    intervention_threshold = datetime.utcnow() - timedelta(days=INTERVENTION_DAYS_THRESHOLD)

    for student in students:
        # 投稿数と最終投稿日を取得
        posts_stmt = select(
            func.count(Post.id).label("post_count"),
            func.max(Post.created_at).label("last_posted_at"),
            Post.phase_label
        ).where(
            Post.user_id == student.id,
            Post.deleted_at.is_(None)
        ).group_by(Post.phase_label)

        posts_result = await db.execute(posts_stmt)
        posts_data = posts_result.all()

        # 総投稿数
        total_posts = sum(row.post_count for row in posts_data)

        # 最終投稿日（全フェーズ）
        last_posted_at = None
        if posts_data:
            last_posted_stmt = select(func.max(Post.created_at)).where(
                Post.user_id == student.id,
                Post.deleted_at.is_(None)
            )
            last_posted_result = await db.execute(last_posted_stmt)
            last_posted_at = last_posted_result.scalar()

        # 最新のフェーズ
        latest_phase = None
        if posts_data:
            latest_post_stmt = select(Post.phase_label).where(
                Post.user_id == student.id,
                Post.deleted_at.is_(None)
            ).order_by(Post.created_at.desc()).limit(1)
            latest_post_result = await db.execute(latest_post_stmt)
            latest_phase = latest_post_result.scalar()

        # 問いの変更回数をカウント（question_state_change_type が none 以外）
        question_change_stmt = select(func.count(Post.id)).where(
            Post.user_id == student.id,
            Post.deleted_at.is_(None),
            Post.question_state_change_type != QuestionStateChangeType.none
        )
        question_change_result = await db.execute(question_change_stmt)
        question_change_count = question_change_result.scalar() or 0

        # 介入フラグの判定（2週間以上投稿がない場合にTRUE）
        intervention_flag = False
        if last_posted_at is None:
            # 一度も投稿がない場合は介入が必要
            intervention_flag = True
        elif last_posted_at < intervention_threshold:
            # 最終投稿が2週間以上前の場合
            intervention_flag = True

        # フェーズラベルを日本語に変換
        display_phase = "未投稿"
        if latest_phase:
            display_phase = PHASE_LABEL_MAP.get(latest_phase, latest_phase)

        progress_data.append({
            "user_id": student.id,
            "full_name": student.full_name,
            "grade": student.grade,
            "class_name": student.class_name,
            "phase": display_phase,
            "post_count": total_posts,
            "question_change_count": question_change_count,
            "last_posted_at": last_posted_at.isoformat() if last_posted_at else None,
            "intervention_flag": intervention_flag,
        })

    return progress_data


@router.get("/non-cognitive-abilities")
async def get_non_cognitive_abilities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """非認知能力データを取得（生徒ごと）"""
    # 管理者と教師のみアクセス可能
    if current_user.role not in [RoleEnum.admin, RoleEnum.teacher]:
        raise HTTPException(status_code=403, detail="管理者または教師のみアクセス可能です")

    # 生徒一覧を取得
    students_stmt = select(User).where(
        User.role == RoleEnum.student,
        User.is_active == True,
        User.is_deleted == False
    ).order_by(User.full_name)

    students_result = await db.execute(students_stmt)
    students = students_result.scalars().all()

    ability_data = []

    # 全ての能力を取得
    abilities_stmt = select(NonCogAbility).order_by(NonCogAbility.id)
    abilities_result = await db.execute(abilities_stmt)
    all_abilities = abilities_result.scalars().all()

    ability_code_to_id = {ability.code: ability.id for ability in all_abilities}

    for student in students:
        # 投稿数を取得
        posts_stmt = select(func.count(Post.id)).where(
            Post.user_id == student.id,
            Post.deleted_at.is_(None)
        )
        posts_result = await db.execute(posts_stmt)
        post_count = posts_result.scalar() or 0

        # 受け取った感謝の手紙数
        received_letters_stmt = select(func.count(ThanksLetter.id)).where(
            ThanksLetter.receiver_user_id == student.id
        )
        received_letters_result = await db.execute(received_letters_stmt)
        received_letters_count = received_letters_result.scalar() or 0

        # 送った感謝の手紙数（参考情報として）
        sent_letters_stmt = select(func.count(ThanksLetter.id)).where(
            ThanksLetter.sender_user_id == student.id
        )
        sent_letters_result = await db.execute(sent_letters_stmt)
        sent_letters_count = sent_letters_result.scalar() or 0

        # 実際のDBから能力スコアを集計
        # 投稿から選択された能力をカウント
        post_ability_counts = {}
        for ability in all_abilities:
            count_stmt = select(func.count(PostAbilityPoint.id)).select_from(PostAbilityPoint).join(
                Post, PostAbilityPoint.post_id == Post.id
            ).where(
                Post.user_id == student.id,
                Post.deleted_at.is_(None),
                PostAbilityPoint.ability_id == ability.id
            )
            count_result = await db.execute(count_stmt)
            post_ability_counts[ability.code] = count_result.scalar() or 0

        # 受信した感謝の手紙から選択された能力をカウント（受信者の能力として記録）
        letter_ability_counts = {}
        for ability in all_abilities:
            count_stmt = select(func.count(ThanksLetterAbilityPoint.id)).select_from(
                ThanksLetterAbilityPoint
            ).join(
                ThanksLetter, ThanksLetterAbilityPoint.thanks_letter_id == ThanksLetter.id
            ).where(
                ThanksLetter.receiver_user_id == student.id,
                ThanksLetterAbilityPoint.ability_id == ability.id
            )
            count_result = await db.execute(count_stmt)
            letter_ability_counts[ability.code] = count_result.scalar() or 0

        # スコア計算（投稿での選択 + 受信した手紙での選択）
        # 1回選択 = 1点として計算
        abilities_scores = {}
        for ability in all_abilities:
            total_count = post_ability_counts[ability.code] + letter_ability_counts[ability.code]
            score = total_count * 1
            abilities_scores[ability.code] = score

        ability_data.append({
            "user_id": student.id,
            "full_name": student.full_name,
            "grade": student.grade,
            "class_name": student.class_name,
            "post_count": post_count,
            "received_letters_count": received_letters_count,
            "sent_letters_count": sent_letters_count,
            "abilities": abilities_scores
        })

    return ability_data
