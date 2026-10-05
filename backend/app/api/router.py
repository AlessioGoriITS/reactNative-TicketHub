from fastapi import APIRouter

from app.api.routes import admin, ai, auth, categories, dashboard, tickets

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(categories.router)
api_router.include_router(tickets.router)
api_router.include_router(ai.router)
api_router.include_router(dashboard.router)
api_router.include_router(admin.router)
