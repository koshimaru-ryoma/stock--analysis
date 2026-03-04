"""例外レスポンスのスキーマ."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """エラーレスポンス."""

    detail: str
