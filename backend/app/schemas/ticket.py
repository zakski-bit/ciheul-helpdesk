from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from .message import MessageResponse

class TicketCreate(BaseModel):
    session_token: str
    customer_name: Optional[str] = "Pengunjung Tamu"
    customer_email: Optional[str] = None
    subject: Optional[str] = "Konsultasi Kendala"
    category: Optional[str] = "GENERAL"
    initial_message: str

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    assigned_agent_id: Optional[str] = None

class TicketRatingRequest(BaseModel):
    session_token: Optional[str] = None
    rating: int = Field(..., ge=1, le=5, description="Nilai kepuasan layanan skala 1 sampai 5")
    feedback: Optional[str] = None

class TicketEscalateRequest(BaseModel):
    session_token: Optional[str] = None

class TicketResponse(BaseModel):
    id: str
    customer_id: str
    assigned_agent_id: Optional[str] = None
    subject: str
    category: str
    status: str
    priority: str
    rating: Optional[int] = None
    feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    agent_name: Optional[str] = None
    last_message: Optional[str] = None
    unread_count: Optional[int] = 0

    class Config:
        from_attributes = True

class TicketDetailResponse(TicketResponse):
    messages: List[MessageResponse] = []
