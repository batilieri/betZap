from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from web.core.database import get_db
from web.crud import message as crud_message
from web.schemas.message import Message, MessageCreate
from web.api.deps import get_current_user
from web.models import User
from web.services.whatsapp_service import WhatsAppService
from web.core.websocket_manager import manager

router = APIRouter()


@router.get("/chat/{chat_id}", response_model=List[Message])
async def get_chat_messages(
        chat_id: int,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    messages = await crud_message.get_by_chat(db, chat_id=chat_id, skip=skip, limit=limit)
    return messages


@router.post("/", response_model=Message)
async def send_message(
        message_in: MessageCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # Criar mensagem no banco
    message = await crud_message.create(db, obj_in=message_in)

    # Enviar via WhatsApp
    whatsapp_service = WhatsAppService()
    success = await whatsapp_service.send_message(
        chat_id=message_in.chat_id,
        content=message_in.content,
        message_type=message_in.message_type
    )

    if success:
        # Notificar via WebSocket
        await manager.send_message_update(
            str(message_in.chat_id),
            {
                "id": message.id,
                "content": message.content,
                "type": message.message_type,
                "timestamp": message.created_at.isoformat()
            }
        )

    return message


@router.post("/upload")
async def upload_media(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user)
):
    # Implementar upload de mídia
    # Salvar arquivo e retornar URL
    return {"media_url": f"/static/uploads/{file.filename}"}