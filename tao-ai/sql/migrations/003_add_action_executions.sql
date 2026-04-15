-- Migration 003: add action execution persistence for approval-then-execute loop

CREATE TABLE IF NOT EXISTS ai_action_executions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    action_name VARCHAR(128) NOT NULL,
    action_payload_json JSON NULL,
    approval_action VARCHAR(32) NOT NULL,
    approver_id VARCHAR(64) NULL,
    comment TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    response_json JSON NULL,
    error_message TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ai_action_executions_idem (idempotency_key),
    INDEX idx_ai_action_executions_task_id (task_id),
    CONSTRAINT fk_ai_action_executions_task FOREIGN KEY (task_id) REFERENCES ai_tasks(task_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
