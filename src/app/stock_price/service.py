"""株価データのサービスモジュール."""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated
from zoneinfo import ZoneInfo

import pandas as pd
from fastapi import Depends

from app.common.log_prefix import IMPORT_STOCK_DATA
from app.database.model.stock_price_1m import StockPrice1m
from app.database.model.ticker import Ticker
from app.database.repository.stock_price_1m_repository import (
    StockPrice1mRepository,
    get_stock_price_1m_repository,
)
from app.database.repository.ticker_repository import (
    TickerRepository,
    get_ticker_repository,
)
from app.stock_price.protocol import StockDataFetcher

JST = ZoneInfo("Asia/Tokyo")

# 1日あたりの最低レコード数 (東証: 前場150分+後場150分=約300件)
# これを下回る日は部分欠損とみなして再取得対象にする
MIN_RECORDS_PER_DAY = 200

logger = logging.getLogger(__name__)


class StockPriceService:
    """株価データに関するビジネスロジックを提供するサービス.

    Attributes
    ----------
        ticker_repo: Tickerリポジトリ
        price_repo: StockPrice1mリポジトリ

    """

    def __init__(
        self,
        ticker_repo: TickerRepository,
        price_repo: StockPrice1mRepository,
    ) -> None:
        """StockPriceServiceを初期化.

        Args:
        ----
            ticker_repo: Tickerリポジトリ
            price_repo: StockPrice1mリポジトリ

        """
        self.ticker_repo = ticker_repo
        self.price_repo = price_repo

    # --- パブリックメソッド ---

    async def process_all_tickers(
        self,
        fetcher: StockDataFetcher,
        days: int,
        specific_ticker: str | None = None,
        dry_run: bool = False,
    ) -> None:
        """全アクティブ銘柄の株価データを取得・取り込み.

        Args:
        ----
            fetcher: データ取得クライアント
            days: 取得する過去日数
            specific_ticker: 特定銘柄のみ処理する場合に指定
            dry_run: ドライランモード(DB書き込みなし)

        """
        tickers = await self.ticker_repo.get_active_tickers(
            specific_ticker=specific_ticker,
        )
        logger.info(f"Found {len(tickers)} active ticker(s) to process")

        for ticker_obj in tickers:
            try:
                await self.process_ticker(
                    fetcher=fetcher,
                    ticker_obj=ticker_obj,
                    days=days,
                    dry_run=dry_run,
                )
            except Exception as e:
                logger.error(
                    f"Error processing ticker {ticker_obj.ticker}: {e}",
                    exc_info=True,
                )
                continue

    async def process_ticker(
        self,
        fetcher: StockDataFetcher,
        ticker_obj: Ticker,
        days: int,
        dry_run: bool = False,
    ) -> int:
        """単一銘柄のデータを取得・取り込み.

        Args:
        ----
            fetcher: データ取得クライアント
            ticker_obj: 銘柄オブジェクト
            days: 取得する過去日数
            dry_run: ドライランモード(DB書き込みなし)

        Returns:
        -------
            取り込んだレコード数

        """
        ticker_symbol = ticker_obj.ticker
        logger.info(f"Processing {ticker_symbol}...")

        end_date = datetime.now(JST)
        start_date = (end_date - timedelta(days=days)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        missing_ranges = await self._get_missing_ranges(
            ticker_symbol, start_date, end_date
        )

        if not missing_ranges:
            logger.info(f"{ticker_symbol}: all data already imported, skipping")
            return 0

        logger.info(
            f"{ticker_symbol}: found {len(missing_ranges)} gap(s) to fetch"
        )

        total_imported = 0
        for range_start, range_end in missing_ranges:
            try:
                df = await fetcher.fetch_1m_data(
                    ticker=ticker_symbol,
                    start=range_start,
                    end=range_end,
                )

                if df.empty:
                    logger.warning(
                        f"{ticker_symbol}: no data returned for "
                        f"{range_start} to {range_end}"
                    )
                    continue

                if dry_run:
                    logger.info(
                        f"{ticker_symbol}: DRY RUN - "
                        f"would import {len(df)} records "
                        f"for range {range_start} to {range_end}"
                    )
                    total_imported += len(df)
                    continue

                imported_count = await self._import_price_data(
                    ticker=ticker_symbol,
                    df=df,
                )
                total_imported += imported_count
                logger.info(
                    f"{IMPORT_STOCK_DATA} {ticker_symbol}: "
                    f"imported {imported_count} records "
                    f"for range {range_start} to {range_end}"
                )

            except Exception as e:
                logger.error(
                    f"{ticker_symbol}: error fetching/importing range "
                    f"{range_start} to {range_end}: {e}"
                )
                continue

        logger.info(
            f"{ticker_symbol}: completed. "
            f"total imported: {total_imported} records"
        )
        return total_imported

    # --- プライベートメソッド ---

    async def _get_missing_ranges(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[tuple[datetime, datetime]]:
        """既存データと比較して欠損している日時範囲を計算.

        DBから既存データの日時範囲を取得し、
        まだ取得していない日の範囲を特定する。

        Args:
        ----
            ticker: 銘柄コード
            start_date: 開始日時
            end_date: 終了日時

        Returns:
        -------
            欠損している日時範囲のリスト

        """
        existing_ranges = await self.price_repo.get_date_ranges(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
        )

        if not existing_ranges:
            return [(start_date, end_date)]

        # count が閾値以上の日のみ「完了」とみなす
        complete_dates: set[date] = set()
        for min_dt, _, count in existing_ranges:
            if count >= MIN_RECORDS_PER_DAY:
                complete_dates.add(min_dt.date())
            else:
                logger.info(
                    f"{ticker}: {min_dt.date()} has only {count} records "
                    f"(threshold={MIN_RECORDS_PER_DAY}), will re-fetch"
                )

        # 欠損日を収集
        missing_dates: list[date] = []
        current_date = start_date.date()
        end_date_only = end_date.date()

        while current_date <= end_date_only:
            if current_date not in complete_dates:
                missing_dates.append(current_date)
            current_date += timedelta(days=1)

        if not missing_dates:
            return []

        # 連続する欠損日をマージ
        merged: list[tuple[datetime, datetime]] = []
        range_start_date = missing_dates[0]
        prev_date = missing_dates[0]

        for d in missing_dates[1:]:
            if d == prev_date + timedelta(days=1):
                prev_date = d
            else:
                merged.append(
                    self._to_datetime_range(range_start_date, prev_date)
                )
                range_start_date = d
                prev_date = d

        merged.append(self._to_datetime_range(range_start_date, prev_date))

        return merged

    async def _import_price_data(
        self,
        ticker: str,
        df: pd.DataFrame,
    ) -> int:
        """DataFrameから株価データをDBに一括登録.

        Args:
        ----
            ticker: 銘柄コード
            df: 株価データのDataFrame (index=datetime)

        Returns:
        -------
            登録したレコード数

        """
        if df.empty:
            logger.warning(f"{ticker}: empty DataFrame, nothing to import")
            return 0

        records = []
        for dt, row in df.iterrows():
            record = StockPrice1m(
                ticker=ticker,
                price_datetime=dt,
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=int(row["volume"]),
            )
            records.append(record)

        return await self.price_repo.bulk_insert(records)

    def _to_datetime_range(
        self,
        start: date,
        end: date,
    ) -> tuple[datetime, datetime]:
        """日付ペアをタイムゾーン付きdatetimeの範囲に変換."""
        return (
            datetime.combine(start, datetime.min.time()).replace(tzinfo=JST),
            datetime.combine(end, datetime.max.time()).replace(tzinfo=JST),
        )


async def get_stock_price_service(
    ticker_repo: Annotated[
        TickerRepository,
        Depends(get_ticker_repository),
    ],
    price_repo: Annotated[
        StockPrice1mRepository,
        Depends(get_stock_price_1m_repository),
    ],
) -> StockPriceService:
    """FastAPI DI用のStockPriceServiceファクトリ.

    Returns
    -------
        StockPriceService

    """
    return StockPriceService(
        ticker_repo=ticker_repo,
        price_repo=price_repo,
    )
