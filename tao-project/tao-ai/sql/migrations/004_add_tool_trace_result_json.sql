-- Migration 004: add structured result column for tool traces

SET @has_result_json_col := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'ai_tool_traces'
      AND column_name = 'result_json'
);

SET @ddl := IF(
    @has_result_json_col = 0,
    'ALTER TABLE ai_tool_traces ADD COLUMN result_json JSON NULL AFTER result_preview',
    'SELECT 1'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
