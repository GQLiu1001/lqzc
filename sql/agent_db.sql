-- ====================================================================================
--  TAO AI Agent Runtime - PostgreSQL 数据库脚本
--  数据库: agent_db
--
--  包含: 审计日志、评测结果、文档元数据、出库审批单
--  注意: LangGraph checkpoint 表由 AsyncPostgresSaver.setup() 自动创建，无需手动建表
-- ====================================================================================

CREATE DATABASE agent_db;

\c agent_db;

-- ----------------------------
-- 1. 审计日志表
--    记录每次 /chat 请求的路由、工具调用、耗时等信息，用于排查和监控
-- ----------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGSERIAL       PRIMARY KEY,
    session_id      VARCHAR(64)     NOT NULL,
    message_id      VARCHAR(64),
    user_type       VARCHAR(20)     NOT NULL,
    user_id         BIGINT          NOT NULL,
    route           VARCHAR(30),
    intent          VARCHAR(60),
    tool_name       VARCHAR(100),
    tool_args       JSONB,
    status          VARCHAR(30)     NOT NULL DEFAULT 'success',
    error_code      VARCHAR(60),
    latency_ms      INT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- 常用查询维度索引
    CONSTRAINT idx_audit_session UNIQUE (session_id, message_id, tool_name)
);

CREATE INDEX idx_audit_user      ON audit_log (user_id, created_at);
CREATE INDEX idx_audit_route     ON audit_log (route, created_at);
CREATE INDEX idx_audit_status    ON audit_log (status) WHERE status != 'success';
CREATE INDEX idx_audit_time      ON audit_log (created_at);


-- ----------------------------
-- 2. 文档元数据表
--    管理 RAG 知识库中每篇文档的来源、版本、生效时间、权限等
-- ----------------------------
CREATE TABLE IF NOT EXISTS document_meta (
    id              BIGSERIAL       PRIMARY KEY,
    doc_id          VARCHAR(64)     NOT NULL UNIQUE,
    title           VARCHAR(256)    NOT NULL,
    domain          VARCHAR(30)     NOT NULL,
    scene           VARCHAR(60),
    source_type     VARCHAR(30)     NOT NULL DEFAULT 'manual',
    access_level    VARCHAR(20)     NOT NULL DEFAULT 'staff',
    role_allowlist  TEXT[]          DEFAULT '{}',
    tenant_id       VARCHAR(30),
    warehouse_scope TEXT[]          DEFAULT '{}',
    version         VARCHAR(30),
    effective_at    TIMESTAMPTZ,
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    chunk_count     INT             NOT NULL DEFAULT 0,
    file_path       VARCHAR(512),
    file_hash       VARCHAR(64),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_doc_domain      ON document_meta (domain, is_active);
CREATE INDEX idx_doc_scene       ON document_meta (domain, scene);
CREATE INDEX idx_doc_active      ON document_meta (is_active) WHERE is_active = TRUE;


-- ----------------------------
-- 3. 出库审批单表
--    记录 WarehouseAgent 通过 interrupt_on 触发的审批请求
-- ----------------------------
CREATE TABLE IF NOT EXISTS outbound_approval (
    id              BIGSERIAL       PRIMARY KEY,
    approval_no     VARCHAR(30)     NOT NULL UNIQUE,
    session_id      VARCHAR(64)     NOT NULL,
    warehouse_id    VARCHAR(20)     NOT NULL,
    item_id         VARCHAR(30)     NOT NULL,
    qty             INT             NOT NULL,
    reason          TEXT            DEFAULT '',
    applicant_id    BIGINT          NOT NULL,
    applicant_role  VARCHAR(30)     NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'pending',
    reviewer_id     BIGINT,
    review_comment  TEXT,
    reviewed_at     TIMESTAMPTZ,
    idempotency_key VARCHAR(128)    UNIQUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_approval_status CHECK (status IN ('pending', 'approved', 'rejected'))
);

CREATE INDEX idx_approval_session   ON outbound_approval (session_id);
CREATE INDEX idx_approval_status    ON outbound_approval (status, created_at);
CREATE INDEX idx_approval_applicant ON outbound_approval (applicant_id, created_at);


-- ----------------------------
-- 4. 离线评测结果表
--    存储离线 eval runner 的每轮评测指标汇总
-- ----------------------------
CREATE TABLE IF NOT EXISTS eval_run (
    id              BIGSERIAL       PRIMARY KEY,
    run_id          VARCHAR(64)     NOT NULL UNIQUE,
    dataset_name    VARCHAR(100)    NOT NULL,
    total_samples   INT             NOT NULL DEFAULT 0,
    hit_at_5        NUMERIC(5,4),
    recall_at_10    NUMERIC(5,4),
    mrr             NUMERIC(5,4),
    ndcg_at_10      NUMERIC(5,4),
    groundedness    NUMERIC(5,4),
    correctness     NUMERIC(5,4),
    permission_safety NUMERIC(5,4),
    no_hit_rate     NUMERIC(5,4),
    duration_ms     INT,
    config_snapshot JSONB,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);


-- ----------------------------
-- 5. 离线评测样本明细表
--    每条评测样本的检索结果、回答与评分
-- ----------------------------
CREATE TABLE IF NOT EXISTS eval_sample (
    id              BIGSERIAL       PRIMARY KEY,
    run_id          VARCHAR(64)     NOT NULL REFERENCES eval_run(run_id),
    sample_id       VARCHAR(64)     NOT NULL,
    domain          VARCHAR(30)     NOT NULL,
    scene           VARCHAR(60),
    question        TEXT            NOT NULL,
    user_context    JSONB,
    expected_doc_ids TEXT[],
    reference_answer TEXT,
    actual_answer   TEXT,
    retrieved_docs  JSONB,
    hit             BOOLEAN,
    groundedness    NUMERIC(5,4),
    correctness     NUMERIC(5,4),
    permission_safe BOOLEAN,
    latency_ms      INT,
    passed          BOOLEAN         NOT NULL DEFAULT TRUE,
    failure_reason  TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_eval_sample_run    ON eval_sample (run_id);
CREATE INDEX idx_eval_sample_fail   ON eval_sample (passed) WHERE passed = FALSE;


-- ----------------------------
-- 6. 在线评测抽样记录表
--    在线 eval worker 对真实流量的抽样评测结果
-- ----------------------------
CREATE TABLE IF NOT EXISTS online_eval_sample (
    id              BIGSERIAL       PRIMARY KEY,
    session_id      VARCHAR(64)     NOT NULL,
    message_id      VARCHAR(64),
    route           VARCHAR(30),
    intent          VARCHAR(60),
    question        TEXT            NOT NULL,
    answer          TEXT,
    tool_calls      TEXT[],
    retrieved_docs  JSONB,
    no_hit          BOOLEAN         NOT NULL DEFAULT FALSE,
    latency_ms      INT,
    status          VARCHAR(30),
    user_context    JSONB,

    -- judge 评分
    rule_judge_pass BOOLEAN,
    rule_judge_detail JSONB,
    llm_judge_score NUMERIC(5,4),
    llm_judge_detail JSONB,

    failed          BOOLEAN         NOT NULL DEFAULT FALSE,
    failure_tags    TEXT[],
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_online_eval_session ON online_eval_sample (session_id);
CREATE INDEX idx_online_eval_fail    ON online_eval_sample (failed) WHERE failed = TRUE;
CREATE INDEX idx_online_eval_time    ON online_eval_sample (created_at);
