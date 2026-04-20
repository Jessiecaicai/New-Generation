-- Create metadata database
CREATE DATABASE IF NOT EXISTS agent_meta;
USE agent_meta;

-- Sessions
CREATE TABLE sessions (
    id VARCHAR(36) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Chat history
CREATE TABLE chat_history (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    role ENUM('USER','ASSISTANT') NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR(50),
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    INDEX idx_session_time (session_id, created_at)
);

-- Knowledge bases
CREATE TABLE knowledge_bases (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    document_count INT DEFAULT 0,
    chunk_count INT DEFAULT 0,
    status ENUM('ACTIVE','BUILDING','ERROR') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Knowledge documents
CREATE TABLE knowledge_documents (
    id VARCHAR(36) PRIMARY KEY,
    knowledge_base_id VARCHAR(36) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    file_type VARCHAR(20),
    chunk_count INT DEFAULT 0,
    status ENUM('PENDING','INDEXED','ERROR') DEFAULT 'PENDING',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id)
);

-- System logs
CREATE TABLE system_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    service_name ENUM('JAVA_BACKEND','PYTHON_AGENT') NOT NULL,
    log_level ENUM('INFO','WARN','ERROR','FATAL') NOT NULL,
    category VARCHAR(100),
    message TEXT NOT NULL,
    stack_trace TEXT,
    request_id VARCHAR(36),
    session_id VARCHAR(36),
    metadata JSON,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_level_time (log_level, created_at DESC),
    INDEX idx_service_time (service_name, created_at DESC),
    INDEX idx_unresolved (is_resolved, log_level, created_at DESC)
);

-- Agent skills config
CREATE TABLE agent_skills (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    skill_type ENUM('BUILTIN','CUSTOM') NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Agent prompt templates
CREATE TABLE agent_prompts (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    template_content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Async tasks
CREATE TABLE tasks (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36),
    question TEXT NOT NULL,
    status ENUM('QUEUED','PROCESSING','SUCCESS','ERROR') NOT NULL DEFAULT 'QUEUED',
    intent VARCHAR(50),
    result JSON,
    error_message TEXT,
    queue_position INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    INDEX idx_status (status, created_at)
);

-- Insert default skills
INSERT INTO agent_skills (id, name, description, skill_type, is_enabled) VALUES
('sk-001', 'nl2sql', '将自然语言转换为SQL查询并执行，支持查表结构、生成SQL、语法校验', 'BUILTIN', TRUE),
('sk-002', 'log_analyzer', '分析系统日志，定位异常和错误根因，提供统计和趋势分析', 'BUILTIN', TRUE),
('sk-003', 'knowledge_qa', '基于知识库文档回答问题，支持语义检索和引用溯源', 'BUILTIN', TRUE);
