"""StockPrice1mテーブルのリポジトリモジュール."""

import logging
from datetime import datetime
from typing import Annotated, Any, cast

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.common.log_prefix import INSERT_STOCK_DATA
from app.database.database import get_async_db_session
from app.database.model.stock_price_1m import StockPrice1m

logger = logging.getLogger(__name__)


class StockPrice1mRepository:
    """StockPrice1mテーブルへのデータアクセスを提供するリポジトリ.

    Attributes
    ----------
        session: 非同期DBセッション

    """

    def __init__(self, session: AsyncSession) -> None:
        """StockPrice1mRepositoryを初期化.

        Args:
        ----
            session: 非同期DBセッション

        """
        self.session = session

    async def get_date_ranges(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[tuple[datetime, datetime, int]]:
        """指定範囲内の既存データの日時範囲を日単位で取得.

        Args:
        ----
            ticker: 銘柄コード
            start_date: 開始日時
            end_date: 終了日時

        Returns:
        -------
            (min_datetime, max_datetime, count)のタプルのリスト

        """
        stmt = (
            select(
                func.date(StockPrice1m.price_datetime).label("date"),
                func.min(StockPrice1m.price_datetime).label("min_dt"),
                func.max(StockPrice1m.price_datetime).label("max_dt"),
                func.count().label("count"),
            )
            .where(
                col(StockPrice1m.ticker) == ticker,
                col(StockPrice1m.price_datetime) >= start_date,
                col(StockPrice1m.price_datetime) <= end_date,
            )
            .group_by(func.date(StockPrice1m.price_datetime))
            .order_by("date")
        )

        result = await self.session.exec(stmt)  # type: ignore[call-overload]
        rows = result.all()

        return [(row.min_dt, row.max_dt, row.count) for row in rows]

    async def bulk_insert(
        self,
        records: list[StockPrice1m],
    ) -> int:
        """株価レコードを一括登録.

        Args:
        ----
            records: 登録するStockPrice1mのリスト

        Returns:
        -------
            登録したレコード数

        Raises:
        ------
            Exception: DB登録エラー時

        """
        if not records:
            return 0

        rows = [self._to_insert_row(record) for record in records]

        try:
            stmt = self._build_insert_statement(rows, with_returning=True)
            result = await self.session.exec(stmt)
            inserted_count = len(result.all())
            await self.session.commit()
            skipped_count = len(rows) - inserted_count
            if skipped_count > 0:
                logger.info(
                    "stock_prices_1m insert completed with duplicates skipped: "
                    "inserted=%s skipped=%s total=%s",
                    inserted_count,
                    skipped_count,
                    len(rows),
                )
            return inserted_count
        except SQLAlchemyError as bulk_error:
            await self.session.rollback()
            await self._pinpoint_and_log_bulk_error(rows, bulk_error)
            raise

    def _to_insert_row(self, record: StockPrice1m) -> dict[str, Any]:
        """StockPrice1mモデルをINSERT用辞書へ変換."""
        return {
            "ticker": record.ticker,
            "price_datetime": record.price_datetime,
            "open": record.open,
            "high": record.high,
            "low": record.low,
            "close": record.close,
            "volume": record.volume,
            "created_at": record.created_at,
        }

    def _build_insert_statement(
        self,
        rows: list[dict[str, Any]],
        *,
        with_returning: bool,
    ) -> Any:
        """ON CONFLICT付きINSERT文を構築."""
        table = cast(Any, StockPrice1m.__table__)  # type: ignore[attr-defined]
        stmt = (
            pg_insert(table)
            .values(rows)
            .on_conflict_do_nothing(
                index_elements=[table.c.ticker, table.c.price_datetime]
            )
        )
        if with_returning:
            return stmt.returning(table.c.id)
        return stmt

    async def _pinpoint_and_log_bulk_error(
        self,
        rows: list[dict[str, Any]],
        bulk_error: SQLAlchemyError,
    ) -> None:
        """バルクINSERT失敗時に原因レコードとSQLを特定してログ出力."""
        self._log_sql_error(
            rows=rows,
            error=bulk_error,
            context="bulk_insert_failed",
        )

        for row in rows:
            try:
                async with self.session.begin_nested():
                    stmt = self._build_insert_statement(
                        [row], with_returning=False
                    )
                    await self.session.exec(stmt)
            except SQLAlchemyError as row_error:
                self._log_sql_error(
                    rows=[row],
                    error=row_error,
                    context="failing_record_identified",
                )

    def _log_sql_error(
        self,
        *,
        rows: list[dict[str, Any]],
        error: SQLAlchemyError,
        context: str,
    ) -> None:
        """SQL実行エラーをSQL文とレコード内容付きでログ出力."""
        stmt = self._build_insert_statement(rows, with_returning=False)
        sql = str(
            stmt.compile(
                dialect=self.session.bind.dialect,
                compile_kwargs={"literal_binds": False},
            )
        )
        orig = getattr(error, "orig", None)
        diag = getattr(orig, "diag", None)
        logger.error(
            f"{INSERT_STOCK_DATA} error context=%s sql=%s params=%s "
            "sqlstate=%s detail=%s message=%s",
            context,
            sql,
            rows,
            getattr(orig, "sqlstate", None),
            getattr(diag, "message_detail", None),
            str(error),
        )


async def get_stock_price_1m_repository(
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> StockPrice1mRepository:
    """FastAPI DI用のStockPrice1mRepositoryファクトリ.

    Returns
    -------
        StockPrice1mRepository

    """
    return StockPrice1mRepository(session)
