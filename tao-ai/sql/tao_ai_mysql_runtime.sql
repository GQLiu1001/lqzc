-- Tao AI runtime schema (MySQL)
-- Stack: LangChain + LangGraph + Milvus + MySQL

CREATE TABLE IF NOT EXISTS ai_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NULL,
    user_id VARCHAR(64) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ai_messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content MEDIUMTEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ai_messages_session_id (session_id),
    CONSTRAINT fk_ai_messages_session FOREIGN KEY (session_id) REFERENCES ai_sessions(session_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ai_tasks (
    task_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    tenant_id VARCHAR(64) NULL,
    user_id VARCHAR(64) NULL,
    status VARCHAR(32) NOT NULL,
    current_agent VARCHAR(64) NULL,
    current_skill VARCHAR(128) NULL,
    risk_level VARCHAR(16) NOT NULL DEFAULT 'LOW',
    user_message MEDIUMTEXT NULL,
    final_response MEDIUMTEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ai_tasks_session_id (session_id),
    INDEX idx_ai_tasks_status (status),
    CONSTRAINT fk_ai_tasks_session FOREIGN KEY (session_id) REFERENCES ai_sessions(session_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ai_tool_traces (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    tool_name VARCHAR(128) NOT NULL,
    arguments_json JSON NULL,
    result_preview TEXT NULL,
    result_json JSON NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ai_tool_traces_task_id (task_id),
    CONSTRAINT fk_ai_tool_traces_task FOREIGN KEY (task_id) REFERENCES ai_tasks(task_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ai_retrieval_traces (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    query_text TEXT NOT NULL,
    domain VARCHAR(64) NOT NULL,
    collection_name VARCHAR(128) NOT NULL,
    hits INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ai_retrieval_traces_task_id (task_id),
    CONSTRAINT fk_ai_retrieval_traces_task FOREIGN KEY (task_id) REFERENCES ai_tasks(task_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ai_approvals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    approval_action VARCHAR(32) NOT NULL,
    approver_id VARCHAR(64) NULL,
    comment TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ai_approvals_task (task_id),
    CONSTRAINT fk_ai_approvals_task FOREIGN KEY (task_id) REFERENCES ai_tasks(task_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
