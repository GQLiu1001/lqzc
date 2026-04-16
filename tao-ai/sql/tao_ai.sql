-- tao-ai M2: 业务表 DDL
-- MySQL 8.0+ / MariaDB 10.7+
-- 注意: LangGraph checkpoint 表由 AIOMySQLSaver.setup() 自动创建, 此处只管业务表。

CREATE DATABASE IF NOT EXISTS tao_ai_runtime
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE tao_ai_runtime;

-- ========== 任务轨迹 ==========

CREATE TABLE IF NOT EXISTS task (
    task_id       VARCHAR(64)  NOT NULL,
    session_id    VARCHAR(255) NOT NULL COMMENT 'LangGraph thread_id',
    skill         VARCHAR(50)  DEFAULT NULL,
    status        ENUM('pending','running','waiting_approval','succeeded','failed','expired')
                  NOT NULL DEFAULT 'pending',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    error         TEXT         DEFAULT NULL,
    PRIMARY KEY (task_id),
    INDEX idx_task_session (session_id),
    INDEX idx_task_status  (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========== 工具调用记录 (幂等执行器) ==========

CREATE TABLE IF NOT EXISTS tool_call (
    id              BIGINT       AUTO_INCREMENT PRIMARY KEY,
    task_id         VARCHAR(64)  NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL COMMENT 'sha256(task_id:tool:sorted_args)',
    tool            VARCHAR(100) NOT NULL,
    args            JSON         DEFAULT NULL,
    status          ENUM('ok','error','pending_approval','rejected','timeout')
                    NOT NULL DEFAULT 'ok',
    result          JSON         DEFAULT NULL,
    error           TEXT         DEFAULT NULL,
    latency_ms      INT          DEFAULT NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_idemp (idempotency_key),
    INDEX idx_tc_task (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========== 审批记录 ==========

CREATE TABLE IF NOT EXISTS approval (
    id            BIGINT       AUTO_INCREMENT PRIMARY KEY,
    task_id       VARCHAR(64)  NOT NULL,
    session_id    VARCHAR(255) NOT NULL,
    tool          VARCHAR(100) NOT NULL,
    args          JSON         DEFAULT NULL,
    risk_level    VARCHAR(20)  NOT NULL DEFAULT 'high' COMMENT 'high / medium',
    risk_reason   TEXT         DEFAULT NULL,
    ai_review     TEXT         DEFAULT NULL COMMENT 'AI 自审意见',
    decision      ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    decided_by    VARCHAR(100) DEFAULT NULL,
    decided_at    DATETIME     DEFAULT NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_appr_task    (task_id),
    INDEX idx_appr_session (session_id),
    INDEX idx_appr_pending (decision)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
