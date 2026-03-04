"""銘柄ごとの株価データのスキーマ."""

from pydantic import BaseModel

from app.stock_price.schema.dto.stock_price_data_point import (
    StockPriceDataPoint,
)


class TickerPriceData(BaseModel):
    """銘柄ごとの株価データ."""

    ticker_id: int
    ticker: str
    name: str | None
    data: list[StockPriceDataPoint]
