from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DatabaseSession
from app.models import User, UserRole
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.audit import record_audit_event

router = APIRouter(prefix="/admin", tags=["administration"])


def require_admin(current_user: CurrentUser) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operazione riservata agli amministratori.")


@router.get("/users", response_model=list[UserResponse])
def list_users(current_user: CurrentUser, database: DatabaseSession) -> list[User]:
    """List all users for administration."""

    require_admin(current_user)
    return list(database.scalars(select(User).order_by(User.created_at.desc(), User.id.desc())))


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int, payload: UserUpdateRequest, current_user: CurrentUser, database: DatabaseSession
) -> User:
    """Update a user's role or active status while preserving an audit trail."""

    require_admin(current_user)
    user = database.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato.")
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return user
    if user.id == current_user.id and updates.get("is_active") is False:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Non puoi disattivare il tuo account.")

    old_value = {key: getattr(user, key).value if hasattr(getattr(user, key), "value") else getattr(user, key) for key in updates}
    for field, value in updates.items():
        setattr(user, field, value)
    record_audit_event(
        database,
        "user.updated_by_admin",
        user_id=current_user.id,
        old_value={"target_user_id": user.id, **old_value},
        new_value={"target_user_id": user.id, **payload.model_dump(exclude_unset=True, mode="json")},
    )
    database.commit()
    database.refresh(user)
    return user
