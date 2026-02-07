from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession  # noqa: F401
from app.settings import settings

async_engine = create_async_engine(str(settings.DATABASE_URL), echo=True)
async_session = async_sessionmaker(async_engine)


async def get_async_session():
    async with async_session() as session:
        yield session
