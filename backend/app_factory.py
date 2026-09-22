from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.services.model.model_service import get_model
from backend.services.scheduler_service import scheduler, setup_jobs

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    model, tokenizer = get_model()
    inputs = tokenizer("warmup", return_tensors="pt").to(model.device)
    model.generate(**inputs, max_new_tokens=1)

    setup_jobs()
    scheduler.start()

    yield
    scheduler.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title="Pickle Bot Backend", lifespan=lifespan, version=settings.version)

    if settings.is_dev:
        origins = ["*"]
    else:
        origins = settings.allowed_origins.split(",") if settings.allowed_origins else []

    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
