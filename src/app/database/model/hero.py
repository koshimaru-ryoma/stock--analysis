"""ヒーローのデータモデルを定義するモジュール."""

from sqlmodel import Field, SQLModel


class Hero(SQLModel, table=True):
    """ヒーローを表すデータベースモデル.

    Attributes
    ----------
        id: ヒーローの一意識別子(主キー)
        name: ヒーローの公開名(インデックス付き)
        age: ヒーローの年齢(オプショナル、インデックス付き)
        secret_name: ヒーローの本名

    """

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    secret_name: str
