from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserCreateRequest(BaseModel):
    role: str = Field(..., description="student / teacher / admin")
    full_name: str
    full_name_kana: Optional[str] = None
    email: EmailStr
    gender: str = "unknown"
    school_person_id: Optional[str] = Field(
        default=None, min_length=6, max_length=6, description="6-digit string"
    )
    date_of_birth: Optional[date] = None
    grade: Optional[int] = None
    class_name: Optional[str] = None

    @validator("school_person_id")
    def validate_school_person_id(cls, v):
        if v is None:
            return v
        if len(v) != 6 or not v.isdigit():
            raise ValueError("school_person_id must be 6 digits")
        return v


class LocalUserCreateRequest(UserCreateRequest):
    login_id: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=4)


class UserUpdateRequest(BaseModel):
    full_name: str
    full_name_kana: Optional[str] = None
    email: EmailStr
    role: str = Field(..., description="student / teacher / admin")
    gender: str = "unknown"
    school_person_id: Optional[str] = Field(
        default=None, min_length=6, max_length=6, description="6-digit string"
    )
    date_of_birth: Optional[date] = None
    grade: Optional[int] = None
    class_name: Optional[str] = None
    is_active: bool = True

    @validator("school_person_id")
    def validate_school_person_id(cls, v):
        if v is None:
            return v
        if len(v) != 6 or not v.isdigit():
            raise ValueError("school_person_id must be 6 digits")
        return v


class UserListItem(BaseModel):
    id: int
    school_person_id: Optional[str]
    role: str
    full_name: str
    full_name_kana: Optional[str]
    date_of_birth: Optional[date]
    email: EmailStr
    grade: Optional[int]
    class_name: Optional[str]
    gender: str
    is_active: bool
    is_deleted: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: list[UserListItem]
    total: int
    page: int
    page_size: int


class UserDeleteResponse(BaseModel):
    detail: str


class BulkRowResult(BaseModel):
    line_number: int
    status: Literal["ok", "error"]
    message: Optional[str] = None


class BulkResult(BaseModel):
    total: int
    success: int
    errors: int
    rows: list[BulkRowResult]
