from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from ...db.session import DbSession
from ...features.auth.schemas import RegisterUser
from ...entities import User
from pwdlib import PasswordHash

hash_password = PasswordHash.recommended()


async def create_user(register_data: RegisterUser, db: DbSession):
    # 1. check if the username is not taken
    result = await db.execute(
        select(User).where(func.lower(User.username) == register_data.username.lower())
    )
    user_exists = result.scalar_one_or_none()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already taken"
        )
    # 2. check if the email is not taken
    result = await db.execute(
        select(User).where(func.lower(User.email) == register_data.email.lower())
    )
    user_exists = result.scalar_one_or_none()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )
    # 3. add the user and commit
    new_user = User(
        username=register_data.username,
        email=register_data.email,
        firstname=register_data.firstname,
        lastname=register_data.lastname,
        password_hash=hash_password.hash(register_data.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def token(login_data: OAuth2PasswordRequestForm, db: AsyncSession):
    return "Not yet implemented"
