from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)
DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    database: DatabaseSession,
) -> User:
    """Load the active user identified by a valid bearer token."""

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticazione richiesta o token non valido.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise unauthorized

    subject = payload.get("sub")
    try:
        user_id = int(subject)
    except (TypeError, ValueError) as error:
        raise unauthorized from error

    user = database.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: UserRole):
    """Return a dependency that permits only the listed user roles."""

    def role_guard(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non disponi dei permessi necessari per questa operazione.",
            )
        return current_user

    return role_guard
