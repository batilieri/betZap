from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool
from sqlalchemy import event
from contextlib import asynccontextmanager
import logging
from .config import settings

logger = logging.getLogger(__name__)

# Engine com pool de conexões otimizado
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    poolclass=StaticPool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    } if "sqlite" in settings.database_url else {}
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()


@asynccontextmanager
async def get_db():
    """Context manager para sessões de database."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            await session.close()


async def get_db_session():
    """Dependency para FastAPI."""
    async with get_db() as session:
        yield session


# Event listeners para otimização
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Otimizações específicas para SQLite."""
    if "sqlite" in settings.database_url:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000")
        cursor.close()


async def create_tables():
    """Cria as tabelas no banco."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Fecha as conexões do banco."""
    await engine.dispose()