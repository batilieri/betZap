from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from core.database import Base
import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Classe base para operações CRUD."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Busca registro por ID."""
        try:
            result = await db.execute(select(self.model).where(self.model.id == id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Erro ao buscar {self.model.__name__} por ID {id}: {e}")
            return None

    async def get_by_uuid(self, db: AsyncSession, uuid: str) -> Optional[ModelType]:
        """Busca registro por UUID."""
        try:
            result = await db.execute(select(self.model).where(self.model.uuid == uuid))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Erro ao buscar {self.model.__name__} por UUID {uuid}: {e}")
            return None

    async def get_multi(
            self,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            order_by: Optional[str] = None,
            **filters
    ) -> List[ModelType]:
        """Busca múltiplos registros com paginação e filtros."""
        try:
            query = select(self.model)

            # Aplicar filtros
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.where(getattr(self.model, field) == value)

            # Ordenação
            if order_by and hasattr(self.model, order_by):
                query = query.order_by(getattr(self.model, order_by))
            elif hasattr(self.model, 'created_at'):
                query = query.order_by(self.model.created_at.desc())

            # Paginação
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Erro ao buscar múltiplos {self.model.__name__}: {e}")
            return []

    async def count(self, db: AsyncSession, **filters) -> int:
        """Conta registros com filtros."""
        try:
            query = select(func.count(self.model.id))

            # Aplicar filtros
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.where(getattr(self.model, field) == value)

            result = await db.execute(query)
            return result.scalar() or 0

        except Exception as e:
            logger.error(f"Erro ao contar {self.model.__name__}: {e}")
            return 0

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """Cria novo registro."""
        try:
            obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            await db.flush()
            await db.refresh(db_obj)
            return db_obj

        except Exception as e:
            logger.error(f"Erro ao criar {self.model.__name__}: {e}")
            await db.rollback()
            raise

    async def update(
            self,
            db: AsyncSession,
            *,
            db_obj: ModelType,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Atualiza registro existente."""
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in

            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            # Atualizar timestamp se existir
            if hasattr(db_obj, 'updated_at'):
                from datetime import datetime
                db_obj.updated_at = datetime.utcnow()

            await db.flush()
            await db.refresh(db_obj)
            return db_obj

        except Exception as e:
            logger.error(f"Erro ao atualizar {self.model.__name__}: {e}")
            await db.rollback()
            raise

    async def delete(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """Remove registro por ID."""
        try:
            result = await db.execute(select(self.model).where(self.model.id == id))
            obj = result.scalar_one_or_none()

            if obj:
                await db.delete(obj)
                await db.flush()

            return obj

        except Exception as e:
            logger.error(f"Erro ao deletar {self.model.__name__} ID {id}: {e}")
            await db.rollback()
            raise

    async def soft_delete(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """Soft delete (marca como inativo/deletado)."""
        try:
            result = await db.execute(select(self.model).where(self.model.id == id))
            obj = result.scalar_one_or_none()

            if obj:
                if hasattr(obj, 'is_active'):
                    obj.is_active = False
                elif hasattr(obj, 'is_deleted'):
                    obj.is_deleted = True

                if hasattr(obj, 'updated_at'):
                    from datetime import datetime
                    obj.updated_at = datetime.utcnow()

                await db.flush()
                await db.refresh(obj)

            return obj

        except Exception as e:
            logger.error(f"Erro ao fazer soft delete {self.model.__name__} ID {id}: {e}")
            await db.rollback()
            raise

    async def get_or_create(
            self,
            db: AsyncSession,
            defaults: Optional[Dict[str, Any]] = None,
            **kwargs
    ) -> tuple[ModelType, bool]:
        """Busca ou cria registro. Retorna (objeto, foi_criado)."""
        try:
            # Tentar buscar existente
            query = select(self.model)
            for field, value in kwargs.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

            result = await db.execute(query)
            obj = result.scalar_one_or_none()

            if obj:
                return obj, False

            # Criar novo se não existe
            create_data = {**kwargs, **(defaults or {})}
            db_obj = self.model(**create_data)
            db.add(db_obj)
            await db.flush()
            await db.refresh(db_obj)

            return db_obj, True

        except Exception as e:
            logger.error(f"Erro ao buscar ou criar {self.model.__name__}: {e}")
            await db.rollback()
            raise

    async def bulk_create(self, db: AsyncSession, *, objects: List[CreateSchemaType]) -> List[ModelType]:
        """Cria múltiplos registros em lote."""
        try:
            db_objects = []
            for obj_in in objects:
                obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
                db_obj = self.model(**obj_in_data)
                db_objects.append(db_obj)

            db.add_all(db_objects)
            await db.flush()

            # Refresh todos os objetos
            for db_obj in db_objects:
                await db.refresh(db_obj)

            return db_objects

        except Exception as e:
            logger.error(f"Erro ao criar múltiplos {self.model.__name__}: {e}")
            await db.rollback()
            raise

    async def bulk_update(
            self,
            db: AsyncSession,
            *,
            updates: List[Dict[str, Any]]
    ) -> int:
        """Atualiza múltiplos registros em lote."""
        try:
            if not updates:
                return 0

            # Agrupar por ID para evitar conflitos
            update_count = 0

            for update_data in updates:
                if 'id' not in update_data:
                    continue

                obj_id = update_data.pop('id')

                if hasattr(self.model, 'updated_at'):
                    from datetime import datetime
                    update_data['updated_at'] = datetime.utcnow()

                result = await db.execute(
                    update(self.model)
                    .where(self.model.id == obj_id)
                    .values(**update_data)
                )
                update_count += result.rowcount

            await db.flush()
            return update_count

        except Exception as e:
            logger.error(f"Erro ao atualizar múltiplos {self.model.__name__}: {e}")
            await db.rollback()
            raise

    async def search(
            self,
            db: AsyncSession,
            *,
            query: str,
            search_fields: List[str],
            skip: int = 0,
            limit: int = 100
    ) -> List[ModelType]:
        """Busca textual em campos específicos."""
        try:
            stmt = select(self.model)

            # Construir condições de busca
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    field_attr = getattr(self.model, field)
                    search_conditions.append(field_attr.ilike(f"%{query}%"))

            if search_conditions:
                from sqlalchemy import or_
                stmt = stmt.where(or_(*search_conditions))

            # Ordenação e paginação
            if hasattr(self.model, 'created_at'):
                stmt = stmt.order_by(self.model.created_at.desc())

            stmt = stmt.offset(skip).limit(limit)

            result = await db.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Erro na busca de {self.model.__name__}: {e}")
            return []

    async def exists(self, db: AsyncSession, **filters) -> bool:
        """Verifica se registro existe com os filtros."""
        try:
            query = select(self.model.id)

            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.where(getattr(self.model, field) == value)

            query = query.limit(1)
            result = await db.execute(query)
            return result.scalar() is not None

        except Exception as e:
            logger.error(f"Erro ao verificar existência de {self.model.__name__}: {e}")
            return False