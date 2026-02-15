# syntax=docker/dockerfile:1.7

############################
# base
############################
FROM python:3.13-slim-bookworm AS base
SHELL ["sh", "-exc"]
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /src


############################
# deps (uv is used only here)
############################
FROM base AS deps
SHELL ["sh", "-exc"]

# ビルドが必要な依存が出るケースに備える（不要なら削ってOK）
RUN <<'EOT'
apt-get update -qy
apt-get install -qyy --no-install-recommends \
  build-essential \
  pkg-config \
  ca-certificates
rm -rf /var/lib/apt/lists/*
EOT

# uv binaries
COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.13 \
    UV_PROJECT_ENVIRONMENT=/.venv

# 依存だけ先に（キャッシュ効かせる）
COPY src/pyproject.toml src/uv.lock ./

# 本番/ステージング用：dev依存なし
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project


############################
# local (runtime WITH uv, for docker-based development)
############################
FROM base AS local
SHELL ["sh", "-exc"]

# localは uv を入れて依存追加や sync を楽にする
COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.13 \
    UV_PROJECT_ENVIRONMENT=/.venv \
    PATH="/.venv/bin:$PATH" \
    ENVIRONMENT=local

# local は dev 依存込みで入れる（lint/test等をdev dependenciesに置く前提）
COPY src/pyproject.toml src/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

EXPOSE 8000
EXPOSE 5678
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]


############################
# dev (staging) runtime (NO uv)
############################
FROM base AS dev
SHELL ["sh", "-exc"]

# depsで作った venv を持ち込む（uvは持ち込まない）
COPY --from=deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH" \
    ENVIRONMENT=dev

# staging なのでコードはイメージに含める（マウントしない想定）
COPY src/alembic.ini ./
COPY src/app ./app

EXPOSE 8000
# staging は prod に寄せて reload なし。ログレベル等は環境変数で調整推奨
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


############################
# prod runtime (NO uv, smaller & safer)
############################
FROM base AS prod
SHELL ["sh", "-exc"]

# non-root 推奨（任意）
RUN adduser --disabled-password --gecos "" appuser
USER appuser

COPY --from=deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH" \
    ENVIRONMENT=prod

COPY src/alembic.ini ./
COPY src/app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]