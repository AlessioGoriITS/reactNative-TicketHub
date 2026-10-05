from typing import Literal

from pydantic import BaseModel, Field

from app.models import TicketPriority


class TicketClassificationResponse(BaseModel):
    summary: str
    suggested_priority: TicketPriority
    suggested_category: str | None = None
    keywords: list[str] = Field(default_factory=list)
    source: Literal["ai", "fallback"]
    notice: str | None = None


class SuggestedReplyResponse(BaseModel):
    reply: str
    source: Literal["ai", "fallback"]
    notice: str | None = None
