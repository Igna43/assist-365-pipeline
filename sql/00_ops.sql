-- Operational tables. Idempotent so every run can ensure them before reading the watermark.

CREATE TABLE IF NOT EXISTS `${project}.ops.watermarks` (
  resource STRING NOT NULL,
  watermark_ts TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `${project}.ops.extract_counts` (
  resource STRING NOT NULL,
  batch_id STRING,
  mode STRING,
  api_total INT64,
  loaded_rows INT64,
  extracted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `${project}.ops.pipeline_runs` (
  batch_id STRING,
  started_at TIMESTAMP,
  finished_at TIMESTAMP,
  status STRING,
  detail STRING
);
