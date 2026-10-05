from fastapi import APIRouter

from app.api.routes import ai, auth, categories, tickets

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(categories.router)
api_router.include_router(tickets.router)
api_router.include_router(ai.router)
