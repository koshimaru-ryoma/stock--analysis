"""株価データ取得のプロトコル定義."""

from datetime import datetime
from typing import Protocol

import pandas as pd


class StockDataFetcher(Protocol):
    """株価データ取得のインターフェース."""

    async def fetch_1m_data(
        self,
        ticker: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """1分足データを取得."""
        ...
