"""リソースが見つからない場合の例外."""

from typing import Any


class NotFoundError(Exception):
    """リソースが見つからない場合の例外.

    Attributes
    ----------
        field: エラーとなったフィールド名
        value: エラーとなった値

    """

    def __init__(self, field: str, value: Any) -> None:
        """NotFoundErrorを初期化.

        Args:
        ----
            field: エラーとなったフィールド名
            value: エラーとなった値

        """
        self.field = field
        self.value = value
        super().__init__(f"{field}={value!r} not found")
