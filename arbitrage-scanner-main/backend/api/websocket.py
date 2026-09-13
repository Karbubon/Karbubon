from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
from datetime import datetime

# Создаем роутер без префикса здесь (префикс будет в main.py)
router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.opportunity_cache: Dict[int, dict] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(
                f"❌ WebSocket client disconnected. Total: {len(self.active_connections)}"
            )

    async def broadcast_new_opportunity(self, opportunity: dict):
        message = {
            "type": "new_opportunity",
            "data": opportunity,
            "timestamp": datetime.now().isoformat(),
        }
        self.opportunity_cache[opportunity.get("id")] = opportunity

        for connection in self.active_connections[
            :
        ]:  # Копия списка для безопасной итерации
            try:
                await connection.send_json(message)
            except:
                self.disconnect(connection)

    async def broadcast_opportunity_gone(self, opportunity_id: int):
        message = {
            "type": "opportunity_gone",
            "opportunity_id": opportunity_id,
            "timestamp": datetime.now().isoformat(),
        }
        self.opportunity_cache.pop(opportunity_id, None)

        for connection in self.active_connections[:]:
            try:
                await connection.send_json(message)
            except:
                self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws/opportunities")
async def websocket_opportunities(websocket: WebSocket):
    """WebSocket для получения арбитражей в реальном времени"""
    await manager.connect(websocket)

    try:
        # Отправляем текущие активные возможности
        for opp in manager.opportunity_cache.values():
            await websocket.send_json(
                {
                    "type": "new_opportunity",
                    "data": opp,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Поддерживаем соединение
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json(
                    {"type": "pong", "timestamp": datetime.now().isoformat()}
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
