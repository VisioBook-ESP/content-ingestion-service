from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.api import api_router
from src.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(  # type: ignore[call-arg, arg-type]
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=settings.CORS_ORIGINS,  # type: ignore[arg-type]
    allow_credentials=True,  # type: ignore[arg-type]
    allow_methods=["*"],  # type: ignore[arg-type]
    allow_headers=["*"],  # type: ignore[arg-type]
)

app.include_router(api_router, prefix=settings.API_PREFIX)
