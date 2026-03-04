"""FastAPIアプリケーションのメインエントリーポイント."""

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.database import get_async_db_session
from app.exceptions.handlers import register_exception_handlers
from app.settings.settings import Settings, get_settings
from app.stock_price.router import router as stock_price_router
from app.ticker.router import router as ticker_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.include_router(ticker_router)
app.include_router(stock_price_router)


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
