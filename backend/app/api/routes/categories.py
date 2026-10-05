from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DatabaseSession
from app.models import Category, UserRole
from app.schemas.ticket import CategoryCreateRequest, CategoryResponse, CategoryUpdateRequest

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(_: CurrentUser, database: DatabaseSession) -> list[Category]:
    """List active ticket categories for authenticated users."""

    return list(
        database.scalars(
            select(Category).where(Category.is_active.is_(True)).order_by(Category.name.asc())
        )
    )


def require_admin(current_user: CurrentUser) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operazione riservata agli amministratori.")


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreateRequest, current_user: CurrentUser, database: DatabaseSession
) -> Category:
    """Create a category available to new tickets."""

    require_admin(current_user)
    existing_category = database.scalar(select(Category).where(Category.name == payload.name.strip()))
    if existing_category is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esiste già una categoria con questo nome.")
    category = Category(name=payload.name.strip(), description=payload.description.strip() if payload.description else None)
    database.add(category)
    database.commit()
    database.refresh(category)
    return category


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    payload: CategoryUpdateRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> Category:
    """Update a category or deactivate it without deleting historical data."""

    require_admin(current_user)
    category = database.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria non trovata.")
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates:
        name = updates["name"].strip()
        duplicate = database.scalar(select(Category).where(Category.name == name, Category.id != category.id))
        if duplicate is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esiste già una categoria con questo nome.")
        category.name = name
    if "description" in updates:
        category.description = updates["description"].strip() if updates["description"] else None
    if "is_active" in updates:
        category.is_active = updates["is_active"]
    database.commit()
    database.refresh(category)
    return category
