from fastapi import APIRouter, Depends

from app.api import deps
from app.schemas.user import UserMe


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMe)
async def get_me(current_user=Depends(deps.get_current_user)):
    return UserMe.model_validate(current_user)
