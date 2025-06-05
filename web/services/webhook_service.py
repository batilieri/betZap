from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from web.core.database import AsyncSessionLocal
from web.crud import contact as crud_contact, chat as crud_chat, message as crud_message
from web.schemas.contact import ContactCreate
from web.schemas.chat import ChatCreate
from web.schemas.message import MessageCreate
from web.models import MessageType, ChatStatus


class WebhookService:
    async def process_whatsapp_webhook(self, data: Dict[str, Any]) -> Optional[Dict]:
        """Processa webhook recebido do WhatsApp"""
        try:
            async with AsyncSessionLocal() as db:
                # Extrair dados da mensagem
                entry = data.get("entry", [{}])[0]
                changes = entry.get("changes", [{}])[0]
                value = changes.get("value", {})
                messages = value.get("messages", [])

                if not messages:
                    return None

                message_data = messages[0]
                phone = message_data.get("from")
                message_type = message_data.get("type", "text")
                timestamp = message_data.get("timestamp")

                # Buscar ou criar contato
                contact = await crud_contact.get_by_phone(db, phone=phone)
                if not contact:
                    contact_create = ContactCreate(
                        phone=phone,
                        name=f"Cliente {phone[-4:]}"
                    )
                    contact = await crud_contact.create(db, obj_in=contact_create)

                # Buscar ou criar chat
                chat = await self._get_or_create_chat(db, contact.id)

                # Processar conteúdo da mensagem
                content = await self._extract_message_content(message_data, message_type)

                # Criar mensagem
                message_create = MessageCreate(
                    chat_id=chat.id,
                    content=content.get("text", ""),
                    message_type=MessageType(message_type),
                    is_from_customer=True,
                    media_url=content.get("media_url")
                )

                message = await crud_message.create(db, obj_in=message_create)

                return {
                    "chat_id": chat.id,
                    "message_id": message.id,
                    "contact": contact.name,
                    "content": content.get("text", "")
                }

        except Exception as e:
            print(f"Erro ao processar webhook: {e}")
            return None

    async def _get_or_create_chat(self, db: AsyncSession, contact_id: int):
        """Busca chat ativo ou cria novo"""
        # Buscar chat em aberto
        chats = await crud_chat.get_by_status(db, status=ChatStatus.OPEN)
        for chat in chats:
            if chat.contact_id == contact_id:
                return chat

        # Buscar chat pendente
        pending_chats = await crud_chat.get_by_status(db, status=ChatStatus.PENDING)
        for chat in pending_chats:
            if chat.contact_id == contact_id:
                return chat

        # Criar novo chat
        chat_create = ChatCreate(contact_id=contact_id)
        return await crud_chat.create(db, obj_in=chat_create)

    async def _extract_message_content(self, message_data: Dict, message_type: str) -> Dict:
        """Extrai conteúdo da mensagem baseado no tipo"""
        content = {"text": "", "media_url": None}

        if message_type == "text":
            content["text"] = message_data.get("text", {}).get("body", "")
        elif message_type == "image":
            image_data = message_data.get("image", {})
            content["text"] = image_data.get("caption", "")
            content["media_url"] = image_data.get("id")  # Usar para baixar depois
        elif message_type == "audio":
            audio_data = message_data.get("audio", {})
            content["media_url"] = audio_data.get("id")
        elif message_type == "video":
            video_data = message_data.get("video", {})
            content["text"] = video_data.get("caption", "")
            content["media_url"] = video_data.get("id")
        elif message_type == "document":
            doc_data = message_data.get("document", {})
            content["text"] = doc_data.get("filename", "Documento")
            content["media_url"] = doc_data.get("id")

        return content