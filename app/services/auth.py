from datetime import UTC, timedelta, datetime
from fastapi import HTTPException, status, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from pwdlib import PasswordHash
import jwt
from app.core.config import settings
from app.models.user import User
from ..schemas.auth import auth_request

hash_password = PasswordHash.recommended()


async def create_user(register_data: auth_request.RegisterUser, db: AsyncSession):
    # 1. check if the username is not taken
    result = await db.execute(
        select(User).where(func.lower(User.username) == register_data.username.lower())
    )
    user_exists = result.scalar_one_or_none()
    print(user_exists)
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


def verify_password(password: str, hash: str) -> bool:
    return hash_password.verify(password=password, hash=hash)


def create_token(payload: dict, expires_delta: timedelta | None = None):
    to_encode = payload.copy()

    if expires_delta is None:
        expires = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expires_minutes
        )
    else:
        expires = datetime.now(UTC) + expires_delta
    to_encode.update({"exp": expires})
    return jwt.encode(
        to_encode,
        key=settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


def verify_token(access_token: str) -> str | None:
    try:
        payload = jwt.decode(
            access_token,
            key=settings.secret_key.get_secret_value(),
            algorithms=settings.algorithm,
        )
    except jwt.InvalidTokenError:
        return None
    else:

        return payload.get("sub")


async def token(username: str, password: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password=password, hash=user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    access_token = create_token({"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}
