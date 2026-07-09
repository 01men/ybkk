"""SQLAlchemy 异步会话与引擎管理。"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config import get_settings

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine() -> None:
    """初始化引擎（在 FastAPI lifespan 启动时调用）。"""
    global _engine, _session_factory
    settings = get_settings()
    _engine = create_async_engine(
        settings.postgres_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.debug,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def get_engine():  # type: ignore[no-untyped-def]
    if _engine is None:
        init_engine()
    return _engine


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """异步上下文管理器风格的 session。"""
    if _session_factory is None:
        init_engine()
    assert _session_factory is not None
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """关闭引擎（在 FastAPI lifespan 关闭时调用）。"""
    global _engine
    if _engine is not None:
        await _engine.dispose()