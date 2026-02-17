-- 8001.T (伊藤忠商事) のシードデータ
-- Usage: psql -h localhost -U admin -d <db_name> -f seed.sql

-- 銘柄マスタ
INSERT INTO tickers (ticker, name, is_active, created_at, updated_at)
VALUES ('8001.T', '伊藤忠商事', TRUE, NOW(), NOW())
ON CONFLICT (ticker) DO NOTHING;
