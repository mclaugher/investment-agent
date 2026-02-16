"""WebSocket endpoint for real-time updates (per §10.2).

Broadcasts agent status, new reports, decisions, and price updates.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected ({len(self.active_connections)} total)")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected ({len(self.active_connections)} total)")

    async def broadcast(self, message: dict[str, Any]):
        """Send message to all connected clients."""
        text = json.dumps(message, default=str)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(text)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.active_connections.remove(conn)


# Singleton manager
manager = ConnectionManager()


@router.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time updates WebSocket (per §10.2).

    Message types:
    - agent_status: Agent started/completed/error
    - new_report: New analysis report generated
    - new_decision: New investment decision
    - price_update: Real-time price change
    - analysis_progress: Progress of analysis cycle
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; handle incoming messages if needed
            data = await websocket.receive_text()
            # Client can send ping or filter requests
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Helper functions for broadcasting from other parts of the app

async def broadcast_agent_status(agent_name: str, status: str, message: str = ""):
    """Broadcast agent status update (per §10.2)."""
    await manager.broadcast({
        "type": "agent_status",
        "payload": {
            "agent_name": agent_name,
            "status": status,
            "message": message,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def broadcast_new_report(report_id: int, agent_name: str, symbol: str | None = None):
    """Broadcast new report notification (per §10.2)."""
    await manager.broadcast({
        "type": "new_report",
        "payload": {
            "report_id": report_id,
            "agent_name": agent_name,
            "symbol": symbol,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def broadcast_new_decision(decision_id: int, symbol: str, action: str):
    """Broadcast new decision notification (per §10.2)."""
    await manager.broadcast({
        "type": "new_decision",
        "payload": {
            "decision_id": decision_id,
            "symbol": symbol,
            "action": action,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def broadcast_price_update(symbol: str, price: float):
    """Broadcast price update (per §10.2)."""
    await manager.broadcast({
        "type": "price_update",
        "payload": {
            "symbol": symbol,
            "price": price,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def broadcast_analysis_progress(progress_pct: float, message: str):
    """Broadcast analysis progress (per §10.2)."""
    await manager.broadcast({
        "type": "analysis_progress",
        "payload": {
            "progress_pct": progress_pct,
            "message": message,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
