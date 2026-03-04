"""株価取得クエリパラメータのスキーマ."""

from datetime import date

from pydantic import BaseModel, field_validator, model_validator


class StockPriceQuery(BaseModel):
    """株価取得のクエリパラメータ."""

    ticker_ids: list[int]
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("ticker_ids")
    @classmethod
    def deduplicate(cls, v: list[int]) -> list[int]:
        """重複IDを除去しつつ入力順を維持."""
        seen: set[int] = set()
        return [x for x in v if not (x in seen or seen.add(x))]  # type: ignore[func-returns-value]

    @model_validator(mode="after")
    def validate_date_order(self) -> StockPriceQuery:
        """start_date <= end_date を保証."""
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        ):
            raise ValueError(
                "start_date must be before or equal to end_date"
            )
        return self
