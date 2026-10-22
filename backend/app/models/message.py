import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from app.core.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False, index=True)
    sender_type = Column(String(20), nullable=False)  # CUSTOMER, BOT, AGENT, SYSTEM
    sender_name = Column(String(255), default="System")
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
