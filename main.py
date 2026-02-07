from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.cache import init_cache
from app.db import async_session
from app.routes.report import router as report_router
from app.task.mockfill import mockfill


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    app.state.cache = await init_cache()

    async with async_session() as db:
        await mockfill(db)

    yield
    await app.state.cache.close()


app = FastAPI(lifespan=lifespan)

app.include_router(report_router)


@app.get("/health")
def health():
    return {"health": "ok"}


if __name__ == "__main__":
    from uvicorn import run

    run(app, host="0.0.0.0", port=8000)
