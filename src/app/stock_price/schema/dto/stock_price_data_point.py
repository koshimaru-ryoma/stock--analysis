"""1分足株価データポイントのスキーマ."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class StockPriceDataPoint(BaseModel):
    """1分足の株価データポイント."""

    model_config = ConfigDict(from_attributes=True)

    price_datetime: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
