from pydantic import BaseModel, Field, field_serializer
from datetime import datetime
from typing import Optional, List
from .message import MessageResponse

class TicketCreate(BaseModel):
    session_token: str = Field(..., min_length=5, max_length=128)
    customer_name: Optional[str] = Field("Pengunjung Tamu", max_length=100)
    customer_email: Optional[str] = Field(None, max_length=150)
    subject: Optional[str] = Field("Konsultasi Kendala", max_length=200)
    category: Optional[str] = Field("GENERAL", max_length=50)
    initial_message: str = Field(..., min_length=1, max_length=3000)

class TicketUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    assigned_agent_id: Optional[str] = Field(None, max_length=100)

class TicketRatingRequest(BaseModel):
    session_token: Optional[str] = Field(None, max_length=128)
    rating: int = Field(..., ge=1, le=5, description="Nilai kepuasan layanan skala 1 sampai 5")
    feedback: Optional[str] = Field(None, max_length=1000)

class TicketEscalateRequest(BaseModel):
    session_token: Optional[str] = Field(None, max_length=128)

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

    @field_serializer("created_at", "updated_at")
    def serialize_datetimes(self, dt: datetime, _info):
        iso = dt.isoformat()
        if not iso.endswith("Z") and "+" not in iso and "-" not in iso[-6:]:
            return iso + "Z"
        return iso

    class Config:
        from_attributes = True

class TicketDetailResponse(TicketResponse):
    messages: List[MessageResponse] = []
