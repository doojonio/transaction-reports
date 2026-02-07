from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.db import AsyncSession, get_async_session
from app.cache import Cache, get_cache

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/")
async def get_report(
    db: AsyncSession = Depends(get_async_session), redis: Cache = Depends(get_cache)
):
    test_db = await db.execute(select(999))
    await redis.set("test", "123")
    test_redis = await redis.get("test")
    return {
        "test_db": test_db.scalar(),
        "test_redis": test_redis,
    }
