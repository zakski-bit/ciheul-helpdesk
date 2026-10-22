from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.ticket import Ticket
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/summary")
def get_analytics_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_tickets = db.query(Ticket).count()
    waiting_agent = db.query(Ticket).filter(Ticket.status == "WAITING_AGENT").count()
    agent_active = db.query(Ticket).filter(Ticket.status == "AGENT_ACTIVE").count()
    bot_active = db.query(Ticket).filter(Ticket.status == "BOT_ACTIVE").count()
    resolved = db.query(Ticket).filter(Ticket.status.in_(["RESOLVED", "CLOSED"])).count()
    
    # Deflection count: Tickets resolved without human agent assignment
    deflected_count = db.query(Ticket).filter(
        Ticket.status.in_(["RESOLVED", "CLOSED"]),
        Ticket.assigned_agent_id.is_(None)
    ).count()
    deflection_rate = round((deflected_count / max(total_tickets, 1)) * 100, 1) if total_tickets > 0 else 0.0

    raw_avg_rating = db.query(func.avg(Ticket.rating)).filter(Ticket.rating.isnot(None)).scalar()
    avg_rating = round(float(raw_avg_rating), 1) if raw_avg_rating is not None else None
    
    total_kb_helped = db.query(func.sum(KnowledgeBase.helpful_count)).scalar() or 0

    return {
        "total_tickets": total_tickets,
        "waiting_agent": waiting_agent,
        "agent_active": agent_active,
        "bot_active": bot_active,
        "resolved_tickets": resolved,
        "deflection_rate": deflection_rate,
        "average_cs_rating": avg_rating,
        "kb_helpful_hits": total_kb_helped
    }
