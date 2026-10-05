from datetime import timezone

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DatabaseSession
from app.models import Ticket, TicketPriority, TicketStatus, UserRole
from app.schemas.ticket import DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    current_user: CurrentUser, database: DatabaseSession
) -> DashboardSummaryResponse:
    """Return aggregate metrics scoped to the caller's permissions."""

    query = select(Ticket)
    if current_user.role == UserRole.CUSTOMER:
        query = query.where(Ticket.customer_id == current_user.id)
    tickets = list(database.scalars(query))
    resolved_durations = []
    for ticket in tickets:
        if ticket.resolved_at is not None:
            created_at = ticket.created_at
            resolved_at = ticket.resolved_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if resolved_at.tzinfo is None:
                resolved_at = resolved_at.replace(tzinfo=timezone.utc)
            resolved_durations.append((resolved_at - created_at).total_seconds() / 3600)

    return DashboardSummaryResponse(
        total_tickets=len(tickets),
        open_tickets=sum(ticket.status == TicketStatus.OPEN for ticket in tickets),
        in_progress_tickets=sum(
            ticket.status in {TicketStatus.IN_PROGRESS, TicketStatus.WAITING_FOR_CUSTOMER} for ticket in tickets
        ),
        urgent_tickets=sum(ticket.priority == TicketPriority.URGENT for ticket in tickets),
        resolved_tickets=sum(ticket.status == TicketStatus.RESOLVED for ticket in tickets),
        unassigned_tickets=sum(ticket.assigned_to_id is None for ticket in tickets),
        average_resolution_hours=(round(sum(resolved_durations) / len(resolved_durations), 1) if resolved_durations else None),
    )
