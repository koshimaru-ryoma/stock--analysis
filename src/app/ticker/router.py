"""銘柄APIのルーター定義."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.database.repository.ticker_repository import (
    TickerRepository,
    get_ticker_repository,
)
from app.ticker.schema import TickerResponse

router = APIRouter(prefix="/tickers", tags=["tickers"])


@router.get("", response_model=list[TickerResponse])
async def get_tickers(
    repo: Annotated[TickerRepository, Depends(get_ticker_repository)],
) -> list[TickerResponse]:
    """登録済みの銘柄一覧を返す."""
    tickers = await repo.get_all()
    return [TickerResponse.model_validate(t) for t in tickers]
