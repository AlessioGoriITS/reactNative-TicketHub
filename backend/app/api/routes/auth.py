from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DatabaseSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models import AuditLog, User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


def create_token_response(user: User) -> TokenResponse:
    """Build the common login/register response for an authenticated user."""

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, database: DatabaseSession) -> TokenResponse:
    """Register a customer account and return an access token."""

    email = str(payload.email).lower()
    existing_user = database.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esiste già un account associato a questa email.",
        )

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole.CUSTOMER,
    )
    database.add(user)
    database.flush()
    database.add(
        AuditLog(
            user_id=user.id,
            action="user.registered",
            new_value={"email": user.email, "role": user.role.value},
        )
    )
    database.commit()
    database.refresh(user)
    return create_token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, database: DatabaseSession) -> TokenResponse:
    """Authenticate an active user with their email and password."""

    email = str(payload.email).lower()
    user = database.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non validi.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    database.add(AuditLog(user_id=user.id, action="user.logged_in"))
    database.commit()
    database.refresh(user)
    return create_token_response(user)


@router.get("/me", response_model=UserResponse)
def get_authenticated_user(current_user: CurrentUser) -> User:
    """Return the profile associated with the current bearer token."""

    return current_user
