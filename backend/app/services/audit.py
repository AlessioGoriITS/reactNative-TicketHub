from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog


def record_audit_event(
    database: Session,
    action: str,
    *,
    user_id: int | None = None,
    ticket_id: int | None = None,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
) -> None:
    """Queue an auditable domain event in the current transaction."""

    database.add(
        AuditLog(
            user_id=user_id,
            ticket_id=ticket_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )
    )
