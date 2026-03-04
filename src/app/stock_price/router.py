"""株価APIのルーター定義."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.exceptions.schema import ErrorResponse
from app.stock_price.schema.request.stock_price_query import StockPriceQuery
from app.stock_price.schema.response.ticker_price_data import TickerPriceData
from app.stock_price.service import StockPriceService, get_stock_price_service

router = APIRouter(prefix="/stock-prices", tags=["stock-prices"])


@router.get(
    "",
    response_model=list[TickerPriceData],
    responses={404: {"model": ErrorResponse}},
)
async def get_stock_prices(
    query: Annotated[StockPriceQuery, Query()],
    service: Annotated[StockPriceService, Depends(get_stock_price_service)],
) -> list[TickerPriceData]:
    """指定銘柄・日付範囲の1分足株価データを返す.

    Args:
    ----
        query: クエリパラメータ(ticker_ids, start_date, end_date)
        service: 株価サービス

    Returns:
    -------
        銘柄ごとの1分足データのリスト

    """
    return await service.get_ticker_price_data(
        ticker_ids=query.ticker_ids,
        start_date=query.start_date,
        end_date=query.end_date,
    )
