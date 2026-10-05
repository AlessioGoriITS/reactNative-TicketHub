from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DatabaseSession
from app.models import Category
from app.schemas.ticket import CategoryResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(_: CurrentUser, database: DatabaseSession) -> list[Category]:
    """List active ticket categories for authenticated users."""

    return list(
        database.scalars(
            select(Category).where(Category.is_active.is_(True)).order_by(Category.name.asc())
        )
    )
