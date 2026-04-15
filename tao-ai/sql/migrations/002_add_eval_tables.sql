-- Migration 002: add evaluation persistence tables

CREATE TABLE IF NOT EXISTS ai_eval_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    dataset_name VARCHAR(128) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING',
    total_cases INT NOT NULL DEFAULT 0,
    passed_cases INT NOT NULL DEFAULT 0,
    route_accuracy DOUBLE NOT NULL DEFAULT 0,
    tool_success_rate DOUBLE NOT NULL DEFAULT 0,
    retrieval_hit_rate DOUBLE NOT NULL DEFAULT 0,
    approval_trigger_precision DOUBLE NOT NULL DEFAULT 0,
    pass_rate DOUBLE NOT NULL DEFAULT 0,
    avg_latency_ms DOUBLE NOT NULL DEFAULT 0,
    error_message TEXT NULL,
    started_at VARCHAR(64) NULL,
    finished_at VARCHAR(64) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ai_eval_runs_dataset (dataset_name),
    INDEX idx_ai_eval_runs_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ai_eval_case_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL,
    case_id VARCHAR(128) NOT NULL,
    message TEXT NOT NULL,
    expected_agent VARCHAR(64) NULL,
    expected_skill VARCHAR(128) NULL,
    expected_requires_approval TINYINT(1) NULL,
    actual_agent VARCHAR(64) NULL,
    actual_skill VARCHAR(128) NULL,
    actual_requires_approval TINYINT(1) NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL,
    retrieval_hits INT NOT NULL DEFAULT 0,
    tool_calls_total INT NOT NULL DEFAULT 0,
    tool_calls_success INT NOT NULL DEFAULT 0,
    latency_ms DOUBLE NOT NULL DEFAULT 0,
    passed_route TINYINT(1) NOT NULL DEFAULT 0,
    passed_retrieval TINYINT(1) NOT NULL DEFAULT 0,
    passed_approval TINYINT(1) NOT NULL DEFAULT 0,
    passed_keywords TINYINT(1) NOT NULL DEFAULT 0,
    passed TINYINT(1) NOT NULL DEFAULT 0,
    error_message TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ai_eval_case_run (run_id),
    INDEX idx_ai_eval_case_case_id (case_id),
    CONSTRAINT fk_ai_eval_case_run FOREIGN KEY (run_id) REFERENCES ai_eval_runs(run_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
