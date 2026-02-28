"""1分足の株価データモデルを定義するモジュール."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel


class StockPrice1m(SQLModel, table=True):
    """1分足の株価データを表すデータベースモデル.

    Attributes
    ----------
        id: 自動採番ID(主キー)
        ticker: 銘柄コード (例: 8001.T)
        price_datetime: 日時 (例: 2024-02-15 09:00:00+09)
        open: 始値 (例: 4500.00)
        high: 高値 (例: 4510.00)
        low: 安値 (例: 4495.00)
        close: 終値 (例: 4505.00)
        volume: 出来高 (例: 150000)
        created_at: 登録日時

    """

    __tablename__ = "stock_prices_1m"
    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "price_datetime",
            name="uq_stock_prices_1m_ticker_price_datetime",
        ),
    )

    id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True),
    )
    ticker: str = Field(
        max_length=20,
        index=True,
    )
    price_datetime: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    open: Decimal = Field(
        max_digits=10,
        decimal_places=2,
    )
    high: Decimal = Field(
        max_digits=10,
        decimal_places=2,
    )
    low: Decimal = Field(
        max_digits=10,
        decimal_places=2,
    )
    close: Decimal = Field(
        max_digits=10,
        decimal_places=2,
    )
    volume: int = Field(
        sa_column=Column(BigInteger, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
