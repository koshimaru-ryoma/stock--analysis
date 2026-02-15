"""アプリケーション設定を管理するモジュール."""

from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション全体の設定を管理するクラス.

    環境変数から設定値を読み込み、データベース接続情報などを提供する。

    Attributes
    ----------
        environment: 実行環境(development, production等)
        postgres_host: PostgreSQLホスト名
        postgres_port: PostgreSQLポート番号
        postgres_user: PostgreSQLユーザー名
        postgres_password: PostgreSQLパスワード
        postgres_database: PostgreSQLデータベース名
        sql_log: SQLログの出力有無(デフォルト: False)

    """

    environment: str

    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_database: str

    sql_log: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def postgres_driver_url(self) -> str:
        """PostgreSQLの非同期接続URLを生成する.

        Returns
        -------
            str: asyncpg用のPostgreSQL接続URL

        """
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        )


@lru_cache
def get_settings() -> Settings:
    """アプリケーション設定のシングルトンインスタンスを取得する.

    LRUキャッシュにより同一インスタンスを再利用し、
    環境変数の読み込みコストを削減する。

    Returns
    -------
        Settings: アプリケーション設定オブジェクト

    """
    return Settings()
