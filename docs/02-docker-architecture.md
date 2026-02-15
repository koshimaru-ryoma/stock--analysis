# Docker アーキテクチャ

本ドキュメントでは、プロジェクトで使用している Docker のマルチステージビルド構成と、各環境（local、dev、prod）の違いについて説明します。

## 目次

1. [マルチステージビルドの概要](#マルチステージビルドの概要)
2. [各ステージの詳細](#各ステージの詳細)
3. [環境別の使い分け](#環境別の使い分け)
4. [uv の活用](#uvの活用)
5. [ベストプラクティス](#ベストプラクティス)

## マルチステージビルドの概要

本プロジェクトの `Dockerfile` は、以下の4つのステージで構成されています：

```
base (基盤イメージ)
  ↓
deps (依存関係のビルド) ─→ local (開発環境)
  ↓                        ↓
  ↓                     dev (ステージング環境)
  ↓                        ↓
  └─────────────────→ prod (本番環境)
```

### マルチステージビルドのメリット

1. **イメージサイズの削減**: 本番環境には不要なビルドツールを含めない
2. **セキュリティ向上**: 各環境に必要最小限のツールのみをインストール
3. **ビルド時間の短縮**: レイヤーキャッシュを効果的に活用
4. **環境の明確な分離**: 開発・ステージング・本番で適切な設定を適用

## 各ステージの詳細

### 1. base ステージ

すべてのステージの基盤となるイメージです。

```dockerfile
FROM python:3.13-slim-bookworm AS base
SHELL ["sh", "-exc"]
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /src
```

**設定内容**:
- **ベースイメージ**: `python:3.13-slim-bookworm` - 軽量なDebianベース
- **PYTHONDONTWRITEBYTECODE=1**: `.pyc` ファイルを生成しない（コンテナでは不要）
- **PYTHONUNBUFFERED=1**: 標準出力をバッファリングせず即座に表示（ログ確認に有用）
- **WORKDIR**: `/src` を作業ディレクトリに設定

### 2. deps ステージ

依存パッケージをビルド・インストールするステージです。

```dockerfile
FROM base AS deps
# ビルドツールのインストール
RUN apt-get update -qy && \
    apt-get install -qyy --no-install-recommends \
      build-essential pkg-config ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# uv のコピー
COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /uvx /bin/

# 依存関係のインストール（本番用: dev依存なし）
COPY src/pyproject.toml src/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project
```

**ポイント**:
- **ビルドツール**: C拡張を含むパッケージ（asyncpg等）のビルドに必要
- **uv のコピー**: 公式イメージから uv バイナリをコピー
- **キャッシュマウント**: `--mount=type=cache` で uv のキャッシュを保持し、再ビルドを高速化
- **--no-dev**: 本番環境では開発用パッケージを除外
- **--no-install-project**: プロジェクト自体はインストールせず、依存関係のみ

### 3. local ステージ（開発環境）

開発者がローカルで使用するステージです。

```dockerfile
FROM base AS local
# uv を含める（開発中に依存追加できるように）
COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.13 \
    UV_PROJECT_ENVIRONMENT=/.venv \
    PATH="/.venv/bin:$PATH" \
    ENVIRONMENT=local

# dev 依存込みでインストール
COPY src/pyproject.toml src/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

EXPOSE 8000 5678
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", \
     "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--reload", "--log-level", "debug"]
```

**特徴**:
- **uv 同梱**: コンテナ内で `uv add` や `uv sync` を実行可能
- **dev 依存込み**: `ruff`, `mypy`, `debugpy` などをインストール
- **--reload**: ファイル変更を検知して自動リロード
- **debugpy**: ポート5678でリモートデバッグを待ち受け
- **ボリュームマウント**: `docker-compose.yml` で `/src` をマウントし、コード変更を即反映

### 4. dev ステージ（ステージング環境）

ステージング環境で使用するステージです。

```dockerfile
FROM base AS dev
# uvは含めない（イメージサイズ削減）
COPY --from=deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH" ENVIRONMENT=dev

# コードをイメージに含める
COPY src/alembic.ini ./
COPY src/app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**特徴**:
- **uv なし**: 依存追加は不要なため除外
- **コードをコピー**: ボリュームマウントせず、イメージに含める
- **reload なし**: 本番に近い動作で検証

### 5. prod ステージ（本番環境）

本番環境で使用するステージです。

```dockerfile
FROM base AS prod
# 非rootユーザーで実行
RUN adduser --disabled-password --gecos "" appuser
USER appuser

COPY --from=deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH" ENVIRONMENT=prod

COPY src/alembic.ini ./
COPY src/app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**特徴**:
- **非rootユーザー**: セキュリティベストプラクティス
- **最小構成**: ビルドツールや開発ツールを一切含まない
- **イメージサイズ最小化**: 必要最小限のファイルのみ

## 環境別の使い分け

### 開発環境 (local)

**使用タイミング**: ローカルマシンでの開発時

**起動方法**:
```bash
docker compose up
```

**特徴**:
- ホットリロード有効
- デバッガー有効
- ボリュームマウントでコード変更即反映
- 開発ツール（linter、formatter）利用可能

### ステージング環境 (dev)

**使用タイミング**: 本番デプロイ前の検証

**ビルド方法**:
```bash
docker build --target dev -t myapp:dev .
```

**特徴**:
- 本番に近い設定
- コードはイメージに含まれる
- パフォーマンス検証に適している

### 本番環境 (prod)

**使用タイミング**: 本番デプロイ

**ビルド方法**:
```bash
docker build --target prod -t myapp:prod .
```

**特徴**:
- 最小サイズ
- セキュアな設定（非root）
- 開発ツール一切なし

## uv の活用

### uv とは

[uv](https://github.com/astral-sh/uv) は Rust 製の高速な Python パッケージマネージャーです。

**従来の pip との比較**:
- **速度**: 10〜100倍高速なインストール
- **ロックファイル**: `uv.lock` で再現可能なビルド
- **依存解決**: より高速で正確な依存関係の解決

### uv の主要コマンド

```bash
# 依存関係の追加
uv add fastapi

# 開発用依存の追加
uv add --dev ruff

# 依存関係のインストール
uv sync

# ロックファイルの更新
uv lock

# パッケージの削除
uv remove package-name
```

### Docker での uv 活用

**キャッシュの活用**:
```dockerfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked
```
- `--mount=type=cache` で uv のダウンロードキャッシュを保持
- 2回目以降のビルドが大幅に高速化

**環境変数の設定**:
```dockerfile
ENV UV_LINK_MODE=copy \           # ハードリンクではなくコピー（Docker向け）
    UV_COMPILE_BYTECODE=1 \        # .pyc ファイルを事前コンパイル
    UV_PYTHON_DOWNLOADS=never \    # Pythonの自動ダウンロードを無効化
    UV_PYTHON=python3.13 \         # 使用する Python バージョン
    UV_PROJECT_ENVIRONMENT=/.venv  # 仮想環境のパス
```

## ベストプラクティス

### 1. レイヤーキャッシュの最適化

依存関係ファイル（`pyproject.toml`, `uv.lock`）を先にコピーし、アプリケーションコードは後でコピーすることで、コード変更時のビルドを高速化：

```dockerfile
# ✅ 良い例
COPY src/pyproject.toml src/uv.lock ./
RUN uv sync --locked
COPY src/app ./app

# ❌ 悪い例
COPY src ./
RUN uv sync --locked
```

### 2. .dockerignore の活用

不要なファイルをコピーしないよう `.dockerignore` を設定：

```
__pycache__/
*.pyc
*.pyo
.git/
.venv/
node_modules/
```

### 3. 非rootユーザーでの実行

本番環境では非rootユーザーで実行し、セキュリティリスクを軽減：

```dockerfile
RUN adduser --disabled-password --gecos "" appuser
USER appuser
```

### 4. マルチステージビルドの活用

開発・ステージング・本番で適切なステージを使い分け：

```bash
# 開発
docker compose up  # local ステージ

# ステージング
docker build --target dev -t app:staging .

# 本番
docker build --target prod -t app:prod .
```

### 5. 環境変数の管理

環境ごとに異なる設定は環境変数で管理：

```yaml
# docker-compose.yml
env_file:
  - ./containers/api/api.env
```

## まとめ

本プロジェクトの Docker 構成は、マルチステージビルドと uv を活用することで：

- ✅ 高速なビルドとインストール
- ✅ 環境ごとに最適化されたイメージ
- ✅ セキュアな本番環境
- ✅ 効率的な開発体験

を実現しています。
