"""投稿API"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.post import Post
from app.models.post_ability_point import PostAbilityPoint
from app.models.post_like import PostLike
from app.models.non_cog_ability import NonCogAbility
from app.models.user import User, RoleEnum
from app.schemas.post import PostCreate, PostUpdate, PostResponse, PostListResponse


router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PostListResponse)
async def get_posts(
    skip: int = 0,
    limit: int = 20,
    user_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """投稿一覧を取得（新しい順）。user_idを指定すると特定ユーザーの投稿のみ取得"""
    # 投稿とユーザー情報を結合して取得
    stmt = (
        select(Post)
        .options(joinedload(Post.user))
        .where(Post.deleted_at.is_(None))
    )

    # user_idが指定されている場合はフィルタリング
    if user_id is not None:
        stmt = stmt.where(Post.user_id == user_id)

    stmt = stmt.order_by(Post.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(stmt)
    posts = result.scalars().unique().all()

    # 総数を取得
    count_stmt = select(Post).where(Post.deleted_at.is_(None))
    if user_id is not None:
        count_stmt = count_stmt.where(Post.user_id == user_id)
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    # 各投稿のいいね数を取得
    post_ids = [post.id for post in posts]
    like_counts = {}
    if post_ids:
        like_count_stmt = (
            select(PostLike.post_id, func.count(PostLike.id).label("count"))
            .where(PostLike.post_id.in_(post_ids))
            .group_by(PostLike.post_id)
        )
        like_count_result = await db.execute(like_count_stmt)
        like_counts = {row.post_id: row.count for row in like_count_result}

    # ログインユーザーがいいねした投稿を取得
    user_likes = set()
    if current_user and post_ids:
        user_likes_stmt = select(PostLike.post_id).where(
            PostLike.post_id.in_(post_ids),
            PostLike.user_id == current_user.id
        )
        user_likes_result = await db.execute(user_likes_stmt)
        user_likes = {row.post_id for row in user_likes_result}

    # レスポンス用にユーザー名とアバターURLを追加
    post_responses = []
    for post in posts:
        post_dict = {
            "id": post.id,
            "user_id": post.user_id,
            "problem": post.problem,
            "content_1": post.content_1,
            "content_2": post.content_2,
            "content_3": post.content_3,
            "question_state_change_type": post.question_state_change_type,
            "phase_label": post.phase_label,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "user_name": post.user.full_name if post.user else None,
            "user_avatar_url": post.user.avatar_url if post.user else None,
            "like_count": like_counts.get(post.id, 0),
            "liked_by_me": post.id in user_likes,
        }
        post_responses.append(PostResponse(**post_dict))

    return PostListResponse(posts=post_responses, total=total)


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """投稿を作成（生徒・教師のみ）"""
    user = current_user

    # 管理者は投稿できない
    if user.role == RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrators cannot create posts"
        )

    # 投稿を作成
    now = datetime.utcnow()
    new_post = Post(
        user_id=user.id,
        problem=post_data.problem,
        content_1=post_data.content_1,
        content_2=post_data.content_2,
        content_3=post_data.content_3,
        question_state_change_type=post_data.question_state_change_type,
        phase_label=post_data.phase_label,
        created_at=now,
        updated_at=now,
    )

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)

    # 非認知能力の関連を保存
    if post_data.ability_codes:
        # ability_codesからability_idを取得
        abilities_stmt = select(NonCogAbility).where(NonCogAbility.code.in_(post_data.ability_codes))
        abilities_result = await db.execute(abilities_stmt)
        abilities = abilities_result.scalars().all()

        # PostAbilityPointを作成
        for ability in abilities:
            post_ability_point = PostAbilityPoint(
                post_id=new_post.id,
                ability_id=ability.id
            )
            db.add(post_ability_point)

        await db.commit()

    # ユーザー情報を取得
    await db.refresh(new_post, ["user"])

    return PostResponse(
        id=new_post.id,
        user_id=new_post.user_id,
        problem=new_post.problem,
        content_1=new_post.content_1,
        content_2=new_post.content_2,
        content_3=new_post.content_3,
        question_state_change_type=new_post.question_state_change_type,
        phase_label=new_post.phase_label,
        created_at=new_post.created_at,
        updated_at=new_post.updated_at,
        user_name=new_post.user.full_name if new_post.user else None,
        user_avatar_url=new_post.user.avatar_url if new_post.user else None,
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
):
    """投稿詳細を取得"""
    stmt = select(Post).options(joinedload(Post.user)).where(Post.id == post_id, Post.deleted_at.is_(None))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    return PostResponse(
        id=post.id,
        user_id=post.user_id,
        problem=post.problem,
        content_1=post.content_1,
        content_2=post.content_2,
        content_3=post.content_3,
        question_state_change_type=post.question_state_change_type,
        phase_label=post.phase_label,
        created_at=post.created_at,
        updated_at=post.updated_at,
        user_name=post.user.full_name if post.user else None,
        user_avatar_url=post.user.avatar_url if post.user else None,
    )


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """投稿を更新（投稿者本人のみ）"""
    # 投稿を取得
    stmt = select(Post).where(Post.id == post_id, Post.deleted_at.is_(None))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # 投稿者本人のみ更新可能
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own posts"
        )

    # 投稿内容を更新
    post.problem = post_data.problem
    post.content_1 = post_data.content_1
    post.content_2 = post_data.content_2
    post.content_3 = post_data.content_3
    post.question_state_change_type = post_data.question_state_change_type
    post.phase_label = post_data.phase_label
    post.updated_at = datetime.utcnow()

    # 既存の能力関連を削除
    delete_stmt = select(PostAbilityPoint).where(PostAbilityPoint.post_id == post_id)
    delete_result = await db.execute(delete_stmt)
    existing_points = delete_result.scalars().all()
    for point in existing_points:
        await db.delete(point)

    await db.commit()

    # 新しい能力関連を保存
    if post_data.ability_codes:
        abilities_stmt = select(NonCogAbility).where(NonCogAbility.code.in_(post_data.ability_codes))
        abilities_result = await db.execute(abilities_stmt)
        abilities = abilities_result.scalars().all()

        for ability in abilities:
            post_ability_point = PostAbilityPoint(
                post_id=post.id,
                ability_id=ability.id
            )
            db.add(post_ability_point)

    await db.commit()
    await db.refresh(post, ["user"])

    return PostResponse(
        id=post.id,
        user_id=post.user_id,
        problem=post.problem,
        content_1=post.content_1,
        content_2=post.content_2,
        content_3=post.content_3,
        question_state_change_type=post.question_state_change_type,
        phase_label=post.phase_label,
        created_at=post.created_at,
        updated_at=post.updated_at,
        user_name=post.user.full_name if post.user else None,
        user_avatar_url=post.user.avatar_url if post.user else None,
    )


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """投稿を削除（論理削除、投稿者本人または管理者のみ）"""
    # 投稿を取得
    stmt = select(Post).where(Post.id == post_id, Post.deleted_at.is_(None))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # 投稿者本人または管理者のみ削除可能
    if post.user_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own posts"
        )

    # 論理削除
    post.deleted_at = datetime.utcnow()
    await db.commit()

    return None


@router.post("/{post_id}/like", status_code=status.HTTP_201_CREATED)
async def like_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """投稿にいいねする"""
    # 投稿を取得
    stmt = select(Post).where(Post.id == post_id, Post.deleted_at.is_(None))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # 既にいいねしているか確認
    existing_like_stmt = select(PostLike).where(
        PostLike.post_id == post_id,
        PostLike.user_id == current_user.id
    )
    existing_like_result = await db.execute(existing_like_stmt)
    existing_like = existing_like_result.scalar_one_or_none()

    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already liked this post"
        )

    # いいねを作成
    new_like = PostLike(
        post_id=post_id,
        user_id=current_user.id,
        created_at=datetime.utcnow()
    )
    db.add(new_like)
    await db.commit()

    # いいね数を取得
    like_count_stmt = select(func.count(PostLike.id)).where(PostLike.post_id == post_id)
    like_count_result = await db.execute(like_count_stmt)
    like_count = like_count_result.scalar()

    return {"post_id": post_id, "like_count": like_count, "liked_by_me": True}


@router.delete("/{post_id}/like", status_code=status.HTTP_200_OK)
async def unlike_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """投稿のいいねを取り消す"""
    # 投稿を取得
    stmt = select(Post).where(Post.id == post_id, Post.deleted_at.is_(None))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # いいねを取得
    like_stmt = select(PostLike).where(
        PostLike.post_id == post_id,
        PostLike.user_id == current_user.id
    )
    like_result = await db.execute(like_stmt)
    like = like_result.scalar_one_or_none()

    if not like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You haven't liked this post"
        )

    # いいねを削除
    await db.delete(like)
    await db.commit()

    # いいね数を取得
    like_count_stmt = select(func.count(PostLike.id)).where(PostLike.post_id == post_id)
    like_count_result = await db.execute(like_count_stmt)
    like_count = like_count_result.scalar()

    return {"post_id": post_id, "like_count": like_count, "liked_by_me": False}
