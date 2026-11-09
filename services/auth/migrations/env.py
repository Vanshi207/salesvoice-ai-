import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.models import Base

target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name == settings.db_schema
    return True


def run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        include_name=include_name,
        version_table_schema=settings.db_schema,
    )
    with context.begin_transaction():
        context.run_migrations()


async def main():
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        await conn.run_sync(run_migrations)
        await conn.commit()
    await engine.dispose()


asyncio.run(main())
