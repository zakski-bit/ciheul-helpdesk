from pydantic import BaseModel
from typing import Optional

class KBCreate(BaseModel):
    question: str
    answer: str
    category: Optional[str] = "GENERAL"
    keywords: Optional[str] = ""

class KBUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[str] = None
    is_active: Optional[bool] = None

class KBResponse(BaseModel):
    id: str
    question: str
    answer: str
    category: str
    keywords: str
    helpful_count: int
    is_active: bool

    class Config:
        from_attributes = True
