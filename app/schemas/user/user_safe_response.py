from pydantic import ConfigDict
from .user_request import BaseUser


class UserSafeResponse(BaseUser):
    model_config = ConfigDict(from_attributes=True)
