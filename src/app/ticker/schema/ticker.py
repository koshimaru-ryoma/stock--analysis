"""銘柄レスポンススキーマ."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TickerResponse(BaseModel):
    """銘柄レスポンススキーマ."""

    model_config = ConfigDict(from_attributes=True)

    ticker: str
    name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
