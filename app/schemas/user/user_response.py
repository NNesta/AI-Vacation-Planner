from typing import List
from ..trip.trip_safe_response import TripSafeResponse
from ..user.user_safe_response import UserSafeResponse


class UserResponse(UserSafeResponse):
    trips: List[TripSafeResponse]
    created_trips: List[TripSafeResponse]
