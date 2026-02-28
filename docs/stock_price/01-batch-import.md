# 株価データ バッチ取り込み

yfinance から1分足の株価データを取得し、PostgreSQL に取り込むバッチ処理の仕様・設計・運用方法をまとめます。

## 目次

1. [概要](#概要)
2. [コード構成](#コード構成)
3. [データベーススキーマ](#データベーススキーマ)
4. [実行方法](#実行方法)
5. [設定値](#設定値)
6. [処理フロー](#処理フロー)
7. [欠損検出ロジック](#欠損検出ロジック)
8. [エラーハンドリングとリトライ](#エラーハンドリングとリトライ)
9. [ログ出力](#ログ出力)

---

## 概要

- **データソース**: [yfinance](https://github.com/ranaroussi/yfinance)（Yahoo Finance の非公式ラッパー）
- **取得粒度**: 1分足 OHLCV データ
- **対象銘柄**: `tickers` テーブルの `is_active = true` な銘柄
- **重複処理**: `(ticker, price_datetime)` の一意制約により、既存レコードは `ON CONFLICT DO NOTHING` でスキップ
- **欠損補完**: 既存データと比較して未取得の日付範囲のみフェッチ

---

## コード構成

```
src/app/
├── batch/
│   └── fetch_stock_prices.py       # CLIエントリーポイント（Typer）
├── stock_price/
│   ├── service.py                  # 取り込みオーケストレーション
│   └── protocol/
│       └── stock_data_fetcher.py   # データ取得インターフェース
├── infra/
│   └── external/
│       └── yfinance_fetcher.py     # yfinance ラッパー（StockDataFetcher の実装）
└── database/
    ├── model/
    │   └── stock_price_1m.py       # ORM モデル（stock_prices_1m テーブル）
    └── repository/
        └── stock_price_1m_repository.py  # DB 操作
```

| ファイル | 役割 |
|---|---|
| `batch/fetch_stock_prices.py` | CLI オプション解析・非同期実行の起動 |
| `stock_price/service.py` | 銘柄ループ・欠損検出・取り込み呼び出し |
| `infra/external/yfinance_fetcher.py` | yfinance 呼び出し・データ整形・リトライ |
| `database/repository/stock_price_1m_repository.py` | バルク INSERT・エラー特定ログ |

---

## データベーススキーマ

### `stock_prices_1m` テーブル

| カラム | 型 | 説明 |
|---|---|---|
| `id` | BIGINT (PK) | 自動採番 |
| `ticker` | VARCHAR(20) | 銘柄コード（例: `8001.T`） |
| `price_datetime` | TIMESTAMPTZ | 価格の日時（タイムゾーン付き） |
| `open` | NUMERIC(10,2) | 始値 |
| `high` | NUMERIC(10,2) | 高値 |
| `low` | NUMERIC(10,2) | 安値 |
| `close` | NUMERIC(10,2) | 終値 |
| `volume` | BIGINT | 出来高 |
| `created_at` | TIMESTAMPTZ | レコード登録日時（UTC） |

**ユニーク制約**: `uq_stock_prices_1m_ticker_price_datetime`（`ticker`, `price_datetime`）

### `tickers` テーブル（参照）

バッチ対象銘柄を管理するマスタテーブル。`is_active = true` の銘柄のみが取得対象になります。

---

## 実行方法

コンテナ内から以下のコマンドで実行します。
`python -m` を使うのは、ワーキングディレクトリ（`/src`）を `sys.path` に追加し、`from app.xxx import yyy` の絶対インポートを正しく解決するためです。

```bash
# コンテナに入る
docker compose exec api bash

# デフォルト実行（設定値の lookback_days 分を取得）
python -m app.batch.fetch_stock_prices

# 過去日数を指定
python -m app.batch.fetch_stock_prices --days 3

# 特定銘柄のみ取得
python -m app.batch.fetch_stock_prices --ticker 8001.T

# ドライランモード（DB 書き込みなし）
python -m app.batch.fetch_stock_prices --dry-run

# 組み合わせ例
python -m app.batch.fetch_stock_prices --days 1 --ticker 8001.T --dry-run
```

### オプション一覧

| オプション | デフォルト | 説明 |
|---|---|---|
| `--days` | 設定値 `batch_lookback_days`（デフォルト 7） | 取得する過去日数 |
| `--ticker` | なし（全アクティブ銘柄） | 特定銘柄のみ取得する場合に指定 |
| `--dry-run` | `false` | DB への書き込みを行わず件数のみログ出力 |

---

## 設定値

環境変数（`containers/api/api.env`）で制御します。

| 環境変数 | デフォルト | 説明 |
|---|---|---|
| `BATCH_LOOKBACK_DAYS` | `7` | `--days` 未指定時の取得日数 |
| `BATCH_MAX_RETRIES` | `3` | yfinance 取得失敗時の最大リトライ回数 |
| `BATCH_RETRY_DELAY_SECONDS` | `5` | リトライ間隔（秒） |
| `BATCH_LOG_LEVEL` | `INFO` | ログレベル（`DEBUG` / `INFO` / `WARNING` / `ERROR`） |

---

## 処理フロー

```
fetch_stock_prices (CLI)
  │
  ├─ Settings 読み込み
  ├─ AsyncSession 生成
  ├─ StockPriceService 生成
  └─ service.process_all_tickers(fetcher, days)
        │
        ├─ TickerRepository.get_active_tickers()
        │     └─ tickers テーブルから is_active=true の銘柄一覧を取得
        │
        └─ 各銘柄に対して process_ticker() を実行
              │
              ├─ 取得期間を算出（現在時刻 - days ～ 現在時刻）
              ├─ _get_missing_ranges()
              │     └─ 欠損している日付範囲を特定（後述）
              │
              └─ 欠損範囲ごとに:
                    ├─ YFinanceFetcher.fetch_1m_data() で yfinance から取得
                    ├─ （dry_run の場合はここで終了）
                    └─ _import_price_data()
                          └─ StockPrice1mRepository.bulk_insert()
                                └─ ON CONFLICT DO NOTHING で一括 INSERT
```

---

## 欠損検出ロジック

毎回全期間を取得するのではなく、**DB に既に存在するデータを確認し、不足している日付範囲のみを取得**します。

### 手順

1. `stock_prices_1m` テーブルから、取得期間内の日付ごとのレコード件数を集計
2. 件数が閾値（`MIN_RECORDS_PER_DAY = 200`）を下回る日は「部分欠損」とみなし、再取得対象に含める
3. 欠損日を収集し、**連続する日付はひとつの範囲にまとめて** yfinance へのリクエスト回数を最小化

### 閾値について

東証の取引時間は前場（9:00〜11:30）と後場（12:30〜15:30）で合計300分のため、1日あたり最大300件のレコードが存在します。`MIN_RECORDS_PER_DAY = 200` を下回る場合は部分欠損と判断します。

祝日や取引停止日は件数が 0 件になりますが、毎回フェッチを試みて空データが返ることで「欠損なし（0件の取引日）」として処理されます。

---

## エラーハンドリングとリトライ

### yfinance 取得失敗（`YFinanceFetcher`）

- 最大 `batch_max_retries` 回（デフォルト 3 回）リトライ
- リトライ間隔は `batch_retry_delay_seconds`（デフォルト 5 秒）
- 全リトライ失敗時は例外を上位に伝播

### 銘柄単位のエラー隔離（`StockPriceService`）

- 1銘柄の処理に失敗しても他の銘柄の処理は継続
- エラー内容は `ERROR` レベルでスタックトレース付きでログ出力

### バルク INSERT 失敗（`StockPrice1mRepository`）

- バルク INSERT が失敗した場合、1件ずつ再試行して原因レコードを特定
- 特定した失敗レコードの SQL・パラメータ・PostgreSQL エラーコードをログ出力
- セッションはロールバックして例外を再 raise

---

## ログ出力

各処理フェーズにプレフィックスを付与してログを出力します（`app/common/log_prefix.py`）。

| プレフィックス | 出力箇所 | 内容 |
|---|---|---|
| `[BATCH_JOB]` | `fetch_stock_prices.py` | バッチ全体の開始・終了 |
| `[FETCH_STOCK_DATA]` | `yfinance_fetcher.py` | yfinance へのリクエスト（銘柄・期間・試行回数） |
| `[IMPORT_STOCK_DATA]` | `service.py` | DB 取り込み完了（銘柄・件数・期間） |
| `[INSERT_STOCK_DATA]` | `stock_price_1m_repository.py` | バルク INSERT エラー発生時の詳細 |

### ログ出力例

```
2026-02-27 09:00:00 - app.batch.fetch_stock_prices - INFO - [BATCH_JOB] Starting with days=7, ticker=None, dry_run=False
2026-02-27 09:00:00 - app.stock_price.service - INFO - Found 5 active ticker(s) to process
2026-02-27 09:00:00 - app.stock_price.service - INFO - Processing 8001.T...
2026-02-27 09:00:00 - app.stock_price.service - INFO - 8001.T: found 2 gap(s) to fetch
2026-02-27 09:00:01 - app.infra.external.yfinance_fetcher - INFO - [FETCH_STOCK_DATA] 8001.T interval=1m start=... end=... (attempt 1/3)
2026-02-27 09:00:03 - app.stock_price.service - INFO - [IMPORT_STOCK_DATA] 8001.T: imported 298 records for range ...
2026-02-27 09:00:10 - app.batch.fetch_stock_prices - INFO - [BATCH_JOB] Completed
```
