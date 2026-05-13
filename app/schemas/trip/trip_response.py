from typing import List, Optional
from app.schemas.user.user_response import UserSafeResponse
from .trip_safe_response import TripSafeResponse


class TripResponse(TripSafeResponse):
    users: List[UserSafeResponse]
