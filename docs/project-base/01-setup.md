# FastAPI と uv を使った開発環境のセットアップ

本ドキュメントでは、FastAPI と uv（Pythonパッケージマネージャー）を使用した開発環境の構築手順を説明します。

## 目次

1. [前提条件](#前提条件)
2. [プロジェクト構成](#プロジェクト構成)
3. [初回セットアップ](#初回セットアップ)
4. [開発環境の起動](#開発環境の起動)
5. [動作確認](#動作確認)
6. [トラブルシューティング](#トラブルシューティング)

## 前提条件

- Docker Desktop がインストールされていること

## プロジェクト構成

```
.
├── containers/
│   ├── api/
│   │   ├── Dockerfile          # API サーバーのマルチステージビルド定義
│   │   └── api.env             # API サーバーの環境変数
│   └── postgres/
│       ├── db.env              # PostgreSQL の環境変数
│       └── volumes/            # データベースの永続化領域
├── src/
│   ├── app/
│   │   ├── main.py             # FastAPI アプリケーションのエントリーポイント
│   │   ├── database/           # データベース関連
│   │   ├── migration/          # Alembic マイグレーション
│   │   └── settings/           # アプリケーション設定
│   ├── pyproject.toml          # プロジェクト設定と依存関係
│   └── uv.lock                 # 依存関係のロックファイル
├── docker-compose.yml          # Docker Compose 設定
└── trash/
    └── docker-compose.init.yml # 初回セットアップ用（参考）
```

## 初回セットアップ

### 方法1: 既存プロジェクトのセットアップ（推奨）

既に `pyproject.toml` と `uv.lock` が存在する場合は、以下のコマンドで環境を構築できます。

```bash
# コンテナのビルド
docker compose build

# コンテナの起動
docker compose up
```

起動後、http://localhost:9999 にアクセスして動作を確認できます。

### 方法2: ゼロから新規プロジェクトを作成する場合

新規にプロジェクトを作成する場合は、以下の手順で環境を構築します。

#### 1. 初期化用 Dockerfile の作成

`containers/api/Dockerfile.init` を作成します：

```dockerfile
FROM python:3.13-slim-bookworm
SHELL ["sh", "-exc"]

# uv のインストール
COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.13 \
    UV_PROJECT_ENVIRONMENT=/.venv

WORKDIR /src
```

#### 2. 初期化スクリプトの実行

```bash
# 初回セットアップを実行
docker compose -f trash/docker-compose.init.yml run --rm init
```

このコマンドにより、以下のファイルが自動生成されます：

- `src/pyproject.toml` - プロジェクト設定ファイル
- `src/uv.lock` - 依存関係のロックファイル
- `src/app/main.py` - FastAPI アプリケーションの雛形
- `src/app/__init__.py` - Python パッケージ定義

#### 3. 依存パッケージの追加（必要に応じて）

コンテナ内で追加のパッケージをインストールする場合：

```bash
# コンテナに入る
docker compose exec -it api bash

# パッケージの追加例
uv add sqlmodel asyncpg alembic pydantic-settings

# 開発用パッケージの追加例
uv add --dev ruff mypy debugpy
```

## 開発環境の起動

### コンテナの起動

```bash
# バックグラウンドで起動
docker compose up -d

# フォアグラウンドで起動（ログをリアルタイムで確認）
docker compose up
```

起動すると、以下のサービスが利用可能になります：

| サービス | ポート | 説明 |
|---------|--------|------|
| API サーバー | 9999 | FastAPI アプリケーション |
| Debugpy | 5678 | リモートデバッグ用ポート |
| PostgreSQL | 15432 | データベース |

### コンテナの停止

```bash
# 停止（コンテナは保持）
docker compose stop

# 停止してコンテナを削除
docker compose down
```

### コンテナの再ビルド

`pyproject.toml` や `Dockerfile` を変更した場合は、再ビルドが必要です：

```bash
# 停止中の場合
docker compose build

# 起動中の場合（停止 → 再ビルド → 起動）
docker compose up --build
```

## 動作確認

### 1. API のヘルスチェック

ブラウザまたは curl で以下にアクセス：

```bash
curl http://localhost:9999/
```

現在の設定情報が JSON 形式で返却されれば成功です。

### 2. API ドキュメントの確認

FastAPI は自動的に API ドキュメントを生成します：

- Swagger UI: http://localhost:9999/docs
- ReDoc: http://localhost:9999/redoc

### 3. データベース接続の確認

PostgreSQL に接続してデータを確認：

```bash
# ホストから接続
psql -h localhost -p 15432 -U admin -d sample

# コンテナ経由で接続
docker compose exec postgres psql -U admin -d sample
```

パスワードは `containers/postgres/db.env` に定義されています（デフォルト: `admin`）。

### 4. ログの確認

```bash
# すべてのコンテナのログを表示
docker compose logs

# API サーバーのログのみ表示
docker compose logs api

# リアルタイムでログを追跡
docker compose logs -f api
```

## トラブルシューティング

### コンテナが起動しない

```bash
# コンテナの状態を確認
docker compose ps

# エラーログを確認
docker compose logs api



# クリーンビルド
docker compose down -v
docker compose build --no-cache
docker compose up
```

### 依存関係の不整合

```bash
# コンテナ内で uv lock を再実行
docker compose exec api uv lock

# 再ビルド
docker compose up --build
```

### データベース接続エラー

- `containers/api/api.env` と `containers/postgres/db.env` の設定が一致しているか確認
- PostgreSQL コンテナが起動しているか確認: `docker compose ps postgres`

## 開発用コマンド

### コンテナに入る

```bash
docker compose exec api bash
```

### Linter の実行

```bash
docker compose exec api ruff check .
docker compose exec api ruff format .
```

### 型チェックの実行

```bash
docker compose exec api mypy app
```

### マイグレーションの実行

```bash
# マイグレーションファイルの自動生成
docker compose exec api alembic revision --autogenerate -m "migration message"

# マイグレーションの適用
docker compose exec api alembic upgrade head
```

## 次のステップ

- [データベース設計とマイグレーション](02-database.md)（作成予定）

