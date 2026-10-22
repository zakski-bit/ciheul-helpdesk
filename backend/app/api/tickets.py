from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.ticket import Ticket
from app.models.customer import Customer
from app.models.message import Message
from app.models.user import User
from app.schemas.ticket import (
    TicketCreate, TicketUpdate, TicketResponse, 
    TicketDetailResponse, TicketRatingRequest, TicketEscalateRequest
)
from app.schemas.message import MessageResponse
from app.services.ticket_service import TicketService
from app.services.ai_bot_service import AIBotService
from app.websockets.connection_manager import ws_manager
from app.api.auth import get_current_user

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.get("", response_model=List[TicketResponse])
def list_tickets(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Ticket).order_by(desc(Ticket.updated_at))
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    
    tickets = query.all()
    results = []
    for t in tickets:
        last_msg = db.query(Message).filter(Message.ticket_id == t.id).order_by(desc(Message.created_at)).first()
        res = TicketResponse(
            id=t.id,
            customer_id=t.customer_id,
            assigned_agent_id=t.assigned_agent_id,
            subject=t.subject,
            category=t.category,
            status=t.status,
            priority=t.priority,
            rating=t.rating,
            feedback=t.feedback,
            created_at=t.created_at,
            updated_at=t.updated_at,
            customer_name=t.customer.name if t.customer else "Tamu",
            customer_email=t.customer.email if t.customer else None,
            agent_name=t.assigned_agent.full_name if t.assigned_agent else None,
            last_message=last_msg.content if last_msg else None
        )
        results.append(res)
    return results

@router.get("/active/{session_token}", response_model=Optional[TicketDetailResponse])
def get_active_ticket_for_widget(session_token: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.session_token == session_token).first()
    if not customer:
        return None
    
    ticket = TicketService.get_active_ticket_for_customer(db, customer.id)
    if not ticket:
        return None

    messages = db.query(Message).filter(Message.ticket_id == ticket.id).order_by(Message.created_at).all()
    msg_responses = [MessageResponse.from_orm(m) for m in messages]

    return TicketDetailResponse(
        id=ticket.id,
        customer_id=ticket.customer_id,
        assigned_agent_id=None,  # Mask internal staff UUID from customer/widget
        subject=ticket.subject,
        category=ticket.category,
        status=ticket.status,
        priority=ticket.priority,
        rating=ticket.rating,
        feedback=ticket.feedback,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        customer_name=customer.name,
        customer_email=customer.email,
        agent_name=ticket.assigned_agent.full_name if ticket.assigned_agent else None,
        messages=msg_responses
    )

@router.post("", response_model=TicketDetailResponse)
async def create_ticket_from_widget(data: TicketCreate, db: Session = Depends(get_db)):
    ticket, first_msg = TicketService.create_ticket(db, data)
    
    # Process AI Bot response
    ai_result = AIBotService.evaluate_message(db, data.initial_message)
    bot_msg = Message(
        ticket_id=ticket.id,
        sender_type="BOT",
        sender_name="Asisten AI CIHEUL",
        content=ai_result["reply"]
    )
    db.add(bot_msg)
    
    if ai_result["should_escalate"]:
        ticket.status = "WAITING_AGENT"
    
    db.commit()
    db.refresh(ticket)
    db.refresh(bot_msg)

    # Broadcast to agents if escalated
    if ticket.status == "WAITING_AGENT":
        await ws_manager.broadcast_to_agents("ticket_escalated", {
            "ticket_id": ticket.id,
            "customer_name": data.customer_name,
            "subject": ticket.subject,
            "initial_message": data.initial_message
        })

    messages = [
        MessageResponse.from_orm(first_msg),
        MessageResponse.from_orm(bot_msg)
    ]

    return TicketDetailResponse(
        id=ticket.id,
        customer_id=ticket.customer_id,
        assigned_agent_id=None,  # Mask internal staff UUID from customer/widget
        subject=ticket.subject,
        category=ticket.category,
        status=ticket.status,
        priority=ticket.priority,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        customer_name=data.customer_name,
        messages=messages
    )

@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket_detail(ticket_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan")
    
    messages = db.query(Message).filter(Message.ticket_id == ticket.id).order_by(Message.created_at).all()
    msg_responses = [MessageResponse.from_orm(m) for m in messages]

    return TicketDetailResponse(
        id=ticket.id,
        customer_id=ticket.customer_id,
        assigned_agent_id=ticket.assigned_agent_id,
        subject=ticket.subject,
        category=ticket.category,
        status=ticket.status,
        priority=ticket.priority,
        rating=ticket.rating,
        feedback=ticket.feedback,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        customer_name=ticket.customer.name if ticket.customer else "Tamu",
        customer_email=ticket.customer.email if ticket.customer else None,
        agent_name=ticket.assigned_agent.full_name if ticket.assigned_agent else None,
        messages=msg_responses
    )

@router.post("/{ticket_id}/claim", response_model=TicketResponse)
async def claim_ticket(ticket_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan")
    if existing.status in ["RESOLVED", "CLOSED"]:
        raise HTTPException(status_code=400, detail="Tiket yang telah selesai tidak dapat diklaim kembali")
    if existing.assigned_agent_id and existing.assigned_agent_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=409, detail="Tiket ini telah ditugaskan ke staf lain")

    ticket = TicketService.claim_ticket(db, ticket_id, current_user.id)
    if not ticket:
        raise HTTPException(status_code=400, detail="Gagal mengklaim tiket")
    
    # Broadcast to room and agents
    await ws_manager.broadcast_to_ticket(ticket.id, {
        "event": "ticket_claimed",
        "ticket_id": ticket.id,
        "agent_name": current_user.full_name,
        "status": "AGENT_ACTIVE"
    })
    await ws_manager.broadcast_to_agents("ticket_claimed", {
        "ticket_id": ticket.id,
        "agent_id": current_user.id,
        "agent_name": current_user.full_name
    })

    return TicketResponse(
        id=ticket.id,
        customer_id=ticket.customer_id,
        assigned_agent_id=ticket.assigned_agent_id,
        subject=ticket.subject,
        category=ticket.category,
        status=ticket.status,
        priority=ticket.priority,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        customer_name=ticket.customer.name if ticket.customer else None,
        agent_name=current_user.full_name
    )

@router.post("/{ticket_id}/escalate", response_model=TicketResponse)
async def escalate_ticket(
    ticket_id: str, 
    data: Optional[TicketEscalateRequest] = None,
    session_token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan")
    if ticket.status in ["RESOLVED", "CLOSED"]:
        raise HTTPException(status_code=400, detail="Tiket yang telah selesai tidak dapat dialihkan ke eskalasi")
    
    # Ownership verification: must be authenticated agent OR customer matching session_token
    token_to_check = (data.session_token if data and data.session_token else None) or session_token
    is_authenticated_agent = False
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                agent_user = db.query(User).filter(User.id == payload["sub"], User.is_active == True).first()
                if agent_user and agent_user.role in ["CS_AGENT", "ADMIN"]:
                    is_authenticated_agent = True
        except Exception:
            pass

    if not is_authenticated_agent:
        if not token_to_check or not ticket.customer or ticket.customer.session_token != token_to_check:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Otorisasi tidak valid: Hanya pemilik tiket atau staf support yang dapat melakukan eskalasi"
            )

    ticket = TicketService.escalate_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=400, detail="Gagal melakukan eskalasi tiket")
    
    await ws_manager.broadcast_to_ticket(ticket.id, {
        "event": "ticket_escalated",
        "ticket_id": ticket.id,
        "status": "WAITING_AGENT",
        "message": "Tiket telah dialihkan ke Customer Support manusia."
    })
    await ws_manager.broadcast_to_agents("ticket_escalated", {
        "ticket_id": ticket.id,
        "subject": ticket.subject,
        "customer_name": ticket.customer.name if ticket.customer else "Tamu"
    })

    return TicketResponse.from_orm(ticket)

@router.post("/{ticket_id}/resolve", response_model=TicketResponse)
async def resolve_ticket(ticket_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan")
    if existing.status in ["RESOLVED", "CLOSED"]:
        raise HTTPException(status_code=400, detail="Tiket sudah dalam status selesai")

    ticket = TicketService.resolve_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=400, detail="Gagal menyelesaikan tiket")
    
    await ws_manager.broadcast_to_ticket(ticket.id, {
        "event": "ticket_resolved",
        "ticket_id": ticket.id,
        "status": "RESOLVED"
    })
    await ws_manager.broadcast_to_agents("ticket_resolved", {
        "ticket_id": ticket.id,
        "status": "RESOLVED"
    })

    return TicketResponse.from_orm(ticket)

@router.post("/{ticket_id}/rate")
def rate_ticket(
    ticket_id: str, 
    data: TicketRatingRequest, 
    session_token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Tiket tidak ditemukan")
    
    # 1. Customer ownership verification
    provided_session = data.session_token or session_token
    if not provided_session or not ticket.customer or ticket.customer.session_token != provided_session:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Hanya pelanggan pemilik tiket yang berhak memberikan rating"
        )

    # 2. Status verification: ticket must be RESOLVED or CLOSED
    if ticket.status not in ["RESOLVED", "CLOSED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Ulasan hanya dapat diberikan setelah tiket dinyatakan selesai (Resolved)"
        )
    
    # 3. Rating range validation
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Rating harus bernilai antara 1 hingga 5"
        )
    
    ticket.rating = data.rating
    ticket.feedback = data.feedback
    ticket.status = "CLOSED"
    db.commit()
    return {"status": "success", "message": "Rating berhasil disimpan"}
