from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from web.crud.base import CRUDBase
from web.models import Contact
from web.schemas.contact import ContactCreate, ContactUpdate


class CRUDContact(CRUDBase[Contact, ContactCreate, ContactUpdate]):
    async def get_by_phone(self, db: AsyncSession, *, phone: str) -> Optional[Contact]:
        result = await db.execute(select(Contact).where(Contact.phone == phone))
        return result.scalar_one_or_none()


contact = CRUDContact(Contact)
