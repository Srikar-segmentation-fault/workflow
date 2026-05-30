"""
WorkFlow — Database Layer
Provides:
  - Supabase async client (for Auth + Storage)
  - SQLAlchemy async engine (for SQLModel ORM queries)
  - Async session factory
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from supabase import AsyncClient, acreate_client

from app.config import settings

from sqlalchemy import event

# ── SQLAlchemy async engine ────────────────────────────────────────────────────
if settings.database_url.startswith("sqlite"):
    engine = create_async_engine(
        settings.database_url,
        echo=settings.is_development,
    )
    
    # Activate WAL (Write-Ahead Logging) and Normal synchronous mode for SQLite concurrency
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()
else:
    engine = create_async_engine(
        settings.database_url,
        echo=settings.is_development,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Supabase async client ──────────────────────────────────────────────────────
_supabase_client: AsyncClient | None = None


async def get_supabase() -> AsyncClient:
    """Returns a singleton Supabase async client."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = await acreate_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    return _supabase_client


# ── DB init ───────────────────────────────────────────────────────────────────
async def init_db() -> None:
    """Create all tables defined in SQLModel metadata (dev/test only)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db() -> None:
    """Dispose the engine connection pool on shutdown."""
    await engine.dispose()
