from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import Annotated
from ..core import settings


engine = create_async_engine(settings.database_url)
async_session_local = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with async_session_local() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]
