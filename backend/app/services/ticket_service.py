from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.ticket import Ticket
from app.models.customer import Customer
from app.models.message import Message
from app.models.user import User
from app.schemas.ticket import TicketCreate

class TicketService:
    @classmethod
    def get_or_create_customer(cls, db: Session, session_token: str, name: str = "Tamu", email: Optional[str] = None) -> Customer:
        customer = db.query(Customer).filter(Customer.session_token == session_token).first()
        if not customer:
            customer = Customer(session_token=session_token, name=name, email=email)
            db.add(customer)
            db.commit()
            db.refresh(customer)
        else:
            customer.last_seen_at = datetime.utcnow()
            if name and name != "Tamu":
                customer.name = name
            if email:
                customer.email = email
            db.commit()
        return customer

    @classmethod
    def get_active_ticket_for_customer(cls, db: Session, customer_id: str) -> Optional[Ticket]:
        # 1. First check for active ongoing tickets
        active = db.query(Ticket).filter(
            Ticket.customer_id == customer_id,
            Ticket.status.in_(["BOT_ACTIVE", "WAITING_AGENT", "AGENT_ACTIVE"])
        ).order_by(desc(Ticket.created_at)).first()
        if active:
            return active

        # 2. Check for recent resolved tickets that have not been rated yet
        unrated_resolved = db.query(Ticket).filter(
            Ticket.customer_id == customer_id,
            Ticket.status == "RESOLVED",
            Ticket.rating.is_(None)
        ).order_by(desc(Ticket.updated_at)).first()
        return unrated_resolved

    @classmethod
    def create_ticket(cls, db: Session, data: TicketCreate) -> Tuple[Ticket, Message]:
        customer = cls.get_or_create_customer(
            db, session_token=data.session_token,
            name=data.customer_name or "Tamu",
            email=data.customer_email
        )

        ticket = Ticket(
            customer_id=customer.id,
            subject=data.subject or "Bantuan Kendala Pengguna",
            category=data.category or "GENERAL",
            status="BOT_ACTIVE",
            priority="MEDIUM"
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        # Initial message
        first_msg = Message(
            ticket_id=ticket.id,
            sender_type="CUSTOMER",
            sender_name=customer.name,
            content=data.initial_message
        )
        db.add(first_msg)
        db.commit()
        db.refresh(first_msg)

        return ticket, first_msg

    @classmethod
    def escalate_ticket(cls, db: Session, ticket_id: str) -> Optional[Ticket]:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket or ticket.status in ["RESOLVED", "CLOSED"]:
            return None

        ticket.status = "WAITING_AGENT"
        ticket.updated_at = datetime.utcnow()
        
        # Add system message
        sys_msg = Message(
            ticket_id=ticket.id,
            sender_type="SYSTEM",
            sender_name="Sistem Helpdesk",
            content="Tiket telah dialihkan ke antrean Customer Support."
        )
        db.add(sys_msg)
        db.commit()
        db.refresh(ticket)
        return ticket

    @classmethod
    def claim_ticket(cls, db: Session, ticket_id: str, agent_id: str, allow_takeover: bool = False) -> Optional[Ticket]:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        agent = db.query(User).filter(User.id == agent_id).first()
        if not ticket or not agent:
            return None

        # Cannot claim already resolved or closed ticket
        if ticket.status in ["RESOLVED", "CLOSED"]:
            return None

        # Prevent accidental claim takeover if already claimed by another agent
        if ticket.assigned_agent_id and ticket.assigned_agent_id != agent.id and not allow_takeover:
            return None

        ticket.assigned_agent_id = agent.id
        ticket.status = "AGENT_ACTIVE"
        ticket.updated_at = datetime.utcnow()

        sys_msg = Message(
            ticket_id=ticket.id,
            sender_type="SYSTEM",
            sender_name="Sistem Helpdesk",
            content=f"Agen {agent.full_name} ditugaskan ke percakapan ini."
        )
        db.add(sys_msg)
        db.commit()
        db.refresh(ticket)
        return ticket

    @classmethod
    def resolve_ticket(cls, db: Session, ticket_id: str) -> Optional[Ticket]:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket or ticket.status in ["RESOLVED", "CLOSED"]:
            return None

        ticket.status = "RESOLVED"
        ticket.updated_at = datetime.utcnow()

        sys_msg = Message(
            ticket_id=ticket.id,
            sender_type="SYSTEM",
            sender_name="Sistem Helpdesk",
            content="Kendala telah ditandai selesai oleh Customer Support."
        )
        db.add(sys_msg)
        db.commit()
        db.refresh(ticket)
        return ticket
