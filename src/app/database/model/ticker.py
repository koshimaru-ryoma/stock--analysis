"""銘柄マスタモデルを定義するモジュール."""

from datetime import UTC, datetime

from sqlalchemy import BigInteger, Column, DateTime
from sqlmodel import Field, SQLModel


class Ticker(SQLModel, table=True):
    """銘柄マスタを表すデータベースモデル.

    Attributes
    ----------
        id: 自動採番ID(主キー)
        ticker: 銘柄コード (例: 8001.T, AAPL)
        name: 銘柄名 (例: Apple Inc.)
        is_active: 有効フラグ(True=データ取得対象)
        created_at: 登録日時
        updated_at: 更新日時

    """

    __tablename__ = "tickers"

    id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True),
    )
    ticker: str = Field(
        max_length=20,
        unique=True,
        index=True,
    )
    name: str | None = Field(
        max_length=200,
        default=None,
    )
    is_active: bool = Field(
        default=True,
        index=True,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
