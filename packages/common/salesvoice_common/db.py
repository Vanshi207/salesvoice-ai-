from collections.abc import AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


def make_base(schema: str) -> type[DeclarativeBase]:
    """Every table defined on this Base lives in `schema` (e.g. auth.users)."""
    class Base(DeclarativeBase):
        metadata = MetaData(schema=schema)
    return Base


class Database:
    def __init__(self, url: str):
        self.engine = create_async_engine(url, pool_size=5, max_overflow=5, pool_pre_ping=True)
        self.sessionmaker = async_sessionmaker(self.engine, expire_on_commit=False)

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.sessionmaker() as s:
            yield s

    async def dispose(self) -> None:
        await self.engine.dispose()
