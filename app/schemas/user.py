from datetime import date

from pydantic import BaseModel, EmailStr


class UserMe(BaseModel):
    id: int
    full_name: str
    full_name_kana: str | None
    email: EmailStr
    role: str
    school_person_id: str | None
    grade: int | None
    class_name: str | None
    gender: str
    date_of_birth: date | None

    class Config:
        from_attributes = True
