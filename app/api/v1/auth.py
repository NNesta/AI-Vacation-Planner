from typing import Annotated, Any
from fastapi import APIRouter, BackgroundTasks, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependancies import CurrentUser
from app.db.session import DbSession
from app.schemas.user.user_safe_response import UserSafeResponse

from ...schemas.auth import auth_request, auth_response
from ...services import auth_services


router = APIRouter()


@router.post(
    "/register",
    response_model=auth_response.RegisterUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    register_data: auth_request.RegisterUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
):
    return await auth_services.create_user(register_data, db, background_tasks)


@router.post("/login", response_model=auth_response.LoginResponse)
async def login(
    login_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession
):
    return await auth_services.token(
        username=login_data.username, password=login_data.password, db=db
    )


@router.get("/me", response_model=UserSafeResponse)
async def me(current_user: CurrentUser):
    return current_user
