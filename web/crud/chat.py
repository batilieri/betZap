from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from web.crud.base import CRUDBase
from web.models import Chat, ChatStatus
from web.schemas.chat import ChatCreate, ChatUpdate

class CRUDChat(CRUDBase[Chat, ChatCreate, ChatUpdate]):
    async def get_with_messages(self, db: AsyncSession, *, id: int) -> Chat:
        result = await db.execute(
            select(Chat)
            .options(selectinload(Chat.messages), selectinload(Chat.contact), selectinload(Chat.attendant))
            .where(Chat.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_status(self, db: AsyncSession, *, status: ChatStatus) -> List[Chat]:
        result = await db.execute(
            select(Chat)
            .options(selectinload(Chat.contact), selectinload(Chat.attendant))
            .where(Chat.status == status)
        )
        return result.scalars().all()

    async def get_by_attendant(self, db: AsyncSession, *, attendant_id: int) -> List[Chat]:
        result = await db.execute(
            select(Chat)
            .options(selectinload(Chat.contact), selectinload(Chat.messages))
            .where(Chat.attendant_id == attendant_id)
        )
        return result.scalars().all()

chat = CRUDChat(Chat)