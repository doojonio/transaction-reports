import redis.asyncio as redis
from fastapi import Request

from app.settings import settings

Cache = redis.Redis


async def init_cache() -> Cache:
    return await redis.from_url(str(settings.REDIS_URL), decode_responses=True)  # type: ignore[no-any-return,no-untyped-call]


def get_cache(request: Request) -> Cache:
    return request.app.state.cache  # type: ignore[no-any-return]
