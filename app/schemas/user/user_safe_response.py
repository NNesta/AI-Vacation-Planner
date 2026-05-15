from enum import Enum
from pydantic import ConfigDict, Field, EmailStr
from .user_request import BaseUser


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"


class UserSafeResponse(BaseUser):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(min_length=1, max_length=150)
    firstname: str = Field(min_length=1, max_length=150)
    lastname: str = Field(min_length=1, max_length=150)
    role: str = Field(default=UserRole.USER)
    model_config = ConfigDict(from_attributes=True)
