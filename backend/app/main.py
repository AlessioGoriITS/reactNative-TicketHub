from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="REST API for the TicketHub customer support platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Report that the API process is running."""

    return {"status": "ok", "service": "backend"}


@app.get("/api/health", tags=["system"])
def api_health_check() -> dict[str, str]:
    """Health endpoint scoped under the future API prefix."""

    return health_check()
