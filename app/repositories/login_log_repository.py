from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuthTypeEnum, LoginLog


async def create_login_log(
    db: AsyncSession,
    *,
    user_id: int | None,
    auth_type: AuthTypeEnum,
    success: bool,
    failure_reason: str | None,
    ip_address: str | None,
    user_agent: str | None,
    device_info: str | None = None,
    login_at: datetime,
) -> LoginLog:
    log = LoginLog(
        user_id=user_id,
        login_at=login_at,
        auth_type=auth_type,
        success=1 if success else 0,
        failure_reason=failure_reason,
        ip_address=ip_address,
        user_agent=user_agent,
        device_info=device_info,
    )
    db.add(log)
    await db.flush()
    return log
