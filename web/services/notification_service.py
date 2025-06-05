import asyncio
from typing import List
from web.core.websocket_manager import manager

class NotificationService:
    @staticmethod
    async def notify_new_message(chat_id: int, message_data: dict):
        """Notifica sobre nova mensagem"""
        await manager.send_message_update(str(chat_id), message_data)

    @staticmethod
    async def notify_chat_assignment(chat_id: int, attendant_name: str):
        """Notifica sobre atribuição de chat"""
        notification = {
            "type": "chat_assigned",
            "chat_id": chat_id,
            "attendant": attendant_name,
            "timestamp": asyncio.get_event_loop().time()
        }
        await manager.broadcast(str(notification))

    @staticmethod
    async def notify_typing(chat_id: int, user_id: str, is_typing: bool):
        """Notifica sobre indicador de digitação"""
        notification = {
            "type": "typing",
            "chat_id": chat_id,
            "user_id": user_id,
            "is_typing": is_typing
        }
        await manager.broadcast(str(notification))