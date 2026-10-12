from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db import init_db
from app.routers import assessments


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Aharya",
    description="Lab reports in, a personalised Indian meal plan and grocery list out.",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(assessments.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "llm": "claude" if settings.use_llm else "offline"}
