"""データベースモデルを一括エクスポートするモジュール.

新しいモデルを追加する際は、ここにインポート文を1行追加するだけで
Alembicが自動的に検出します。

Example:
-------
    新しいモデル `User` を追加した場合:
    ```python
    from .user import User
    ```

"""

from .stock_price_1m import StockPrice1m

__all__ = ["StockPrice1m"]
