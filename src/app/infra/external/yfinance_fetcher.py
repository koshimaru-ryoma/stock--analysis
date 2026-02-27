"""yfinance API ラッパーモジュール."""

import asyncio
import logging
import time
from datetime import datetime

import pandas as pd
import yfinance as yf

from app.common.log_prefix import LogPrefix

logger = logging.getLogger(__name__)


class YFinanceFetcher:
    """yfinance ライブラリのラッパークラス.

    エラーハンドリングとレート制限を含むyfinanceのラッパー。

    Attributes
    ----------
        max_retries: 最大リトライ回数
        retry_delay: リトライ間隔(秒)

    """

    def __init__(self, max_retries: int = 3, retry_delay: int = 5) -> None:
        """YFinanceFetcherを初期化.

        Args:
        ----
            max_retries: 最大リトライ回数
            retry_delay: リトライ間隔(秒)

        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def fetch_1m_data(
        self,
        ticker: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """1分足データを取得.

        Args:
        ----
            ticker: 銘柄コード (例: "8001.T")
            start: 開始日時 (UTC)
            end: 終了日時 (UTC)

        Returns:
        -------
            DataFrame with columns: open, high, low, close, volume
            Index: datetime (timezone-aware)

        Raises:
        ------
            Exception: 全リトライ失敗時

        """
        return await asyncio.to_thread(
            self._fetch_1m_data_sync,
            ticker,
            start,
            end,
        )

    def _fetch_1m_data_sync(
        self,
        ticker: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """同期版のデータ取得とリトライロジック.

        Args:
        ----
            ticker: 銘柄コード
            start: 開始日時
            end: 終了日時

        Returns:
        -------
            DataFrame with columns: open, high, low, close, volume

        Raises:
        ------
            Exception: 全リトライ失敗時

        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"{LogPrefix.FETCH_STOCK_DATA} {ticker} "
                    f"interval=1m start={start} end={end} "
                    f"(attempt {attempt}/{self.max_retries})"
                )

                ticker_obj = yf.Ticker(ticker)
                df = ticker_obj.history(
                    start=start,
                    end=end,
                    interval="1m",
                    auto_adjust=False,
                )

                df = self._validate_and_clean(df, ticker)

                logger.debug(f"{ticker} fetched {len(df)} records")
                return df

            except Exception as e:
                logger.warning(f"{ticker} attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    logger.info(
                        f"{ticker} retrying in {self.retry_delay} seconds..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"{ticker} all retries exhausted")
                    raise

        # 型チェッカーのために追加(実際には到達しない)
        return pd.DataFrame()

    def _validate_and_clean(
        self, df: pd.DataFrame, ticker: str
    ) -> pd.DataFrame:
        """取得データの検証とクリーニング.

        Args:
        ----
            df: yfinanceから取得したDataFrame
            ticker: 銘柄コード

        Returns:
        -------
            クリーニング済みのDataFrame

        """
        if df.empty:
            return df

        if df.index.tz is None:
            logger.warning(f"{ticker}: DataFrame has no timezone, assuming UTC")
            df.index = df.index.tz_localize("UTC")

        df = df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )

        needed_cols = ["open", "high", "low", "close", "volume"]
        df = df[needed_cols]

        original_len = len(df)
        df = df.dropna()
        if len(df) < original_len:
            logger.warning(
                f"{ticker}: dropped {original_len - len(df)} rows with NaN values"
            )

        return df
