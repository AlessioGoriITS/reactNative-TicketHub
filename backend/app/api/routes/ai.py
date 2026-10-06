from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DatabaseSession
from app.api.routes.tickets import get_active_category_names, get_automatic_category, is_staff
from app.models import Ticket
from app.schemas.ai import SuggestedReplyResponse, TicketClassificationResponse
from app.services.ai import classify_ticket, suggest_reply
from app.services.audit import record_audit_event

router = APIRouter(prefix="/ai/tickets", tags=["artificial intelligence"])


def get_staff_ticket(ticket_id: int, current_user: CurrentUser, database: DatabaseSession) -> Ticket:
    if not is_staff(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operazione riservata agli operatori.")
    ticket = database.scalar(select(Ticket).where(Ticket.id == ticket_id).options(selectinload(Ticket.messages)))
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket non trovato.")
    return ticket


@router.post("/{ticket_id}/classify", response_model=TicketClassificationResponse)
def classify_ticket_endpoint(
    ticket_id: int, current_user: CurrentUser, database: DatabaseSession
) -> TicketClassificationResponse:
    """Recalculate the stored AI summary and priority proposal for a staff member."""

    ticket = get_staff_ticket(ticket_id, current_user, database)
    classification = classify_ticket(ticket, get_active_category_names(database))
    ticket.ai_summary = classification.summary
    ticket.ai_suggested_priority = classification.suggested_priority
    ticket.category = get_automatic_category(classification.suggested_category, database)
    record_audit_event(
        database,
        "ticket.ai_classified",
        user_id=current_user.id,
        ticket_id=ticket.id,
        new_value={
            "source": classification.source,
            "priority": classification.suggested_priority.value,
            "category": ticket.category.name if ticket.category else None,
        },
    )
    database.commit()
    return TicketClassificationResponse(
        summary=classification.summary,
        suggested_priority=classification.suggested_priority,
        suggested_category=classification.suggested_category,
        keywords=classification.keywords,
        source=classification.source,
        notice=classification.notice,
    )


@router.post("/{ticket_id}/suggest-reply", response_model=SuggestedReplyResponse)
def suggest_reply_endpoint(
    ticket_id: int, current_user: CurrentUser, database: DatabaseSession
) -> SuggestedReplyResponse:
    """Return an editable AI reply proposal; it is never sent automatically."""

    ticket = get_staff_ticket(ticket_id, current_user, database)
    suggestion = suggest_reply(ticket)
    record_audit_event(
        database,
        "ticket.ai_reply_suggested",
        user_id=current_user.id,
        ticket_id=ticket.id,
        new_value={"source": suggestion.source},
    )
    database.commit()
    return SuggestedReplyResponse(reply=suggestion.reply, source=suggestion.source, notice=suggestion.notice)
