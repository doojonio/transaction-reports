import asyncio

import pytest
from sqlalchemy.ext.asyncio import async_scoped_session, async_sessionmaker, create_async_engine

from app.db import get_async_session
from app.settings import settings
from main import app
from tests.base_factory import BaseFactory


@pytest.fixture(autouse=True)
async def _override_db(db):
    app.dependency_overrides[get_async_session] = lambda: db


@pytest.fixture(autouse=True)
async def _set_factory_session(db):
    BaseFactory._meta.sqlalchemy_session = db
    yield
    BaseFactory._meta.sqlalchemy_session = None


@pytest.fixture(scope="session")
def engine():
    return create_async_engine(str(settings.DATABASE_URL))


@pytest.fixture()
async def db(engine):
    async_session = async_scoped_session(
        async_sessionmaker(engine, autocommit=False, autoflush=False, expire_on_commit=False),
        scopefunc=lambda: asyncio.current_task().get_name(),  # type: ignore[union-attr]
    )
    async with async_session() as session:
        async with session.begin() as tr:
            try:
                yield session
            finally:
                await tr.rollback()
