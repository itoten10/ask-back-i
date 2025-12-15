import csv
import io
from datetime import datetime
from typing import Iterable, Optional, Sequence

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, now_utc
from app.models.user import GenderEnum, RoleEnum, User, UserLocalAccount
from app.schemas.admin_user import (
    BulkResult,
    BulkRowResult,
    LocalUserCreateRequest,
    UserCreateRequest,
    UserUpdateRequest,
)


def _parse_role(raw: str) -> RoleEnum:
    try:
        return RoleEnum(raw)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid role") from exc


def _parse_gender(raw: str | None) -> GenderEnum:
    if raw is None:
        return GenderEnum.unknown
    try:
        return GenderEnum(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid gender"
        ) from exc


def _validate_school_person_id(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if len(value) != 6 or not value.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="school_person_id must be 6 digits",
        )
    return value


async def list_users(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    role: Optional[str],
    grade: Optional[int],
    class_name: Optional[str],
    keyword: Optional[str],
    include_deleted: bool,
):
    conditions = []
    if not include_deleted:
        conditions.append(User.is_deleted.is_(False))
    if role:
        try:
            role_enum = RoleEnum(role)
            conditions.append(User.role == role_enum)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid role")
    if grade is not None:
        conditions.append(User.grade == grade)
    if class_name:
        conditions.append(User.class_name == class_name)
    if keyword:
        like_pattern = f"%{keyword}%"
        conditions.append(
            or_(
                User.school_person_id.like(like_pattern),
                User.full_name.like(like_pattern),
                User.email.like(like_pattern),
            )
        )

    where_clause = and_(*conditions) if conditions else None

    total_stmt = select(func.count()).select_from(User)
    if where_clause is not None:
        total_stmt = total_stmt.where(where_clause)
    total = (await db.execute(total_stmt)).scalar_one()

    stmt = select(User)
    if where_clause is not None:
        stmt = stmt.where(where_clause)
    stmt = stmt.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return items, total


async def _check_unique_email(db: AsyncSession, email: str):
    stmt = select(User).where(User.email == email)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email already exists",
        )


async def _check_unique_school_person_id(db: AsyncSession, school_person_id: Optional[str]):
    if not school_person_id:
        return
    stmt = select(User).where(User.school_person_id == school_person_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="school_person_id already exists",
        )


async def _check_unique_login_id(db: AsyncSession, login_id: str):
    stmt = select(UserLocalAccount).where(UserLocalAccount.login_id == login_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="login_id already exists",
        )


async def create_user(db: AsyncSession, payload: UserCreateRequest) -> User:
    role_enum = _parse_role(payload.role)
    gender_enum = _parse_gender(payload.gender)
    school_person_id = _validate_school_person_id(payload.school_person_id)

    if role_enum == RoleEnum.student:
        if payload.grade is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="grade is required for student",
            )
    else:
        payload.grade = None
        payload.class_name = None

    await _check_unique_email(db, payload.email)
    await _check_unique_school_person_id(db, school_person_id)

    user = User(
        role=role_enum,
        full_name=payload.full_name,
        full_name_kana=payload.full_name_kana,
        email=payload.email,
        gender=gender_enum,
        school_person_id=school_person_id,
        date_of_birth=payload.date_of_birth,
        grade=payload.grade,
        class_name=payload.class_name,
        is_active=True,
        is_deleted=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_local_user(db: AsyncSession, payload: LocalUserCreateRequest) -> User:
    role_enum = _parse_role(payload.role)
    gender_enum = _parse_gender(payload.gender)
    school_person_id = _validate_school_person_id(payload.school_person_id)

    # 生徒以外はgrade/class_nameを無効化
    if role_enum != RoleEnum.student:
        payload.grade = None
        payload.class_name = None
    else:
        # 生徒の場合はgradeが必須
        if payload.grade is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="grade is required for student",
            )

    await _check_unique_email(db, payload.email)
    await _check_unique_school_person_id(db, school_person_id)
    await _check_unique_login_id(db, payload.login_id)

    if len(payload.password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="password must be at least 4 characters",
        )

    user = User(
        role=role_enum,
        full_name=payload.full_name,
        full_name_kana=payload.full_name_kana,
        email=payload.email,
        gender=gender_enum,
        school_person_id=school_person_id,
        date_of_birth=payload.date_of_birth,
        grade=payload.grade,
        class_name=payload.class_name,
        is_active=True,
        is_deleted=False,
    )
    db.add(user)
    await db.flush()

    local_account = UserLocalAccount(
        user_id=user.id,
        login_id=payload.login_id,
        password_hash=hash_password(payload.password),
    )
    db.add(local_account)

    await db.commit()
    await db.refresh(user)
    return user


async def soft_delete_user(db: AsyncSession, user_id: int, reason: Optional[str]) -> User:
    """論理削除（後方互換性のため残す）"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    user.is_deleted = True
    user.is_active = False
    user.deleted_at = now_utc()
    user.deleted_reason = reason or "manual delete from admin UI"
    await db.commit()
    await db.refresh(user)
    return user


async def hard_delete_user(db: AsyncSession, user_id: int) -> None:
    """物理削除（DBから完全に削除）"""
    from app.models.post import Post
    from app.models.post_ability_point import PostAbilityPoint
    from app.models.thanks_letter import ThanksLetter
    from app.models.thanks_letter_ability_point import ThanksLetterAbilityPoint
    from app.models.user import UserSession, UserGoogleAccount

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    # 関連データを先に削除
    # 0-1. セッションを削除
    sessions_stmt = select(UserSession).where(UserSession.user_id == user_id)
    sessions_result = await db.execute(sessions_stmt)
    for session in sessions_result.scalars().all():
        await db.delete(session)

    # 0-2. Googleアカウント情報を削除
    google_account_stmt = select(UserGoogleAccount).where(UserGoogleAccount.user_id == user_id)
    google_account_result = await db.execute(google_account_stmt)
    google_account = google_account_result.scalar_one_or_none()
    if google_account:
        await db.delete(google_account)

    # 1. 投稿に紐づく能力ポイントを削除
    posts_stmt = select(Post.id).where(Post.user_id == user_id)
    posts_result = await db.execute(posts_stmt)
    post_ids = [row[0] for row in posts_result.all()]

    if post_ids:
        for post_id in post_ids:
            ability_points_stmt = select(PostAbilityPoint).where(PostAbilityPoint.post_id == post_id)
            ability_points_result = await db.execute(ability_points_stmt)
            for point in ability_points_result.scalars().all():
                await db.delete(point)

        # 投稿を削除
        for post_id in post_ids:
            post = await db.get(Post, post_id)
            if post:
                await db.delete(post)

    # 2. 感謝の手紙に紐づく能力ポイントを削除（送信・受信両方）
    sent_letters_stmt = select(ThanksLetter.id).where(ThanksLetter.sender_user_id == user_id)
    sent_result = await db.execute(sent_letters_stmt)
    sent_letter_ids = [row[0] for row in sent_result.all()]

    received_letters_stmt = select(ThanksLetter.id).where(ThanksLetter.receiver_user_id == user_id)
    received_result = await db.execute(received_letters_stmt)
    received_letter_ids = [row[0] for row in received_result.all()]

    all_letter_ids = list(set(sent_letter_ids + received_letter_ids))

    if all_letter_ids:
        for letter_id in all_letter_ids:
            ability_points_stmt = select(ThanksLetterAbilityPoint).where(
                ThanksLetterAbilityPoint.thanks_letter_id == letter_id
            )
            ability_points_result = await db.execute(ability_points_stmt)
            for point in ability_points_result.scalars().all():
                await db.delete(point)

        # 感謝の手紙を削除
        for letter_id in all_letter_ids:
            letter = await db.get(ThanksLetter, letter_id)
            if letter:
                await db.delete(letter)

    # 3. ローカルアカウントを削除
    local_account_stmt = select(UserLocalAccount).where(UserLocalAccount.user_id == user_id)
    local_account_result = await db.execute(local_account_stmt)
    local_account = local_account_result.scalar_one_or_none()
    if local_account:
        await db.delete(local_account)

    # 4. ユーザーを削除
    await db.delete(user)
    await db.commit()


async def update_user(db: AsyncSession, user_id: int, payload: UserUpdateRequest) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    role_enum = _parse_role(payload.role)
    gender_enum = _parse_gender(payload.gender)
    school_person_id = _validate_school_person_id(payload.school_person_id)

    # Check email uniqueness (exclude current user)
    if payload.email != user.email:
        stmt = select(User).where(User.email == payload.email, User.id != user_id)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="email already exists",
            )

    # Check school_person_id uniqueness (exclude current user)
    if school_person_id and school_person_id != user.school_person_id:
        stmt = select(User).where(User.school_person_id == school_person_id, User.id != user_id)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="school_person_id already exists",
            )

    # Validate student requires grade
    if role_enum == RoleEnum.student and payload.grade is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="grade is required for student",
        )

    # Clear grade/class for non-students
    grade = payload.grade if role_enum == RoleEnum.student else None
    class_name = payload.class_name if role_enum == RoleEnum.student else None

    user.full_name = payload.full_name
    user.full_name_kana = payload.full_name_kana
    user.email = payload.email
    user.role = role_enum
    user.gender = gender_enum
    user.school_person_id = school_person_id
    user.date_of_birth = payload.date_of_birth
    user.grade = grade
    user.class_name = class_name
    user.is_active = payload.is_active

    await db.commit()
    await db.refresh(user)
    return user


def _normalize_string(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _load_csv(file_content: bytes) -> tuple[list[dict], list[str]]:
    decoded = file_content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))
    headers = reader.fieldnames or []
    rows: list[dict] = []
    for row in reader:
        rows.append({k: v for k, v in row.items()})
    return rows, headers


def _validate_import_row(row: dict, line_number: int) -> tuple[Optional[UserCreateRequest], list[str]]:
    errors: list[str] = []
    role = _normalize_string(row.get("role"))
    school_person_id = _normalize_string(row.get("school_person_id"))
    full_name = _normalize_string(row.get("full_name"))
    full_name_kana = _normalize_string(row.get("full_name_kana"))
    date_of_birth = _normalize_string(row.get("date_of_birth"))
    email = _normalize_string(row.get("email"))
    grade = _normalize_string(row.get("grade"))
    class_name = _normalize_string(row.get("class_name"))
    gender = _normalize_string(row.get("gender"))

    if not role:
        errors.append("role is required")
    if not full_name:
        errors.append("full_name is required")
    if not email:
        errors.append("email is required")

    parsed_grade = None
    if grade:
        if grade.isdigit():
            parsed_grade = int(grade)
        else:
            errors.append("grade must be numeric")

    parsed_date = None
    if date_of_birth:
        try:
            parsed_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        except ValueError:
            errors.append("date_of_birth must be YYYY-MM-DD")

    if role == "student" and not grade:
        errors.append("grade is required for student")

    if errors:
        return None, errors

    try:
        payload = UserCreateRequest(
            role=role,
            school_person_id=school_person_id,
            full_name=full_name,
            full_name_kana=full_name_kana,
            date_of_birth=parsed_date,
            email=email,
            grade=parsed_grade,
            class_name=class_name,
            gender=gender or "unknown",
        )
    except Exception as exc:  # pylint: disable=broad-except
        return None, [str(exc)]

    return payload, []


async def bulk_import_users(
    db: AsyncSession, *, file: UploadFile, dry_run: bool
) -> BulkResult:
    content = await file.read()
    rows, headers = _load_csv(content)
    required_headers = [
        "role",
        "school_person_id",
        "full_name",
        "full_name_kana",
        "date_of_birth",
        "email",
        "grade",
        "class_name",
        "gender",
    ]
    if not all(col in headers for col in required_headers):
        missing = [col for col in required_headers if col not in headers]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"missing headers: {', '.join(missing)}",
        )

    row_results: list[BulkRowResult] = []
    payload_rows: list[tuple[int, UserCreateRequest]] = []
    email_seen: dict[str, int] = {}
    school_id_seen: dict[str, int] = {}

    for idx, row in enumerate(rows, start=2):
        payload, errs = _validate_import_row(row, idx)
        if payload:
            if payload.email in email_seen:
                errs.append(f"email duplicated in csv (line {email_seen[payload.email]})")
            else:
                email_seen[payload.email] = idx
            if payload.school_person_id:
                if payload.school_person_id in school_id_seen:
                    errs.append(
                        f"school_person_id duplicated in csv (line {school_id_seen[payload.school_person_id]})"
                    )
                else:
                    school_id_seen[payload.school_person_id] = idx
        if errs:
            row_results.append(BulkRowResult(line_number=idx, status="error", message="; ".join(errs)))
        else:
            payload_rows.append((idx, payload))  # type: ignore[arg-type]
            row_results.append(BulkRowResult(line_number=idx, status="ok", message=None))

    # DB level duplicate checks
    if payload_rows:
        emails = {p.email for _, p in payload_rows}
        stmt_email = select(User.email).where(User.email.in_(emails))
        existing_emails = {row[0] for row in (await db.execute(stmt_email)).all()}

        school_ids = {p.school_person_id for _, p in payload_rows if p.school_person_id}
        if school_ids:
            stmt_sid = select(User.school_person_id).where(User.school_person_id.in_(school_ids))
            existing_sids = {row[0] for row in (await db.execute(stmt_sid)).all()}
        else:
            existing_sids = set()

        line_to_index = {r.line_number: i for i, r in enumerate(row_results)}

        for line_no, payload in payload_rows:
            errs = []
            if payload.email in existing_emails:
                errs.append("email already exists")
            if payload.school_person_id and payload.school_person_id in existing_sids:
                errs.append("school_person_id already exists")
            if errs:
                row_results[line_to_index[line_no]] = BulkRowResult(
                    line_number=line_no,
                    status="error",
                    message="; ".join(errs),
                )

    success_rows = [r for r in row_results if r.status == "ok"]
    error_rows = [r for r in row_results if r.status == "error"]

    if not dry_run and success_rows:
        for line_no, payload in payload_rows:
            # skip rows that turned into errors after DB duplicate check
            if row_results[line_to_index[line_no]].status == "error":
                continue
            role_enum = _parse_role(payload.role)
            gender_enum = _parse_gender(payload.gender)
            if role_enum != RoleEnum.student:
                payload.grade = None
                payload.class_name = None
            user = User(
                role=role_enum,
                full_name=payload.full_name,
                full_name_kana=payload.full_name_kana,
                email=payload.email,
                gender=gender_enum,
                school_person_id=_validate_school_person_id(payload.school_person_id),
                date_of_birth=payload.date_of_birth,
                grade=payload.grade,
                class_name=payload.class_name,
                is_active=True,
                is_deleted=False,
            )
            db.add(user)
        await db.commit()

    return BulkResult(
        total=len(row_results),
        success=len(success_rows),
        errors=len(error_rows),
        rows=row_results,
    )


async def bulk_delete_users(
    db: AsyncSession, *, file: UploadFile, dry_run: bool
) -> BulkResult:
    content = await file.read()
    rows, headers = _load_csv(content)
    required_headers = ["school_person_id", "email", "reason"]
    if not all(col in headers for col in required_headers):
        missing = [col for col in required_headers if col not in headers]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"missing headers: {', '.join(missing)}",
        )

    row_results: list[BulkRowResult] = []
    targets: list[tuple[int, Optional[str]]] = []

    for idx, row in enumerate(rows, start=2):
        sid = _normalize_string(row.get("school_person_id"))
        email = _normalize_string(row.get("email"))
        reason = _normalize_string(row.get("reason"))
        errs: list[str] = []
        if not sid or len(sid) != 6 or not sid.isdigit():
            errs.append("school_person_id must be 6 digits")
        if errs:
            row_results.append(BulkRowResult(line_number=idx, status="error", message="; ".join(errs)))
            continue
        stmt = select(User).where(User.school_person_id == sid)
        user = (await db.execute(stmt)).scalar_one_or_none()
        if not user:
            row_results.append(
                BulkRowResult(line_number=idx, status="error", message="user not found")
            )
            continue
        if email and user.email != email:
            row_results.append(
                BulkRowResult(line_number=idx, status="error", message="email mismatch")
            )
            continue
        targets.append((user.id, reason))
        row_results.append(BulkRowResult(line_number=idx, status="ok", message=None))

    success_rows = [r for r in row_results if r.status == "ok"]
    error_rows = [r for r in row_results if r.status == "error"]

    if not dry_run and targets:
        for user_id, reason in targets:
            await soft_delete_user(db, user_id, reason)

    return BulkResult(
        total=len(row_results),
        success=len(success_rows),
        errors=len(error_rows),
        rows=row_results,
    )


async def export_users_csv(
    db: AsyncSession,
    *,
    role: Optional[str],
    grade: Optional[int],
    class_name: Optional[str],
    keyword: Optional[str],
    include_deleted: bool,
) -> str:
    items, _ = await list_users(
        db,
        page=1,
        page_size=10_000_000,
        role=role,
        grade=grade,
        class_name=class_name,
        keyword=keyword,
        include_deleted=include_deleted,
    )
    headers = [
        "id",
        "school_person_id",
        "role",
        "full_name",
        "full_name_kana",
        "date_of_birth",
        "email",
        "grade",
        "class_name",
        "gender",
        "is_active",
        "is_deleted",
        "deleted_at",
        "deleted_reason",
        "created_at",
        "updated_at",
    ]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for user in items:
        writer.writerow(
            [
                user.id,
                user.school_person_id or "",
                user.role.value,
                user.full_name,
                user.full_name_kana or "",
                user.date_of_birth.isoformat() if user.date_of_birth else "",
                user.email,
                user.grade if user.grade is not None else "",
                user.class_name or "",
                user.gender.value,
                "1" if user.is_active else "0",
                "1" if user.is_deleted else "0",
                user.deleted_at.isoformat() if user.deleted_at else "",
                user.deleted_reason or "",
                user.created_at.isoformat(),
                user.updated_at.isoformat(),
            ]
        )
    return output.getvalue()
