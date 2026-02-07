from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.cache import init_cache

from app.routes.report import router as report_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await init_cache()
    yield
    await app.state.redis.close()


app = FastAPI(lifespan=lifespan)

app.include_router(report_router)


@app.get("/health")
def health():
    return {"health": "ok"}


if __name__ == "__main__":
    from uvicorn import run

    run(app, host="0.0.0.0", port=8000)
