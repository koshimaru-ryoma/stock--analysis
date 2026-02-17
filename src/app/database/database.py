"""データベース接続とセッション管理を提供するモジュール."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.settings.settings import get_settings

settings = get_settings()
postgres_driver_url = settings.postgres_driver_url

async_engine = create_async_engine(
    url=postgres_driver_url,
    echo=settings.sql_log,
    connect_args={"server_settings": {"timezone": "Asia/Tokyo"}},
)


async def get_async_db_session() -> AsyncGenerator[AsyncSession]:
    """非同期データベースセッションを生成する.

    FastAPIの依存性注入で使用されるジェネレーター関数。
    セッションのライフサイクルを管理し、リクエスト終了時に自動的にクローズする。

    Yields
    ------
        AsyncSession: 非同期データベースセッション

    """
    async with AsyncSession(async_engine) as session:
        yield session
