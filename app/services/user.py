from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.user import User


async def get_users(db: AsyncSession):
    stmt = (
        select(User)
        .options(selectinload(User.user_trips))
        .options(selectinload(User.created_trips))
    )
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users
