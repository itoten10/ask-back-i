from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.database import get_db
from app.core.security import now_utc
from app.schemas.admin_user import (
    BulkResult,
    LocalUserCreateRequest,
    UserCreateRequest,
    UserDeleteResponse,
    UserListResponse,
    UserUpdateRequest,
)
from app.services import admin_user_service


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    role: str | None = None,
    grade: int | None = None,
    class_name: str | None = None,
    keyword: str | None = None,
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(deps.get_admin_user),  # noqa: B008
):
    items, total = await admin_user_service.list_users(
        db,
        page=page,
        page_size=page_size,
        role=role,
        grade=grade,
        class_name=class_name,
        keyword=keyword,
        include_deleted=include_deleted,
    )
    return UserListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/users", status_code=201, response_model=UserListResponse)
async def create_user(
    payload: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(deps.get_admin_user),  # noqa: B008
):
    user = await admin_user_service.create_user(db, payload)
    return UserListResponse(items=[user], total=1, page=1, page_size=1)


@router.post("/users/local", status_code=201, response_model=UserListResponse)
async def create_local_user(
    payload: LocalUserCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(deps.get_admin_user),  # noqa: B008
):
    user = await admin_user_service.create_local_user(db, payload)
    return UserListResponse(items=[user], total=1, page=1, page_size=1)


@router.put("/users/{user_id}", response_model=UserListResponse)
async def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(deps.get_admin_user),  # noqa: B008
):
    user = await admin_user_service.update_user(db, user_id, payload)
    return UserListResponse(items=[user], total=1, page=1, page_size=1)


@router.delete("/users/{user_id}", response_model=UserDeleteResponse)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(deps.get_admin_user),  # noqa: B008
):
    # 物理削除（DBから完全に削除）
    await admin_user_service.hard_delete_user(db, user_id)
    return UserDeleteResponse(detail="deleted")


@router.post("/users/bulk_import", response_model=BulkResult)
async def bulk_import_users(
    dry_run: bool = Query(True),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(deps.get_admin_user),  # noqa: B008
):
    return await admin_user_service.bulk_import_users(db, file=file, dry_run=dry_run)


@router.post("/users/bulk_delete", response_model=BulkResult)
async def bulk_delete_users(
    dry_run: bool = Query(True),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(deps.get_admin_user),  # noqa: B008
):
    return await admin_user_service.bulk_delete_users(db, file=file, dry_run=dry_run)


@router.get("/users/export")
async def export_users(
    type: str = Query("full", regex="^(full|template)$"),  # noqa: A002
    role: str | None = None,
    grade: int | None = None,
    class_name: str | None = None,
    keyword: str | None = None,
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_db),
    admin_user=Depends(deps.get_admin_user),  # noqa: B008
):
    if type == "template":
        headers = [
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
        content = ",".join(headers) + "\n"
        filename = "users_template.csv"
    else:
        content = await admin_user_service.export_users_csv(
            db,
            role=role,
            grade=grade,
            class_name=class_name,
            keyword=keyword,
            include_deleted=include_deleted,
        )
        timestamp = now_utc().strftime("%Y%m%d_%H%M")
        filename = f"users_{timestamp}.csv"

    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
