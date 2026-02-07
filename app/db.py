from sqlalchemy.ext.asyncio import (  # noqa: F401
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.settings import settings

async_engine = create_async_engine(str(settings.DATABASE_URL), echo=True)
async_session = async_sessionmaker(async_engine)


async def get_async_session():
    async with async_session() as session:
        yield session
