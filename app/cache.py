import redis.asyncio as redis
from fastapi import Request

from app.settings import settings

Cache = redis.Redis


async def init_cache():
    return await redis.from_url(str(settings.REDIS_URL), decode_responses=True)


def get_cache(request: Request):
    return request.app.state.cache
