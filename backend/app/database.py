"""SQLite database setup with async SQLAlchemy."""
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    pass


# Ensure data directory exists
os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)

engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.DATABASE_PATH}",
    echo=settings.DEBUG,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables and run lightweight migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Add graph_data column if missing (migration for existing DBs)
        try:
            await conn.execute(
                __import__("sqlalchemy").text(
                    "ALTER TABLE jobs ADD COLUMN graph_data TEXT"
                )
            )
        except Exception:
            pass  # Column already exists


async def get_db() -> AsyncSession:
    """Dependency for FastAPI route injection."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
