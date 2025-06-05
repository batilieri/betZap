from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from web.core.database import get_db
from web.crud import chat as crud_chat
from web.schemas.chat import Chat, ChatCreate, ChatUpdate
from web.api.deps import get_current_user
from web.models import User

router = APIRouter()


@router.get("/", response_model=List[Chat])
async def get_chats(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    chats = await crud_chat.get_multi(db, skip=skip, limit=limit)
    return chats


@router.get("/{chat_id}", response_model=Chat)
async def get_chat(
        chat_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    chat = await crud_chat.get(db, id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat não encontrado")
    return chat


@router.post("/", response_model=Chat)
async def create_chat(
        chat_in: ChatCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    chat = await crud_chat.create(db, obj_in=chat_in)
    return chat


@router.put("/{chat_id}", response_model=Chat)
async def update_chat(
        chat_id: int,
        chat_in: ChatUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    chat = await crud_chat.get(db, id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat não encontrado")

    chat = await crud_chat.update(db, db_obj=chat, obj_in=chat_in)
    return chat


@router.post("/{chat_id}/assign")
async def assign_chat(
        chat_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    chat = await crud_chat.get(db, id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat não encontrado")

    update_data = ChatUpdate(attendant_id=current_user.id, status="open")
    chat = await crud_chat.update(db, db_obj=chat, obj_in=update_data)
    return {"message": "Chat atribuído com sucesso"}