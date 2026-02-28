"""株価データ取得バッチジョブ.

yfinanceを使用して1分足の株価データを取得し、
データベースに取り込むバッチジョブ。
"""

import asyncio
import logging
from typing import Annotated

import typer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.common.log_prefix import LogPrefix
from app.database.database import async_engine
from app.database.repository import (
    StockPrice1mRepository,
    TickerRepository,
)
from app.infra.external.yfinance_fetcher import YFinanceFetcher
from app.settings.settings import get_settings
from app.stock_price.service import StockPriceService

app = typer.Typer()

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.batch_log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@app.command()
def main(
    days: Annotated[int | None, typer.Option(help="取得する過去日数")] = None,
    ticker: Annotated[str | None, typer.Option(help="特定銘柄のみ取得")] = None,
    dry_run: Annotated[
        bool,
        typer.Option(help="ドライランモード(DB書き込みなし)"),
    ] = False,
) -> None:
    """株価データを取得してDBに取り込む.

    Args:
    ----
        days: 取得する過去日数
        ticker: 特定銘柄のみ取得する場合に指定
        dry_run: ドライランモード

    """
    if days is None:
        days = settings.batch_lookback_days

    asyncio.run(fetch_stock_prices(days=days, ticker=ticker, dry_run=dry_run))


async def fetch_stock_prices(
    days: int,
    ticker: str | None,
    dry_run: bool,
) -> None:
    """株価データを非同期で取得・取り込み.

    Args:
    ----
        days: 取得する過去日数
        ticker: 特定銘柄のみ取得する場合に指定
        dry_run: ドライランモード

    """
    logger.info(
        f"{LogPrefix.BATCH_JOB} Starting with days={days}, "
        f"ticker={ticker}, dry_run={dry_run}"
    )

    async with AsyncSession(async_engine) as session:
        service = StockPriceService(
            ticker_repo=TickerRepository(session),
            price_repo=StockPrice1mRepository(session),
        )
        fetcher = YFinanceFetcher(
            max_retries=settings.batch_max_retries,
            retry_delay=settings.batch_retry_delay_seconds,
        )

        await service.process_all_tickers(
            fetcher=fetcher,
            days=days,
            specific_ticker=ticker,
            dry_run=dry_run,
        )

    logger.info(f"{LogPrefix.BATCH_JOB} Completed")


if __name__ == "__main__":
    app()
