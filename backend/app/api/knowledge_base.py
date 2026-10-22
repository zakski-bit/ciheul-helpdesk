from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.schemas.knowledge_base import KBCreate, KBUpdate, KBResponse
from app.api.auth import get_current_user, require_admin

router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base"])

@router.get("", response_model=List[KBResponse])
def list_kb(category: Optional[str] = None, search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True)
    if category:
        query = query.filter(KnowledgeBase.category == category)
    if search:
        query = query.filter(
            (KnowledgeBase.question.ilike(f"%{search}%")) | 
            (KnowledgeBase.keywords.ilike(f"%{search}%"))
        )
    return query.all()

@router.post("", response_model=KBResponse)
def create_kb(data: KBCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    kb = KnowledgeBase(
        question=data.question,
        answer=data.answer,
        category=data.category or "GENERAL",
        keywords=data.keywords or ""
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return kb

@router.put("/{kb_id}", response_model=KBResponse)
def update_kb(kb_id: str, data: KBUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base tidak ditemukan")
    
    if data.question is not None:
        kb.question = data.question
    if data.answer is not None:
        kb.answer = data.answer
    if data.category is not None:
        kb.category = data.category
    if data.keywords is not None:
        kb.keywords = data.keywords
    if data.is_active is not None:
        kb.is_active = data.is_active

    db.commit()
    db.refresh(kb)
    return kb

@router.delete("/{kb_id}")
def delete_kb(kb_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base tidak ditemukan")
    kb.is_active = False
    db.commit()
    return {"status": "success", "message": "Knowledge base berhasil dinonaktifkan"}
