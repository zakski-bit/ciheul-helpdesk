import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.core.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_token = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), default="Tamu Pengunjung")
    email = Column(String(255), nullable=True)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
