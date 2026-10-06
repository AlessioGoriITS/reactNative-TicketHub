import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DatabaseSession
from app.models import Category, Ticket, TicketMessage, TicketPriority, TicketStatus, User, UserRole
from app.schemas.ticket import (
    TicketAssignRequest,
    TicketCreateRequest,
    TicketDetailResponse,
    TicketListItemResponse,
    TicketListResponse,
    TicketMessageCreateRequest,
    TicketMessageResponse,
    TicketStatusRequest,
    TicketUpdateRequest,
)
from app.services.ai import analyze_new_ticket
from app.services.audit import record_audit_event

router = APIRouter(prefix="/tickets", tags=["tickets"])


def is_staff(user: User) -> bool:
    return user.role in {UserRole.AGENT, UserRole.ADMIN}


def ticket_options(include_messages: bool = False):
    options = [
        selectinload(Ticket.category),
        selectinload(Ticket.customer),
        selectinload(Ticket.assigned_to),
    ]
    if include_messages:
        options.append(selectinload(Ticket.messages).selectinload(TicketMessage.author))
    return options


def get_ticket_or_404(
    ticket_id: int,
    current_user: User,
    database: DatabaseSession,
    *,
    include_messages: bool = False,
) -> Ticket:
    """Load a ticket only when the current user is allowed to view it."""

    query = select(Ticket).where(Ticket.id == ticket_id).options(*ticket_options(include_messages))
    if not is_staff(current_user):
        query = query.where(Ticket.customer_id == current_user.id)
    ticket = database.scalar(query)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket non trovato.")
    return ticket


def get_category_or_422(category_id: int, database: DatabaseSession) -> Category:
    category = database.get(Category, category_id)
    if category is None or not category.is_active:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Categoria non valida.")
    return category


def serialize_ticket_detail(ticket: Ticket, current_user: User) -> TicketDetailResponse:
    """Serialize a ticket while preventing customers from seeing internal notes."""

    detail = TicketDetailResponse.model_validate(ticket)
    if not is_staff(current_user):
        detail.messages = [
            TicketMessageResponse.model_validate(message)
            for message in ticket.messages
            if not message.is_internal
        ]
    return detail


@router.get("", response_model=TicketListResponse)
def list_tickets(
    current_user: CurrentUser,
    database: DatabaseSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    ticket_status: TicketStatus | None = Query(default=None, alias="status"),
    priority: TicketPriority | None = None,
    category_id: int | None = Query(default=None, gt=0),
    assigned_to_me: bool = False,
    search: str | None = Query(default=None, min_length=2, max_length=100),
) -> TicketListResponse:
    """List tickets visible to the caller, with filters and pagination."""

    filters = []
    if not is_staff(current_user):
        filters.append(Ticket.customer_id == current_user.id)
    elif assigned_to_me:
        filters.append(Ticket.assigned_to_id == current_user.id)
    if ticket_status is not None:
        filters.append(Ticket.status == ticket_status)
    if priority is not None:
        filters.append(Ticket.priority == priority)
    if category_id is not None:
        filters.append(Ticket.category_id == category_id)
    if search is not None:
        query_text = f"%{search.strip()}%"
        filters.append(or_(Ticket.ticket_number.ilike(query_text), Ticket.title.ilike(query_text)))

    total = database.scalar(select(func.count()).select_from(Ticket).where(*filters)) or 0
    tickets = database.scalars(
        select(Ticket)
        .where(*filters)
        .options(*ticket_options())
        .order_by(Ticket.updated_at.desc(), Ticket.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return TicketListResponse(
        items=[TicketListItemResponse.model_validate(ticket) for ticket in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=TicketDetailResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreateRequest, current_user: CurrentUser, database: DatabaseSession
) -> TicketDetailResponse:
    """Create a new support ticket for the authenticated customer."""

    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="I ticket possono essere aperti dagli account cliente.",
        )
    category = None
    if payload.category_id is not None:
        category = get_category_or_422(payload.category_id, database)

    analysis = analyze_new_ticket(payload.description.strip())
    ticket = Ticket(
        ticket_number=f"TMP-{secrets.token_hex(8)}",
        title=analysis.title,
        description=payload.description.strip(),
        priority=analysis.suggested_priority,
        category=category,
        customer=current_user,
        ai_summary=analysis.summary,
        ai_suggested_priority=analysis.suggested_priority,
    )
    database.add(ticket)
    database.flush()
    ticket.ticket_number = f"TK-{ticket.id:06d}"
    record_audit_event(
        database,
        "ticket.created",
        user_id=current_user.id,
        ticket_id=ticket.id,
        new_value={
            "ticket_number": ticket.ticket_number,
            "priority": ticket.priority.value,
            "ai_source": analysis.source,
            "summary_generated": True,
        },
    )
    database.commit()
    return serialize_ticket_detail(
        get_ticket_or_404(ticket.id, current_user, database, include_messages=True), current_user
    )


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(ticket_id: int, current_user: CurrentUser, database: DatabaseSession) -> TicketDetailResponse:
    """Return a ticket with its conversation."""

    return serialize_ticket_detail(
        get_ticket_or_404(ticket_id, current_user, database, include_messages=True), current_user
    )


@router.patch("/{ticket_id}", response_model=TicketDetailResponse)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdateRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> TicketDetailResponse:
    """Update ticket content; elevated fields are restricted to support staff."""

    ticket = get_ticket_or_404(ticket_id, current_user, database, include_messages=True)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return serialize_ticket_detail(ticket, current_user)

    staff_member = is_staff(current_user)
    if not staff_member and {"title", "priority", "category_id"}.intersection(updates):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non puoi modificare titolo, priorità o categoria.",
        )
    if not staff_member and ticket.status not in {TicketStatus.OPEN, TicketStatus.WAITING_FOR_CUSTOMER}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Il ticket non può più essere modificato in questo stato.",
        )

    old_value = {key: getattr(ticket, key).value if hasattr(getattr(ticket, key), "value") else getattr(ticket, key) for key in updates}
    if "category_id" in updates:
        category_id = updates.pop("category_id")
        ticket.category = get_category_or_422(category_id, database) if category_id is not None else None
    for field, value in updates.items():
        setattr(ticket, field, value.strip() if isinstance(value, str) else value)

    record_audit_event(
        database,
        "ticket.updated",
        user_id=current_user.id,
        ticket_id=ticket.id,
        old_value=old_value,
        new_value=payload.model_dump(exclude_unset=True, mode="json"),
    )
    database.commit()
    return serialize_ticket_detail(
        get_ticket_or_404(ticket.id, current_user, database, include_messages=True), current_user
    )


@router.post("/{ticket_id}/assign", response_model=TicketDetailResponse)
def assign_ticket(
    ticket_id: int,
    payload: TicketAssignRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> TicketDetailResponse:
    """Assign or unassign a ticket. Only staff can perform this operation."""

    if not is_staff(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operazione riservata agli operatori.")
    ticket = get_ticket_or_404(ticket_id, current_user, database, include_messages=True)
    assignee = None
    if payload.assigned_to_id is not None:
        assignee = database.get(User, payload.assigned_to_id)
        if assignee is None or not assignee.is_active or assignee.role != UserRole.AGENT:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Operatore non valido.")

    previous_assignee_id = ticket.assigned_to_id
    ticket.assigned_to = assignee
    if assignee is not None and ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS
    record_audit_event(
        database,
        "ticket.assigned",
        user_id=current_user.id,
        ticket_id=ticket.id,
        old_value={"assigned_to_id": previous_assignee_id},
        new_value={"assigned_to_id": assignee.id if assignee else None},
    )
    database.commit()
    return serialize_ticket_detail(
        get_ticket_or_404(ticket.id, current_user, database, include_messages=True), current_user
    )


@router.post("/{ticket_id}/status", response_model=TicketDetailResponse)
def change_ticket_status(
    ticket_id: int,
    payload: TicketStatusRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> TicketDetailResponse:
    """Change a ticket status according to the caller's role."""

    ticket = get_ticket_or_404(ticket_id, current_user, database, include_messages=True)
    staff_member = is_staff(current_user)
    if not staff_member and not (ticket.status == TicketStatus.RESOLVED and payload.status == TicketStatus.OPEN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Non puoi applicare questo cambio di stato.")
    if payload.status == TicketStatus.CLOSED and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo un amministratore può chiudere un ticket.")

    old_status = ticket.status
    ticket.status = payload.status
    ticket.resolved_at = datetime.now(timezone.utc) if payload.status == TicketStatus.RESOLVED else None
    record_audit_event(
        database,
        "ticket.status_changed",
        user_id=current_user.id,
        ticket_id=ticket.id,
        old_value={"status": old_status.value},
        new_value={"status": ticket.status.value},
    )
    database.commit()
    return serialize_ticket_detail(
        get_ticket_or_404(ticket.id, current_user, database, include_messages=True), current_user
    )


@router.post("/{ticket_id}/resolve", response_model=TicketDetailResponse)
def resolve_ticket(
    ticket_id: int, current_user: CurrentUser, database: DatabaseSession
) -> TicketDetailResponse:
    """Resolve a ticket from the operator workspace."""

    if not is_staff(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operazione riservata agli operatori.")
    ticket = get_ticket_or_404(ticket_id, current_user, database, include_messages=True)
    old_status = ticket.status
    ticket.status = TicketStatus.RESOLVED
    ticket.resolved_at = datetime.now(timezone.utc)
    record_audit_event(
        database,
        "ticket.resolved",
        user_id=current_user.id,
        ticket_id=ticket.id,
        old_value={"status": old_status.value},
        new_value={"status": TicketStatus.RESOLVED.value},
    )
    database.commit()
    return serialize_ticket_detail(
        get_ticket_or_404(ticket.id, current_user, database, include_messages=True), current_user
    )


@router.post("/{ticket_id}/reopen", response_model=TicketDetailResponse)
def reopen_ticket(
    ticket_id: int, current_user: CurrentUser, database: DatabaseSession
) -> TicketDetailResponse:
    """Reopen a resolved ticket for further investigation."""

    ticket = get_ticket_or_404(ticket_id, current_user, database, include_messages=True)
    if ticket.status not in {TicketStatus.RESOLVED, TicketStatus.CLOSED}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Il ticket non è riapribile.")
    if ticket.status == TicketStatus.CLOSED and not is_staff(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Il ticket chiuso può essere riaperto solo dal supporto.")

    old_status = ticket.status
    ticket.status = TicketStatus.OPEN
    ticket.resolved_at = None
    record_audit_event(
        database,
        "ticket.reopened",
        user_id=current_user.id,
        ticket_id=ticket.id,
        old_value={"status": old_status.value},
        new_value={"status": TicketStatus.OPEN.value},
    )
    database.commit()
    return serialize_ticket_detail(
        get_ticket_or_404(ticket.id, current_user, database, include_messages=True), current_user
    )


@router.get("/{ticket_id}/messages", response_model=list[TicketMessageResponse])
def list_ticket_messages(
    ticket_id: int, current_user: CurrentUser, database: DatabaseSession
) -> list[TicketMessageResponse]:
    """List visible messages, excluding internal notes for customers."""

    ticket = get_ticket_or_404(ticket_id, current_user, database, include_messages=True)
    messages = ticket.messages if is_staff(current_user) else [m for m in ticket.messages if not m.is_internal]
    return [TicketMessageResponse.model_validate(message) for message in messages]


@router.post("/{ticket_id}/messages", response_model=TicketMessageResponse, status_code=status.HTTP_201_CREATED)
def add_ticket_message(
    ticket_id: int,
    payload: TicketMessageCreateRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> TicketMessageResponse:
    """Add a customer-visible reply or an internal note to a ticket."""

    ticket = get_ticket_or_404(ticket_id, current_user, database)
    if payload.is_internal and not is_staff(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Le note interne sono riservate agli operatori.")
    if ticket.status == TicketStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Non puoi scrivere su un ticket chiuso.")

    message = TicketMessage(
        ticket_id=ticket.id,
        author_id=current_user.id,
        body=payload.body.strip(),
        is_internal=payload.is_internal,
    )
    database.add(message)
    record_audit_event(
        database,
        "ticket.message_added",
        user_id=current_user.id,
        ticket_id=ticket.id,
        new_value={"is_internal": payload.is_internal},
    )
    database.commit()
    database.refresh(message)
    message.author = current_user
    return TicketMessageResponse.model_validate(message)
