from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.users import User


async def get_users(db: AsyncSession):
    result = await db.execute(select(User).options(selectinload(User.trips)))
    users = result.scalars().all()
    return users
