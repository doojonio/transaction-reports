from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.cache import init_cache
from app.db import async_session
from app.routes.report import router as report_router
from app.settings import settings
from app.task.mockfill import mockfill


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown events.

    This async context manager is used by FastAPI as the application's
    lifespan handler.

    On startup, it:
    1. Initializes the Redis cache connection and stores it in the app state.
    2. If the `MOCKFILL` setting is True, it seeds the database with mock data.

    On shutdown, it:
    1. Gracefully closes the Redis cache connection.

    Args:
        app: The FastAPI application instance.
    """
    app.state.cache = await init_cache()

    if settings.MOCKFILL:
        async with async_session() as db:
            await mockfill(db)

    yield
    await app.state.cache.close()


app = FastAPI(lifespan=lifespan)

app.include_router(report_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"health": "ok"}


if __name__ == "__main__":
    from uvicorn import run

    run(app, host="0.0.0.0", port=8000)
