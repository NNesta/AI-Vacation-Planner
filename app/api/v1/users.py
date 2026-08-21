from typing import List
from fastapi import APIRouter

from app.db.session import DbSession
from ...schemas.user import user_response
from ...services import user_services


router = APIRouter()


@router.get("/", response_model=List[user_response.UserResponse])
async def get_users(db: DbSession):
    return await user_services.get_users(db)
