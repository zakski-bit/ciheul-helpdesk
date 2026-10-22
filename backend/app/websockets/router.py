import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.ticket import Ticket
from app.models.customer import Customer
from app.models.user import User
from app.models.message import Message
from app.services.ai_bot_service import AIBotService
from app.websockets.connection_manager import ws_manager

logger = logging.getLogger("helpdesk.ws")
router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/ticket/{ticket_id}")
async def websocket_ticket_room(
    websocket: WebSocket, 
    ticket_id: str,
    token: Optional[str] = Query(None),
    session_token: Optional[str] = Query(None)
):
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        verified_sender_type: str = ""
        verified_sender_name: str = ""

        # 1. Authenticate via Agent/Admin JWT
        if token:
            payload = decode_access_token(token)
            if not payload or "sub" not in payload:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            user = db.query(User).filter(User.id == payload["sub"], User.is_active == True).first()
            if not user or user.role not in ["CS_AGENT", "ADMIN"]:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            verified_sender_type = "AGENT"
            verified_sender_name = user.full_name

        # 2. Authenticate via Customer session token
        elif session_token:
            if not ticket.customer or ticket.customer.session_token != session_token:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            verified_sender_type = "CUSTOMER"
            verified_sender_name = ticket.customer.name or "Pelanggan"

        # 3. Reject unauthenticated connections
        else:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Connection verified - register to room
        await ws_manager.connect_to_ticket(websocket, ticket_id)

        while True:
            raw_data = await websocket.receive_text()
            try:
                msg_data = json.loads(raw_data)
            except json.JSONDecodeError:
                continue

            event_type = msg_data.get("event")

            # Heartbeat Ping-Pong
            if event_type == "ping":
                await websocket.send_text(json.dumps({
                    "event": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                continue

            # Typing indicator (Identity enforced by server session)
            elif event_type == "typing":
                await ws_manager.broadcast_to_ticket(ticket_id, {
                    "event": "typing",
                    "sender_type": verified_sender_type,
                    "sender_name": verified_sender_name,
                    "is_typing": bool(msg_data.get("is_typing", True))
                })
                continue

            # Offline missed messages sync
            elif event_type == "sync_missed":
                last_msg_id = msg_data.get("last_message_id")
                query = db.query(Message).filter(Message.ticket_id == ticket_id)
                if last_msg_id:
                    last_msg = db.query(Message).filter(Message.id == last_msg_id).first()
                    if last_msg:
                        query = query.filter(Message.created_at > last_msg.created_at)
                missed = query.order_by(Message.created_at).all()
                await websocket.send_text(json.dumps({
                    "event": "sync_result",
                    "messages": [
                        {
                            "id": m.id,
                            "ticket_id": m.ticket_id,
                            "sender_type": m.sender_type,
                            "sender_name": m.sender_name,
                            "content": m.content,
                            "created_at": m.created_at.isoformat()
                        } for m in missed
                    ]
                }))
                continue

            # Chat Message sent (Strict Anti-Spoofing: sender_type & sender_name from server session only)
            elif event_type == "send_message":
                content = str(msg_data.get("content", "")).strip()
                if not content:
                    continue

                # Save incoming message to DB
                new_msg = Message(
                    ticket_id=ticket_id,
                    sender_type=verified_sender_type,
                    sender_name=verified_sender_name,
                    content=content
                )
                db.add(new_msg)
                
                # Fetch ticket and update timestamp
                ticket.updated_at = datetime.utcnow()

                db.commit()
                db.refresh(new_msg)

                # Broadcast to room
                msg_payload = {
                    "event": "new_message",
                    "id": new_msg.id,
                    "ticket_id": ticket_id,
                    "sender_type": verified_sender_type,
                    "sender_name": verified_sender_name,
                    "content": new_msg.content,
                    "created_at": new_msg.created_at.isoformat()
                }
                await ws_manager.broadcast_to_ticket(ticket_id, msg_payload)

                # Also inform CS agents global feed
                await ws_manager.broadcast_to_agents("ticket_message_activity", {
                    "ticket_id": ticket_id,
                    "sender_type": verified_sender_type,
                    "last_message": content
                })

                # If customer is chatting and ticket is in BOT_ACTIVE mode, evaluate AI bot
                if verified_sender_type == "CUSTOMER" and ticket and ticket.status == "BOT_ACTIVE":
                    ai_res = AIBotService.evaluate_message(db, content)
                    
                    bot_msg = Message(
                        ticket_id=ticket_id,
                        sender_type="BOT",
                        sender_name="Asisten AI CIHEUL",
                        content=ai_res["reply"]
                    )
                    db.add(bot_msg)

                    if ai_res["should_escalate"]:
                        ticket.status = "WAITING_AGENT"

                    db.commit()
                    db.refresh(bot_msg)

                    bot_payload = {
                        "event": "new_message",
                        "id": bot_msg.id,
                        "ticket_id": ticket_id,
                        "sender_type": "BOT",
                        "sender_name": "Asisten AI CIHEUL",
                        "content": bot_msg.content,
                        "created_at": bot_msg.created_at.isoformat()
                    }
                    await ws_manager.broadcast_to_ticket(ticket_id, bot_payload)

                    if ai_res["should_escalate"]:
                        await ws_manager.broadcast_to_ticket(ticket_id, {
                            "event": "ticket_escalated",
                            "ticket_id": ticket_id,
                            "status": "WAITING_AGENT"
                        })
                        await ws_manager.broadcast_to_agents("ticket_escalated", {
                            "ticket_id": ticket_id,
                            "subject": ticket.subject,
                            "customer_name": ticket.customer.name if ticket.customer else "Tamu",
                            "initial_message": content
                        })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, ticket_id)
    except Exception as e:
        logger.error(f"Error in websocket ticket room: {e}")
        ws_manager.disconnect(websocket, ticket_id)
    finally:
        db.close()

@router.websocket("/ws/agents")
async def websocket_agents_channel(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """Global broadcast channel for CS Agents on Web Dashboard & Flutter Mobile App (Protected with JWT)."""
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == payload["sub"], User.is_active == True).first()
        if not user or user.role not in ["CS_AGENT", "ADMIN"]:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    finally:
        db.close()

    await ws_manager.connect_agent_channel(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                if data.get("event") == "ping":
                    await websocket.send_text(json.dumps({
                        "event": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in agents websocket: {e}")
        ws_manager.disconnect(websocket)
