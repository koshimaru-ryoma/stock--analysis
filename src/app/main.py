"""FastAPIアプリケーションのメインエントリーポイント."""

from typing import Annotated

from fastapi import Depends, FastAPI
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.database import get_async_db_session
from app.database.model.hero import Hero
from app.settings.settings import Settings, get_settings

app = FastAPI()


@app.get("/")
async def root(
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Settings:
    """ルートエンドポイント.

    テスト用のヒーローデータをデータベースに追加し、
    アプリケーションの設定情報を返却する。

    Args:
        session: 非同期データベースセッション
        settings: アプリケーション設定

    Returns:
        Settings: アプリケーション設定オブジェクト

    """
    session.add(Hero(name="hero", secret_name="HOGE"))
    await session.commit()
    return settings
