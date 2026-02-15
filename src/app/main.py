"""FastAPIアプリケーションのメインエントリーポイント."""

from typing import Annotated

from fastapi import Depends, FastAPI
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.database import get_async_db_session
from app.settings.settings import Settings, get_settings

app = FastAPI()


@app.get("/")
async def root(
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Settings:
    """ルートエンドポイント.

    アプリケーションの設定情報を返却する。

    Args:
        session: 非同期データベースセッション
        settings: アプリケーション設定

    Returns:
        Settings: アプリケーション設定オブジェクト

    """
    return settings
