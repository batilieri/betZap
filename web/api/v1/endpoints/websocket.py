from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from web.core.websocket_manager import manager
from web.api.deps import get_current_user_ws
import json

router = APIRouter()


@router.websocket("/connect/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Processar diferentes tipos de mensagens WebSocket
            if message_data.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message_data.get("type") == "typing":
                # Broadcast typing indicator
                await manager.broadcast(json.dumps({
                    "type": "typing",
                    "user_id": user_id,
                    "chat_id": message_data.get("chat_id")
                }))

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)