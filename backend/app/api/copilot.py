from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.core.database import get_db
from app.models.ticket import Ticket
from app.models.message import Message
from app.models.user import User
from app.services.ai_bot_service import AIBotService
from app.api.auth import get_current_user

router = APIRouter(prefix="/copilot", tags=["Copilot Assistant"])

class CopilotAskRequest(BaseModel):
    question: str

class CopilotAnalysisResponse(BaseModel):
    ticket_id: str
    customer_name: str
    summary: str
    draft_reply: str
    follow_ups: List[str]

class CopilotAskResponse(BaseModel):
    answer: str

@router.post("/{ticket_id}/analyze", response_model=CopilotAnalysisResponse)
def analyze_ticket_with_copilot(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan")

    messages = db.query(Message).filter(Message.ticket_id == ticket.id).order_by(Message.created_at).all()
    analysis = AIBotService.generate_copilot_analysis(db, ticket, messages)

    return CopilotAnalysisResponse(
        ticket_id=ticket.id,
        customer_name=ticket.customer.name if ticket.customer else "Pelanggan",
        summary=analysis["summary"],
        draft_reply=analysis["draft_reply"],
        follow_ups=analysis["follow_ups"]
    )

@router.post("/{ticket_id}/ask", response_model=CopilotAskResponse)
def ask_copilot(
    ticket_id: str,
    req: CopilotAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan")

    messages = db.query(Message).filter(Message.ticket_id == ticket.id).order_by(Message.created_at).all()
    answer = AIBotService.ask_copilot(req.question, ticket, messages)

    return CopilotAskResponse(answer=answer)
