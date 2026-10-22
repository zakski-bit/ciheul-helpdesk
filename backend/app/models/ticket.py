import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    assigned_agent_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    
    subject = Column(String(255), default="Bantuan Kendala Pengguna")
    category = Column(String(50), default="GENERAL")  # TECHNICAL, BILLING, ACCOUNT, GENERAL
    status = Column(String(50), default="BOT_ACTIVE", index=True)  # BOT_ACTIVE, WAITING_AGENT, AGENT_ACTIVE, RESOLVED, CLOSED
    priority = Column(String(50), default="MEDIUM")  # LOW, MEDIUM, HIGH, URGENT
    
    rating = Column(Integer, nullable=True)  # 1 to 5
    feedback = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", backref="tickets")
    assigned_agent = relationship("User", backref="assigned_tickets")
    messages = relationship("Message", backref="ticket", cascade="all, delete-orphan", order_by="Message.created_at")
