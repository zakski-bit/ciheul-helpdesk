from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    ticket_id: str
    content: str
    sender_type: str = "CUSTOMER"  # CUSTOMER, AGENT, BOT, SYSTEM
    sender_name: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    ticket_id: str
    sender_type: str
    sender_name: str
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
