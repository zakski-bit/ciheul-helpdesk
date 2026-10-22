from pydantic import BaseModel, field_serializer
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

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info):
        iso = dt.isoformat()
        if not iso.endswith("Z") and "+" not in iso and "-" not in iso[-6:]:
            return iso + "Z"
        return iso

    class Config:
        from_attributes = True
