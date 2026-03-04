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

# Alembicのautogenerateがモデルを検出するための副作用インポート。
# migration/env.py で `import app.database.model` を実行した際に
# このファイルが評価され、各モデルが SQLModel.metadata に登録される。
# 再エクスポートが目的ではないため F401(未使用インポート)を無視する。
from .stock_price_1m import StockPrice1m  # noqa: F401
from .ticker import Ticker  # noqa: F401
