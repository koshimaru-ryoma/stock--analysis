# FastAPI Starter プロジェクト

FastAPI、uv、PostgreSQL、Docker を使用したモダンな Web API スターターテンプレートです。

## 🚀 特徴

- **FastAPI**: 高速で型安全な Python Web フレームワーク
- **uv**: Rust製の超高速パッケージマネージャー
- **SQLModel**: Pydantic ベースの ORM
- **Alembic**: データベースマイグレーション管理
- **PostgreSQL**: 信頼性の高いリレーショナルデータベース
- **Docker**: コンテナ化された開発・本番環境
- **マルチステージビルド**: 環境ごとに最適化された Docker イメージ
- **リモートデバッグ**: debugpy による VSCode デバッグ対応
- **Linter/Formatter**: ruff による高速なコード品質管理
- **型チェック**: mypy による静的型チェック

## 📁 プロジェクト構成

```
.
├── containers/              # Docker関連ファイル
│   ├── api/
│   │   ├── Dockerfile      # APIサーバーのマルチステージビルド
│   │   └── api.env         # API環境変数
│   └── postgres/
│       ├── db.env          # DB環境変数
│       └── volumes/        # DBデータ永続化
├── src/                    # アプリケーションソース
│   ├── app/
│   │   ├── main.py         # FastAPIエントリーポイント
│   │   ├── database/       # DB設定とモデル
│   │   ├── migration/      # Alembicマイグレーション
│   │   └── settings/       # アプリケーション設定
│   ├── pyproject.toml      # プロジェクト設定
│   └── uv.lock            # 依存関係ロックファイル
├── docs/                   # ドキュメント
│   ├── 01-setup.md        # セットアップ手順
│   └── 02-docker-architecture.md  # Docker構成説明
├── docker-compose.yml      # Docker Compose設定
└── trash/                  # 参考資料
    └── docker-compose.init.yml  # 初回セットアップ用
```

## 🏃 クイックスタート

### 前提条件

- Docker Desktop がインストールされていること

### 1. コンテナの起動

```bash
# コンテナのビルドと起動
docker compose up --build
```

### 2. 動作確認

ブラウザで以下の URL にアクセス：

- **API ルート**: http://localhost:9999/
- **API ドキュメント (Swagger)**: http://localhost:9999/docs
- **API ドキュメント (ReDoc)**: http://localhost:9999/redoc

### 3. 開発開始

コードを変更すると、自動的にリロードされます（ホットリロード有効）。

## 📚 ドキュメント

詳細な手順やアーキテクチャについては、以下のドキュメントを参照してください：

1. **[セットアップガイド](01-setup.md)** - 環境構築とAPIコンテナの立ち上げ手順
2. **[Dockerアーキテクチャ](02-docker-architecture.md)** - マルチステージビルドとuv活用方法

## 🛠️ 開発コマンド

### コンテナ操作

```bash
# コンテナの起動（バックグラウンド）
docker compose up -d

# コンテナの停止
docker compose stop

# コンテナの削除
docker compose down

# コンテナに入る
docker compose exec api bash
```

### コード品質管理

```bash
# Linterチェック
docker compose exec api ruff check .

# 自動フォーマット
docker compose exec api ruff format .

# 型チェック
docker compose exec api mypy app
```

### データベース操作

```bash
# マイグレーションファイルの生成
docker compose exec api alembic revision --autogenerate -m "migration message"

# マイグレーションの適用
docker compose exec api alembic upgrade head

# マイグレーションのロールバック
docker compose exec api alembic downgrade -1

# PostgreSQLに接続
docker compose exec postgres psql -U admin -d sample
```

### パッケージ管理

```bash
# パッケージの追加
docker compose exec api uv add <package-name>

# 開発用パッケージの追加
docker compose exec api uv add --dev <package-name>

# パッケージの削除
docker compose exec api uv remove <package-name>

# 依存関係の同期
docker compose exec api uv sync
```

## 🌍 環境設定

### API サーバー設定 (`containers/api/api.env`)

```env
ENVIRONMENT=local
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DATABASE=sample
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
SQL_LOG=True
```

### データベース設定 (`containers/postgres/db.env`)

```env
POSTGRES_DB=sample
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
```

## 🔍 デバッグ

### VSCode でのリモートデバッグ

1. VSCode に Python 拡張機能をインストール
2. `.vscode/launch.json` に以下を追加：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Remote Attach",
      "type": "debugpy",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}/src",
          "remoteRoot": "/src"
        }
      ]
    }
  ]
}
```

3. `docker compose up` でコンテナを起動
4. VSCode でブレークポイントを設定
5. デバッグビューから "Python: Remote Attach" を実行

## 📦 使用技術スタック

| カテゴリ | 技術 | バージョン |
|---------|------|-----------|
| 言語 | Python | 3.13 |
| Web フレームワーク | FastAPI | 0.128+ |
| ASGI サーバー | Uvicorn | 0.40+ |
| ORM | SQLModel | 0.0.31+ |
| データベースドライバ | asyncpg | 0.30+ |
| マイグレーション | Alembic | 1.18+ |
| 設定管理 | Pydantic Settings | 2.12+ |
| パッケージマネージャー | uv | 0.8.17 |
| Linter/Formatter | Ruff | 0.14+ |
| 型チェッカー | mypy | 1.14+ |
| デバッガー | debugpy | 1.8+ |
| データベース | PostgreSQL | 17 |
| コンテナ | Docker | - |

## 🏗️ アーキテクチャ

### マルチステージビルド

本プロジェクトは、環境ごとに最適化された Docker イメージを提供します：

- **local**: 開発環境（ホットリロード、デバッガー、開発ツール込み）
- **dev**: ステージング環境（本番に近い構成で検証）
- **prod**: 本番環境（最小サイズ、セキュア設定）

詳細は [Dockerアーキテクチャ](02-docker-architecture.md) を参照してください。

### ディレクトリ構成の設計思想

```
src/app/
├── main.py           # アプリケーションのエントリーポイント
├── database/         # データベース関連（モデル、接続設定）
├── migration/        # Alembicマイグレーション
└── settings/         # アプリケーション設定（環境変数の読み込み）
```

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成


## 🙏 謝辞

- [FastAPI](https://fastapi.tiangolo.com/) - モダンで高速な Web フレームワーク
- [uv](https://github.com/astral-sh/uv) - 超高速 Python パッケージマネージャー
- [SQLModel](https://sqlmodel.tiangolo.com/) - Pydantic ベースの ORM
- [Ruff](https://github.com/astral-sh/ruff) - 高速な Python Linter/Formatter
