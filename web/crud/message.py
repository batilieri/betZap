from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from web.crud.base import CRUDBase
from web.models import Message
from web.schemas.message import MessageCreate, MessageUpdate

class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]):
    async def get_by_chat(
        self, db: AsyncSession, *, chat_id: int, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_unread_by_chat(self, db: AsyncSession, *, chat_id: int) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat_id, Message.read_at.is_(None))
        )
        return result.scalars().all()

message = CRUDMessage(Message)