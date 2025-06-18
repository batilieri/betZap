from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set, Optional, Any
import json
import asyncio
import logging
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Tipos de mensagem WebSocket."""
    CHAT_MESSAGE = "chat_message"
    USER_TYPING = "user_typing"
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    MESSAGE_READ = "message_read"
    MESSAGE_DELIVERED = "message_delivered"
    CHAT_CREATED = "chat_created"
    CHAT_UPDATED = "chat_updated"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class ConnectionInfo:
    """Informações da conexão WebSocket."""

    def __init__(self, websocket: WebSocket, user_id: int, chat_ids: Set[int] = None):
        self.websocket = websocket
        self.user_id = user_id
        self.chat_ids = chat_ids or set()
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.connection_id = str(uuid.uuid4())


class WebSocketManager:
    """Gerenciador avançado de conexões WebSocket."""

    def __init__(self):
        # Conexões ativas: {connection_id: ConnectionInfo}
        self.active_connections: Dict[str, ConnectionInfo] = {}

        # Mapeamento usuário -> conexões: {user_id: set(connection_ids)}
        self.user_connections: Dict[int, Set[str]] = {}

        # Mapeamento chat -> usuários: {chat_id: set(user_ids)}
        self.chat_users: Dict[int, Set[int]] = {}

        # Lock para operações thread-safe
        self._lock = asyncio.Lock()

        # Task para cleanup periódico
        self._cleanup_task = None
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        """Inicia task de limpeza de conexões inativas."""

        async def cleanup_inactive_connections():
            while True:
                try:
                    await asyncio.sleep(30)  # Verifica a cada 30 segundos
                    await self._cleanup_inactive_connections()
                except Exception as e:
                    logger.error(f"Erro no cleanup de conexões: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_inactive_connections())

    async def connect(self, websocket: WebSocket, user_id: int, chat_ids: List[int] = None) -> str:
        """Conecta um usuário via WebSocket."""
        await websocket.accept()

        async with self._lock:
            # Criar informações da conexão
            connection_info = ConnectionInfo(websocket, user_id, set(chat_ids or []))
            connection_id = connection_info.connection_id

            # Registrar conexão
            self.active_connections[connection_id] = connection_info

            # Atualizar mapeamento usuário -> conexões
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)

            # Atualizar mapeamento chat -> usuários
            for chat_id in connection_info.chat_ids:
                if chat_id not in self.chat_users:
                    self.chat_users[chat_id] = set()
                self.chat_users[chat_id].add(user_id)

        # Notificar outros usuários que este usuário ficou online
        await self._broadcast_user_status(user_id, MessageType.USER_ONLINE)

        logger.info(f"Usuário {user_id} conectado via WebSocket (ID: {connection_id})")
        return connection_id

    async def disconnect(self, connection_id: str):
        """Desconecta uma conexão WebSocket."""
        async with self._lock:
            if connection_id not in self.active_connections:
                return

            connection_info = self.active_connections[connection_id]
            user_id = connection_info.user_id

            # Remover da lista de conexões ativas
            del self.active_connections[connection_id]

            # Atualizar mapeamento usuário -> conexões
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

                    # Se não há mais conexões, remover dos chats
                    for chat_id in connection_info.chat_ids:
                        if chat_id in self.chat_users:
                            self.chat_users[chat_id].discard(user_id)
                            if not self.chat_users[chat_id]:
                                del self.chat_users[chat_id]

        # Notificar se usuário ficou offline
        if user_id not in self.user_connections:
            await self._broadcast_user_status(user_id, MessageType.USER_OFFLINE)

        logger.info(f"Usuário {connection_info.user_id} desconectado (ID: {connection_id})")

    async def send_personal_message(self, user_id: int, message: Dict[str, Any]):
        """Envia mensagem para um usuário específico."""
        if user_id not in self.user_connections:
            logger.warning(f"Usuário {user_id} não está online")
            return False

        connection_ids = self.user_connections[user_id].copy()
        success_count = 0

        for connection_id in connection_ids:
            if connection_id in self.active_connections:
                try:
                    connection_info = self.active_connections[connection_id]
                    await connection_info.websocket.send_text(json.dumps(message))
                    success_count += 1
                except Exception as e:
                    logger.error(f"Erro ao enviar mensagem para conexão {connection_id}: {e}")
                    await self.disconnect(connection_id)

        return success_count > 0

    async def broadcast_to_chat(self, chat_id: int, message: Dict[str, Any], exclude_user: int = None):
        """Envia mensagem para todos os usuários de um chat."""
        if chat_id not in self.chat_users:
            logger.warning(f"Chat {chat_id} não possui usuários online")
            return

        user_ids = self.chat_users[chat_id].copy()
        if exclude_user:
            user_ids.discard(exclude_user)

        tasks = []
        for user_id in user_ids:
            tasks.append(self.send_personal_message(user_id, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Envia mensagem para todos os usuários conectados."""
        tasks = []
        for user_id in self.user_connections.keys():
            tasks.append(self.send_personal_message(user_id, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def handle_message(self, connection_id: str, message: str):
        """Processa mensagem recebida via WebSocket."""
        if connection_id not in self.active_connections:
            return

        try:
            data = json.loads(message)
            message_type = data.get("type")
            connection_info = self.active_connections[connection_id]

            # Atualizar último ping
            connection_info.last_ping = datetime.utcnow()

            if message_type == MessageType.PING:
                await self._handle_ping(connection_info)
            elif message_type == MessageType.USER_TYPING:
                await self._handle_typing(connection_info, data)
            elif message_type == MessageType.MESSAGE_READ:
                await self._handle_message_read(connection_info, data)
            else:
                logger.warning(f"Tipo de mensagem desconhecido: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Mensagem JSON inválida recebida: {message}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")

    async def _handle_ping(self, connection_info: ConnectionInfo):
        """Responde a ping com pong."""
        pong_message = {
            "type": MessageType.PONG,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            await connection_info.websocket.send_text(json.dumps(pong_message))
        except Exception as e:
            logger.error(f"Erro ao enviar pong: {e}")

    async def _handle_typing(self, connection_info: ConnectionInfo, data: Dict[str, Any]):
        """Gerencia indicador de digitação."""
        chat_id = data.get("chat_id")
        is_typing = data.get("is_typing", False)

        if chat_id and chat_id in connection_info.chat_ids:
            typing_message = {
                "type": MessageType.USER_TYPING,
                "chat_id": chat_id,
                "user_id": connection_info.user_id,
                "is_typing": is_typing,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.broadcast_to_chat(chat_id, typing_message, exclude_user=connection_info.user_id)

    async def _handle_message_read(self, connection_info: ConnectionInfo, data: Dict[str, Any]):
        """Gerencia confirmação de leitura."""
        message_id = data.get("message_id")
        chat_id = data.get("chat_id")

        if message_id and chat_id:
            read_message = {
                "type": MessageType.MESSAGE_READ,
                "message_id": message_id,
                "chat_id": chat_id,
                "user_id": connection_info.user_id,
                "read_at": datetime.utcnow().isoformat()
            }
            await self.broadcast_to_chat(chat_id, read_message, exclude_user=connection_info.user_id)

    async def _broadcast_user_status(self, user_id: int, status: MessageType):
        """Notifica mudança de status do usuário."""
        # Encontrar todos os chats do usuário
        user_chats = set()
        for connection_id in self.user_connections.get(user_id, []):
            if connection_id in self.active_connections:
                user_chats.update(self.active_connections[connection_id].chat_ids)

        # Notificar usuários dos chats
        status_message = {
            "type": status,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        for chat_id in user_chats:
            await self.broadcast_to_chat(chat_id, status_message, exclude_user=user_id)

    async def _cleanup_inactive_connections(self):
        """Remove conexões inativas."""
        current_time = datetime.utcnow()
        inactive_connections = []

        for connection_id, connection_info in self.active_connections.items():
            # Considerar inativa se não houve ping há mais de 5 minutos
            if (current_time - connection_info.last_ping).seconds > 300:
                inactive_connections.append(connection_id)

        for connection_id in inactive_connections:
            logger.info(f"Removendo conexão inativa: {connection_id}")
            await self.disconnect(connection_id)

    def get_online_users(self, chat_id: int = None) -> List[int]:
        """Retorna lista de usuários online."""
        if chat_id:
            return list(self.chat_users.get(chat_id, set()))
        else:
            return list(self.user_connections.keys())

    def is_user_online(self, user_id: int) -> bool:
        """Verifica se usuário está online."""
        return user_id in self.user_connections

    async def add_user_to_chat(self, user_id: int, chat_id: int):
        """Adiciona usuário a um chat."""
        async with self._lock:
            # Atualizar conexões existentes do usuário
            for connection_id in self.user_connections.get(user_id, []):
                if connection_id in self.active_connections:
                    self.active_connections[connection_id].chat_ids.add(chat_id)

            # Atualizar mapeamento chat -> usuários
            if chat_id not in self.chat_users:
                self.chat_users[chat_id] = set()
            self.chat_users[chat_id].add(user_id)

        # Notificar outros usuários
        join_message = {
            "type": MessageType.USER_JOINED,
            "chat_id": chat_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_chat(chat_id, join_message, exclude_user=user_id)

    async def remove_user_from_chat(self, user_id: int, chat_id: int):
        """Remove usuário de um chat."""
        async with self._lock:
            # Atualizar conexões existentes do usuário
            for connection_id in self.user_connections.get(user_id, []):
                if connection_id in self.active_connections:
                    self.active_connections[connection_id].chat_ids.discard(chat_id)

            # Atualizar mapeamento chat -> usuários
            if chat_id in self.chat_users:
                self.chat_users[chat_id].discard(user_id)
                if not self.chat_users[chat_id]:
                    del self.chat_users[chat_id]

        # Notificar outros usuários
        leave_message = {
            "type": MessageType.USER_LEFT,
            "chat_id": chat_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_chat(chat_id, leave_message)


# Instância global
websocket_manager = WebSocketManager()