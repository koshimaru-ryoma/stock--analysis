"""Tickerテーブルのリポジトリモジュール."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.database import get_async_db_session
from app.database.model.ticker import Ticker


class TickerRepository:
    """Tickerテーブルへのデータアクセスを提供するリポジトリ.

    Attributes
    ----------
        session: 非同期DBセッション

    """

    def __init__(self, session: AsyncSession) -> None:
        """TickerRepositoryを初期化.

        Args:
        ----
            session: 非同期DBセッション

        """
        self.session = session

    async def get_all(self) -> Sequence[Ticker]:
        """全銘柄をDBから取得（is_active 問わず）.

        Returns
        -------
            Tickerオブジェクトのリスト

        """
        result = await self.session.exec(select(Ticker))
        return result.all()

    async def get_active_tickers(
        self,
        specific_ticker: str | None = None,
    ) -> Sequence[Ticker]:
        """アクティブな銘柄をDBから取得.

        Args:
        ----
            specific_ticker: 特定銘柄のみ取得する場合に指定

        Returns:
        -------
            アクティブなTickerオブジェクトのリスト

        """
        if specific_ticker:
            stmt = select(Ticker).where(
                col(Ticker.ticker) == specific_ticker,
                col(Ticker.is_active).is_(True),
            )
        else:
            stmt = select(Ticker).where(
                col(Ticker.is_active).is_(True),
            )

        result = await self.session.exec(stmt)
        return result.all()


async def get_ticker_repository(
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> TickerRepository:
    """FastAPI DI用のTickerRepositoryファクトリ.

    Returns
    -------
        TickerRepository

    """
    return TickerRepository(session)
