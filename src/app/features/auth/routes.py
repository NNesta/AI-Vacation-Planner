from typing import Any
from fastapi import APIRouter, status
from fastapi.security import OAuth2PasswordRequestForm
from ...db.session import DbSession
from .schemas import RegisterUser, RegisterUserResponse
from ...features.auth import services

router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(register_data: RegisterUser, db: DbSession):
    return await services.create_user(register_data, db)


@router.post("/login", response_model=Any)
async def login(login_data: OAuth2PasswordRequestForm, db: DbSession):
    return await services.token(login_data, db)
