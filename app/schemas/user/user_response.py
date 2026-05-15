from typing import List

from app.enums.user_role_enum import UserRole
from ..trip.trip_safe_response import TripSafeResponse
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr


class UserResponse(BaseModel):
    id: UUID
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(min_length=1, max_length=150)
    firstname: str = Field(min_length=1, max_length=150)
    lastname: str = Field(min_length=1, max_length=150)
    role: UserRole = Field(default=UserRole.USER)

    trips: List[TripSafeResponse]
    created_trips: List[TripSafeResponse]
