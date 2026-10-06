from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DatabaseSession
from app.models import Product
from app.schemas.ticket import ProductResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductResponse])
def list_products(_: CurrentUser, database: DatabaseSession) -> list[Product]:
    """List active products available when opening a support ticket."""

    return list(
        database.scalars(
            select(Product).where(Product.is_active.is_(True)).order_by(Product.name.asc())
        )
    )
