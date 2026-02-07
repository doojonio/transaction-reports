import asyncio

import pytest
from sqlalchemy.ext.asyncio import async_scoped_session, async_sessionmaker, create_async_engine

from app.db import get_async_session
from app.settings import settings
from main import app

async_engine = create_async_engine(str(settings.DATABASE_URL))
async_session = async_scoped_session(
    async_sessionmaker(async_engine, autocommit=False, autoflush=False, expire_on_commit=False),
    scopefunc=lambda: asyncio.current_task().get_name(),  # type: ignore[union-attr]
)


@pytest.fixture(autouse=True)
async def _override_db(db):
    app.dependency_overrides[get_async_session] = lambda: db


@pytest.fixture()
async def db():
    async with async_session() as session:
        async with session.begin():
            yield session
