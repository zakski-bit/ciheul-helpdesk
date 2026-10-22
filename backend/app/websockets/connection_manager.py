import json
import logging
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger("helpdesk.ws")

class ConnectionManager:
    def __init__(self):
        # ticket_id -> Set of WebSockets (Customer Widget, Active CS on Web, Active CS on Mobile)
        self.ticket_rooms: Dict[str, Set[WebSocket]] = {}
        
        # Global CS Agent broadcast channels (Web Dashboard & Flutter Mobile App)
        self.agent_broadcast_clients: Set[WebSocket] = set()

    async def connect_to_ticket(self, websocket: WebSocket, ticket_id: str):
        await websocket.accept()
        if ticket_id not in self.ticket_rooms:
            self.ticket_rooms[ticket_id] = set()
        self.ticket_rooms[ticket_id].add(websocket)
        logger.info(f"Client connected to ticket room {ticket_id}. Total in room: {len(self.ticket_rooms[ticket_id])}")

    async def connect_agent_channel(self, websocket: WebSocket):
        await websocket.accept()
        self.agent_broadcast_clients.add(websocket)
        logger.info(f"Agent connected to global broadcast channel. Total agents: {len(self.agent_broadcast_clients)}")

    def disconnect(self, websocket: WebSocket, ticket_id: Optional[str] = None):
        # Remove from ticket room
        if ticket_id and ticket_id in self.ticket_rooms:
            self.ticket_rooms[ticket_id].discard(websocket)
            if not self.ticket_rooms[ticket_id]:
                del self.ticket_rooms[ticket_id]
        else:
            # Search all rooms
            for t_id, sockets in list(self.ticket_rooms.items()):
                sockets.discard(websocket)
                if not sockets:
                    del self.ticket_rooms[t_id]

        # Remove from agent channels
        self.agent_broadcast_clients.discard(websocket)
        logger.info("WebSocket disconnected and cleaned from registries.")

    async def broadcast_to_ticket(self, ticket_id: str, message: Dict[str, Any]):
        """Broadcast a message event to all participants in a ticket room (Customer, CS Web, CS Mobile)."""
        if ticket_id in self.ticket_rooms:
            payload = json.dumps(message)
            dead_sockets = []
            for ws in self.ticket_rooms[ticket_id]:
                try:
                    await ws.send_text(payload)
                except Exception as e:
                    logger.warning(f"Failed to send to client in ticket {ticket_id}: {e}")
                    dead_sockets.append(ws)
            for ws in dead_sockets:
                self.ticket_rooms[ticket_id].discard(ws)

    async def broadcast_to_agents(self, event: str, data: Dict[str, Any]):
        """Broadcast an event to all CS agents on Web App and Mobile App."""
        payload = json.dumps({
            "event": event,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
        dead_sockets = []
        for ws in self.agent_broadcast_clients:
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(f"Failed to broadcast to agent: {e}")
                dead_sockets.append(ws)
        for ws in dead_sockets:
            self.agent_broadcast_clients.discard(ws)

ws_manager = ConnectionManager()
