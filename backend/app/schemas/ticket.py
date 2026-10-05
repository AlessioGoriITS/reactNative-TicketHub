from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import TicketPriority, TicketStatus, UserRole


class UserSummary(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)


class TicketMessageResponse(BaseModel):
    id: int
    body: str
    is_internal: bool
    created_at: datetime
    author: UserSummary

    model_config = ConfigDict(from_attributes=True)


class TicketCreateRequest(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10, max_length=10_000)
    category_id: int | None = Field(default=None, gt=0)
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=200)
    description: str | None = Field(default=None, min_length=10, max_length=10_000)
    category_id: int | None = Field(default=None, gt=0)
    priority: TicketPriority | None = None


class TicketStatusRequest(BaseModel):
    status: TicketStatus


class TicketAssignRequest(BaseModel):
    assigned_to_id: int | None = Field(default=None, gt=0)


class TicketMessageCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=10_000)
    is_internal: bool = False


class TicketListItemResponse(BaseModel):
    id: int
    ticket_number: str
    title: str
    status: TicketStatus
    priority: TicketPriority
    category: CategoryResponse | None
    customer: UserSummary
    assigned_to: UserSummary | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketDetailResponse(TicketListItemResponse):
    description: str
    resolved_at: datetime | None
    ai_summary: str | None
    ai_suggested_priority: TicketPriority | None
    messages: list[TicketMessageResponse]


class TicketListResponse(BaseModel):
    items: list[TicketListItemResponse]
    total: int
    page: int
    page_size: int
