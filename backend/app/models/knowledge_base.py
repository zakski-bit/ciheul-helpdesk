import uuid
from sqlalchemy import Column, String, Text, Integer, Boolean
from app.core.database import Base

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question = Column(String(255), nullable=False, index=True)
    answer = Column(Text, nullable=False)
    category = Column(String(50), default="GENERAL")
    keywords = Column(String(255), default="")
    helpful_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
