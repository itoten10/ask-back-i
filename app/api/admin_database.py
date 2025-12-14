"""管理者用データベース閲覧API"""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.core.database import get_db
from app.models.user import User

router = APIRouter()


@router.get("/tables", response_model=List[str])
async def get_tables(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> List[str]:
    """テーブル一覧を取得"""
    result = await db.execute(text("SHOW TABLES"))
    tables = [row[0] for row in result.fetchall()]
    return tables


@router.get("/tables/{table_name}/schema")
async def get_table_schema(
    table_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> List[Dict[str, Any]]:
    """テーブルのスキーマを取得"""
    # SQLインジェクション対策: テーブル名を検証
    result = await db.execute(text("SHOW TABLES"))
    valid_tables = [row[0] for row in result.fetchall()]

    if table_name not in valid_tables:
        raise HTTPException(status_code=404, detail="Table not found")

    # スキーマ情報を取得
    result = await db.execute(text(f"DESCRIBE {table_name}"))
    columns = []
    for row in result.fetchall():
        columns.append({
            "field": row[0],
            "type": row[1],
            "null": row[2],
            "key": row[3],
            "default": row[4],
            "extra": row[5],
        })
    return columns


@router.get("/tables/{table_name}/data")
async def get_table_data(
    table_name: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> Dict[str, Any]:
    """テーブルのデータを取得"""
    # SQLインジェクション対策: テーブル名を検証
    result = await db.execute(text("SHOW TABLES"))
    valid_tables = [row[0] for row in result.fetchall()]

    if table_name not in valid_tables:
        raise HTTPException(status_code=404, detail="Table not found")

    # データ件数を取得
    count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    total = count_result.scalar()

    # データを取得
    data_result = await db.execute(
        text(f"SELECT * FROM {table_name} LIMIT :limit OFFSET :offset"),
        {"limit": limit, "offset": offset}
    )

    # カラム名を取得
    columns = list(data_result.keys())

    # データを辞書のリストに変換
    rows = []
    for row in data_result.fetchall():
        row_dict = {}
        for i, col in enumerate(columns):
            value = row[i]
            # datetime型をISO文字列に変換
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            row_dict[col] = value
        rows.append(row_dict)

    return {
        "table_name": table_name,
        "total": total,
        "limit": limit,
        "offset": offset,
        "columns": columns,
        "rows": rows,
    }


@router.get("/tables/{table_name}/count")
async def get_table_count(
    table_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> Dict[str, Any]:
    """テーブルのレコード数を取得"""
    # SQLインジェクション対策: テーブル名を検証
    result = await db.execute(text("SHOW TABLES"))
    valid_tables = [row[0] for row in result.fetchall()]

    if table_name not in valid_tables:
        raise HTTPException(status_code=404, detail="Table not found")

    # データ件数を取得
    count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    total = count_result.scalar()

    return {
        "table_name": table_name,
        "count": total,
    }
