-- Tao AI runtime schema (MySQL 8.0+)
-- Stack: LangChain + LangGraph + Milvus + MySQL + Redis

CREATE DATABASE IF NOT EXISTS tao_ai_runtime
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE tao_ai_runtime;

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

