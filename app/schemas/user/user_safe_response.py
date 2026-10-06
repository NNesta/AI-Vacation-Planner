from pydantic import BaseModel, ConfigDict, Field, EmailStr
from app.enums.user_role_enum import UserRole
from uuid import UUID


class UserSafeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(min_length=1, max_length=150)
    firstname: str = Field(min_length=1, max_length=150)
    lastname: str = Field(min_length=1, max_length=150)
    role: UserRole = Field(default=UserRole.USER)
