# Alembic データベースマイグレーション

本ドキュメントでは、Alembic を使用したデータベーススキーマのマイグレーション管理について説明します。

## 目次

1. [Alembic とは](#alembic-とは)
2. [プロジェクト構成](#プロジェクト構成)
3. [基本コマンド](#基本コマンド)
4. [マイグレーションのワークフロー](#マイグレーションのワークフロー)
5. [応用コマンド](#応用コマンド)
6. [トラブルシューティング](#トラブルシューティング)

## Alembic とは

Alembic は SQLAlchemy のマイグレーションツールです。データベーススキーマの変更をバージョン管理し、チームでのスキーマ変更を安全に管理できます。

### 本プロジェクトの特徴

- **非同期対応**: `asyncpg` ドライバを使用した非同期マイグレーション
- **SQLModel 統合**: SQLModel のモデル定義から自動生成
- **環境変数管理**: `.env` ファイルから DB 接続情報を読み込み
- **日時ベースの命名**: マイグレーションファイルに日時を含める

## プロジェクト構成

### ディレクトリ構造

```
src/
├── alembic.ini                      # Alembic のメイン設定ファイル
└── app/
    ├── database/
    │   └── model/
    │       └── hero.py              # SQLModel モデル定義
    └── migration/                   # マイグレーションディレクトリ
        ├── env.py                   # マイグレーション環境設定
        ├── script.py.mako           # マイグレーションファイルのテンプレート
        └── versions/                # マイグレーションファイルの保存先
            └── 2026_01_26_2018-4390378ebd41_create_hero_table.py
```

### コンテナ内のパス

| 環境 | マウント先 | Working Directory | alembic.ini の場所 |
|------|-----------|-------------------|-------------------|
| Docker Compose | `/src` | `/src` | `/src/alembic.ini` |
| Dev Container (VSCode) | `/workspace` | `/workspace` | `/workspace/src/alembic.ini` |

**重要:** Alembic コマンドは `alembic.ini` があるディレクトリ（`/src` または `/workspace/src`）で実行する必要があります。

### 重要ファイルの役割

| ファイル | 役割 |
|---------|------|
| `alembic.ini` | Alembic の設定（ファイル名形式、ログ設定など） |
| `env.py` | 環境変数からの DB URL 読み込み、SQLModel メタデータの登録 |
| `script.py.mako` | 新規マイグレーションファイルのテンプレート |
| `versions/*.py` | 実際のマイグレーションスクリプト（自動生成 + 手動調整） |

## 基本コマンド

すべてのコマンドは **コンテナ内** で実行します。

### 重要: 実行ディレクトリについて

Alembic コマンドは `/src` ディレクトリで実行する必要があります。

```bash
# コンテナに入る
docker compose exec api bash

# /src に移動（alembic.ini がある場所）
cd /src
```

または、`docker compose exec` の working directory は既に `/src` なので、直接コマンドを実行できます:

```bash
# コンテナ外から直接実行（推奨）
docker compose exec api alembic upgrade head
```

### Dev Container 環境の場合

VSCode Dev Container では `/workspace` にマウントされますが、`alembic.ini` は `/workspace/src/` にあります。

以下のいずれかの方法で実行してください:

**方法1: `/src` に移動してから実行（推奨）**

```bash
cd /src
alembic upgrade head
```

**方法2: 設定ファイルのパスを明示**

```bash
# /workspace から実行する場合
alembic -c /workspace/src/alembic.ini upgrade head
```

**方法3: Docker Compose 経由（最も確実）**

```bash
# ホストまたは /workspace から実行
docker compose exec api alembic upgrade head
```

### 1. マイグレーションファイルの自動生成

モデルの変更を検出して、マイグレーションファイルを自動生成します。

```bash
alembic revision --autogenerate -m "マイグレーションの説明"
```

**例:**

```bash
# User テーブルを追加
alembic revision --autogenerate -m "add user table"

# Hero テーブルに email カラムを追加
alembic revision --autogenerate -m "add email to hero"
```

生成されるファイル名の例:

```
2026_02_15_1430-a1b2c3d4e5f6_add_user_table.py
```

### 2. マイグレーションの適用

#### 最新版まで適用

```bash
alembic upgrade head
```

#### 1つ進める

```bash
alembic upgrade +1
```

#### 特定のリビジョンまで適用

```bash
alembic upgrade 4390378ebd41
```

### 3. マイグレーションのロールバック

#### 1つ戻す

```bash
alembic downgrade -1
```

#### すべて戻す（データベースを初期状態に）

```bash
alembic downgrade base
```

#### 特定のリビジョンまで戻す

```bash
alembic downgrade 4390378ebd41
```

### 4. マイグレーション履歴の確認

#### 現在の状態を確認

```bash
alembic current
```

**出力例:**

```
4390378ebd41 (head)
```

#### 履歴を表示

```bash
alembic history
```

**出力例:**

```
4390378ebd41 -> (head), create hero table
<base> -> 4390378ebd41, create hero table
```

#### 詳細な履歴表示

```bash
alembic history --verbose
```

## マイグレーションのワークフロー

### 新しいテーブルを追加する場合

#### 1. モデルを定義

`src/app/database/model/user.py` を作成:

```python
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, max_length=50)
    email: str = Field(unique=True, max_length=255)
    is_active: bool = Field(default=True)
```

#### 2. env.py でモデルをインポート

`src/app/migration/env.py` に追加:

```python
from app.database.model.hero import Hero
from app.database.model.user import User  # 追加
```

#### 3. マイグレーションを自動生成

```bash
# Dev Container内から（/src に移動後）
cd /src
alembic revision --autogenerate -m "add user table"

# または、ホスト/Dev Containerから
docker compose exec api alembic revision --autogenerate -m "add user table"
```

#### 4. 生成されたファイルを確認・調整

`src/app/migration/versions/` に生成されたファイルを開いて内容を確認します。

**自動生成されるコード例:**

```python
def upgrade() -> None:
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=False)
```

必要に応じて手動で調整します（デフォルト値、制約の追加など）。

#### 5. マイグレーションを適用

```bash
# Dev Container内から（/src に移動後）
cd /src
alembic upgrade head

# または、ホスト/Dev Containerから
docker compose exec api alembic upgrade head
```

#### 6. データベースで確認

```bash
docker compose exec postgres psql -U admin -d sample -c "\dt"
```

### カラムを追加する場合

#### 1. モデルを更新

```python
class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    secret_name: str
    email: str | None = Field(default=None, max_length=255)  # 追加
```

#### 2. マイグレーションを生成

```bash
# Dev Container内から（/src に移動後）
cd /src
alembic revision --autogenerate -m "add email to hero"

# または、ホスト/Dev Containerから
docker compose exec api alembic revision --autogenerate -m "add email to hero"
```

#### 3. 生成されたファイルを確認

**注意点:** 既存のデータがある場合、NOT NULL カラムの追加はエラーになります。

```python
# 自動生成されたコード（要調整）
def upgrade() -> None:
    op.add_column('hero', sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
```

#### 4. 適用

```bash
# Dev Container内から（/src に移動後）
cd /src
alembic upgrade head

# または、ホスト/Dev Containerから
docker compose exec api alembic upgrade head
```

## 応用コマンド

### 空のマイグレーションファイルを作成

自動生成を使わず、手動で SQL を書きたい場合:

```bash
alembic revision -m "custom migration"
```

### マイグレーションをマージ

複数のブランチがある場合にマージ:

```bash
alembic merge -m "merge branches" <rev1> <rev2>
```

### 未適用のマイグレーションを確認

```bash
# 現在のリビジョンと head の差分を確認
alembic current
alembic history
```

### マイグレーションファイルの内容を表示

```bash
alembic show <revision>
```

**例:**

```bash
alembic show 4390378ebd41
```

### SQL を出力（実行せずに確認）

```bash
alembic upgrade head --sql
```

これにより、実際に実行される SQL が標準出力に表示されます。

### オフラインモード（SQL ファイル生成）

```bash
alembic upgrade head --sql > migration.sql
```

生成された SQL ファイルを手動で実行できます。

## トラブルシューティング

### エラー: `Target database is not up to date`

**原因:** 手動で DB を変更した、または他の開発者のマイグレーションが未適用

**解決策:**

```bash
# 現在の状態を確認
alembic current

# 最新まで適用
alembic upgrade head
```

### エラー: `Can't locate revision identified by 'xxxxx'`

**原因:** マイグレーションファイルが削除された、またはブランチ切り替えで存在しない

**解決策:**

```bash
# 強制的に現在のリビジョンをマーク（注意: データベースの状態と一致することを確認）
alembic stamp head
```

### autogenerate が変更を検出しない

**原因:** モデルが `env.py` でインポートされていない

**解決策:**

`src/app/migration/env.py` を開いて、モデルをインポート:

```python
from app.database.model.hero import Hero
from app.database.model.user import User  # 追加
```

### マイグレーションを取り消したい（未適用の場合）

```bash
# 生成されたファイルを削除
rm src/app/migration/versions/2026_02_15_xxxx_*.py
```

### マイグレーションを取り消したい（適用済みの場合）

```bash
# 1つ戻す
alembic downgrade -1

# ファイルを削除
rm src/app/migration/versions/2026_02_15_xxxx_*.py
```

### データベースを完全にリセット

```bash
# すべてのマイグレーションを取り消し
alembic downgrade base

# または、データベースを再作成
docker compose down -v
docker compose up -d postgres

# マイグレーションを再適用
docker compose exec api alembic upgrade head
```

### マイグレーション履歴が壊れた場合

```bash
# データベースの alembic_version テーブルを確認
docker compose exec postgres psql -U admin -d sample -c "SELECT * FROM alembic_version;"

# 手動で現在のリビジョンを設定（注意: 実際のスキーマ状態と一致させる）
alembic stamp head
```

## ベストプラクティス

### 1. マイグレーション前に必ずバックアップ

本番環境では必ずバックアップを取ってから実行:

```bash
docker compose exec postgres pg_dump -U admin sample > backup.sql
```

### 2. マイグレーションファイルは必ずレビュー

`--autogenerate` で生成されたファイルは必ず目視確認してから適用:

- 不要なカラムの削除が含まれていないか
- NOT NULL 制約の追加で既存データが壊れないか
- インデックスの削除が含まれていないか

### 3. ロールバック（downgrade）も必ずテスト

```bash
# 適用
alembic upgrade head

# 戻す
alembic downgrade -1

# 再度適用
alembic upgrade head
```

### 4. 本番環境では慎重に

- 必ず開発環境でテストしてから本番適用
- データ量が多い場合は、実行時間を考慮
- ロックが発生する操作（テーブル変更）は メンテナンス時間に実行

## 実行環境別コマンドまとめ

### Dev Container 内から実行（VSCode Dev Container）

```bash
# /src に移動
cd /src

# マイグレーション生成
alembic revision --autogenerate -m "add user table"

# 適用
alembic upgrade head

# 履歴確認
alembic history

# 現在の状態
alembic current

# 1つ戻す
alembic downgrade -1

# すべて戻す
alembic downgrade base
```

または `/workspace` から実行する場合:

```bash
# -c オプションで設定ファイルを指定
alembic -c /workspace/src/alembic.ini upgrade head
alembic -c /workspace/src/alembic.ini history
```

### ホストから Docker Compose 経由で実行

```bash
# マイグレーション生成
docker compose exec api alembic revision --autogenerate -m "add user table"

# 適用
docker compose exec api alembic upgrade head

# 履歴確認
docker compose exec api alembic history

# 現在の状態
docker compose exec api alembic current

# 1つ戻す
docker compose exec api alembic downgrade -1

# すべて戻す
docker compose exec api alembic downgrade base
```

**推奨:** Dev Container内でもホストからでも、`docker compose exec api` を使う方法が最も確実です。

## 次のステップ

- [API エンドポイントの実装](04-api-development.md)（作成予定）
- [テストの書き方](05-testing.md)（作成予定）
