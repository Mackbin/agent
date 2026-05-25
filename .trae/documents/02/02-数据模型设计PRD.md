# 个人版 AI 基座 - 数据模型设计 PRD

**版本**：v1.0  
**创建日期**：2024-01-XX  
**文档类型**：技术设计文档  
**关联文档**：《个人版 AI 基座 PRD.md》

---

# 一、文档概述

## 1.1 文档目的

本文档详细描述个人版 AI 基座的数据模型设计，包括数据库表结构、字段定义、索引设计、关系说明等，作为数据库开发、迁移脚本编写的核心依据。

## 1.2 设计原则

- **规范化**：遵循第三范式（3NF），减少数据冗余
- **可扩展**：预留扩展字段，支持后续功能迭代
- **性能优先**：合理设计索引，优化查询性能
- **可维护**：统一命名规范，便于维护

## 1.3 数据库选型

- **数据库**：PostgreSQL 15+
- **向量扩展**：pgvector 0.5+
- **字符集**：UTF8
- **时区**：UTC

---

# 二、核心数据模型

## 2.1 用户相关表

### 2.1.1 用户表（users）

**用途**：存储用户账号信息

```sql
CREATE TABLE users (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 基本信息
    username VARCHAR(50) NOT NULL UNIQUE,           -- 用户名
    email VARCHAR(100) NOT NULL UNIQUE,             -- 邮箱
    password_hash VARCHAR(255) NOT NULL,            -- 密码哈希（bcrypt）
    avatar_url VARCHAR(500),                         -- 头像 URL
    
    -- 状态
    status SMALLINT NOT NULL DEFAULT 1,             -- 状态：1-正常，0-禁用
    is_verified BOOLEAN DEFAULT FALSE,              -- 邮箱是否验证
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,         -- 最后登录时间
    
    -- 索引
    CONSTRAINT chk_status CHECK (status IN (0, 1))
);

-- 索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at);

-- 注释
COMMENT ON TABLE users IS '用户信息表';
COMMENT ON COLUMN users.id IS '用户 ID（UUID）';
COMMENT ON COLUMN users.username IS '用户名（唯一）';
COMMENT ON COLUMN users.email IS '邮箱（唯一）';
COMMENT ON COLUMN users.password_hash IS '密码哈希（bcrypt）';
COMMENT ON COLUMN users.status IS '用户状态：1-正常，0-禁用';
```

### 2.1.2 API Key 表（api_keys）

**用途**：存储用户 API Key

```sql
CREATE TABLE api_keys (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 关联
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Key 信息
    key_hash VARCHAR(64) NOT NULL UNIQUE,           -- API Key 哈希（SHA256）
    key_prefix VARCHAR(20) NOT NULL,                -- Key 前缀（用于展示）
    name VARCHAR(100),                               -- Key 名称
    
    -- 权限配置
    permissions JSONB DEFAULT '{}',                 -- 权限配置（JSON）
    rate_limit INTEGER DEFAULT 60,                  -- 每分钟限流次数
    
    -- 状态
    is_active BOOLEAN NOT NULL DEFAULT TRUE,        -- 是否启用
    expires_at TIMESTAMP WITH TIME ZONE,            -- 过期时间
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,          -- 最后使用时间
    
    -- 索引
    CONSTRAINT chk_rate_limit CHECK (rate_limit > 0)
);

-- 索引
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);
CREATE INDEX idx_api_keys_created_at ON api_keys(created_at);

-- 注释
COMMENT ON TABLE api_keys IS 'API Key 表';
COMMENT ON COLUMN api_keys.key_hash IS 'API Key 哈希（SHA256）';
COMMENT ON COLUMN api_keys.key_prefix IS 'Key 前缀（用于展示，如 sk-abc123）';
COMMENT ON COLUMN api_keys.permissions IS '权限配置（JSON 格式）';
```

## 2.2 对话相关表

### 2.2.1 会话表（conversations）

**用途**：存储对话会话信息

```sql
CREATE TABLE conversations (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 关联
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 会话信息
    title VARCHAR(200),                             -- 会话标题
    model VARCHAR(50) NOT NULL,                     -- 使用的模型
    
    -- 状态
    status SMALLINT NOT NULL DEFAULT 1,             -- 状态：1-活跃，0-归档，-1-删除
    
    -- 统计
    message_count INTEGER NOT NULL DEFAULT 0,       -- 消息数量
    total_tokens INTEGER NOT NULL DEFAULT 0,        -- 总 Token 消耗
    
    -- 配置
    system_prompt TEXT,                             -- 系统提示词
    metadata JSONB DEFAULT '{}',                    -- 元数据
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CONSTRAINT chk_status CHECK (status IN (-1, 0, 1))
);

-- 索引
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at);

-- 注释
COMMENT ON TABLE conversations IS '对话会话表';
COMMENT ON COLUMN conversations.status IS '状态：1-活跃，0-归档，-1-删除';
```

### 2.2.2 消息表（messages）

**用途**：存储对话消息

```sql
CREATE TABLE messages (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 关联
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- 消息内容
    role VARCHAR(20) NOT NULL,                      -- 角色：system/user/assistant
    content TEXT NOT NULL,                          -- 消息内容
    
    -- 统计
    tokens INTEGER,                                 -- Token 数量
    prompt_tokens INTEGER,                          -- 输入 Token
    completion_tokens INTEGER,                      -- 输出 Token
    
    -- 模型信息
    model VARCHAR(50),                              -- 使用的模型
    provider VARCHAR(50),                           -- Provider 名称
    
    -- 性能
    latency_ms INTEGER,                             -- 响应延迟（毫秒）
    
    -- 元数据
    metadata JSONB DEFAULT '{}',                    -- 元数据
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CONSTRAINT chk_role CHECK (role IN ('system', 'user', 'assistant'))
);

-- 索引
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- 复合索引（优化查询）
CREATE INDEX idx_messages_conv_created ON messages(conversation_id, created_at);

-- 注释
COMMENT ON TABLE messages IS '对话消息表';
COMMENT ON COLUMN messages.role IS '角色：system/user/assistant';
COMMENT ON COLUMN messages.tokens IS '总 Token 数';
COMMENT ON COLUMN messages.latency_ms IS '响应延迟（毫秒）';
```

## 2.3 知识库相关表

### 2.3.1 知识库表（knowledge_bases）

**用途**：存储知识库信息

```sql
CREATE TABLE knowledge_bases (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 关联
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 知识库信息
    name VARCHAR(100) NOT NULL,                     -- 知识库名称
    description TEXT,                               -- 描述
    
    -- 配置
    embedding_model VARCHAR(50) DEFAULT 'text-embedding-ada-002',  -- Embedding 模型
    chunk_size INTEGER DEFAULT 500,                 -- 分块大小（tokens）
    chunk_overlap INTEGER DEFAULT 100,              -- 分块重叠（tokens）
    
    -- 状态
    is_active BOOLEAN NOT NULL DEFAULT TRUE,        -- 是否启用
    is_private BOOLEAN NOT NULL DEFAULT TRUE,       -- 是否私有
    
    -- 统计
    document_count INTEGER NOT NULL DEFAULT 0,      -- 文档数量
    chunk_count INTEGER NOT NULL DEFAULT 0,         -- 分块数量
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CONSTRAINT chk_chunk_size CHECK (chunk_size > 0 AND chunk_size <= 2000),
    CONSTRAINT chk_chunk_overlap CHECK (chunk_overlap >= 0 AND chunk_overlap < chunk_size)
);

-- 索引
CREATE INDEX idx_knowledge_bases_user_id ON knowledge_bases(user_id);
CREATE INDEX idx_knowledge_bases_is_active ON knowledge_bases(is_active);
CREATE INDEX idx_knowledge_bases_created_at ON knowledge_bases(created_at);

-- 注释
COMMENT ON TABLE knowledge_bases IS '知识库表';
COMMENT ON COLUMN knowledge_bases.embedding_model IS 'Embedding 模型名称';
COMMENT ON COLUMN knowledge_bases.chunk_size IS '分块大小（tokens）';
COMMENT ON COLUMN knowledge_bases.chunk_overlap IS '分块重叠（tokens）';
```

### 2.3.2 文档表（documents）

**用途**：存储上传的文档信息

```sql
CREATE TABLE documents (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 关联
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    
    -- 文档信息
    title VARCHAR(200) NOT NULL,                    -- 文档标题
    file_name VARCHAR(200),                         -- 文件名
    file_path VARCHAR(500),                         -- 文件存储路径
    file_size BIGINT,                               -- 文件大小（字节）
    file_type VARCHAR(20),                          -- 文件类型：md/txt/pdf
    
    -- 内容
    content TEXT,                                   -- 文档内容（文本）
    content_hash VARCHAR(64),                       -- 内容哈希（用于去重）
    
    -- 状态
    status SMALLINT NOT NULL DEFAULT 0,             -- 状态：0-处理中，1-完成，-1-失败
    processing_error TEXT,                          -- 处理错误信息
    
    -- 统计
    chunk_count INTEGER NOT NULL DEFAULT 0,         -- 分块数量
    word_count INTEGER,                             -- 字数统计
    
    -- 元数据
    metadata JSONB DEFAULT '{}',                    -- 元数据
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CONSTRAINT chk_status CHECK (status IN (-1, 0, 1))
);

-- 索引
CREATE INDEX idx_documents_kb_id ON documents(knowledge_base_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_content_hash ON documents(content_hash);
CREATE INDEX idx_documents_created_at ON documents(created_at);

-- 全文索引（关键词检索）
CREATE INDEX idx_documents_content_fts ON documents USING gin(to_tsvector('simple', content));

-- 注释
COMMENT ON TABLE documents IS '知识库文档表';
COMMENT ON COLUMN documents.status IS '状态：0-处理中，1-完成，-1-失败';
COMMENT ON COLUMN documents.content_hash IS '内容哈希（用于去重）';
```

### 2.3.3 文档分块表（document_chunks）

**用途**：存储文档分块及向量（核心表）

```sql
CREATE TABLE document_chunks (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 关联
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    
    -- 分块信息
    chunk_index INTEGER NOT NULL,                   -- 分块索引（在文档中的位置）
    content TEXT NOT NULL,                          -- 分块内容
    
    -- 向量（核心）
    embedding vector(1536),                         -- 向量（1536 维，根据模型调整）
    
    -- 统计
    token_count INTEGER,                            -- Token 数量
    word_count INTEGER,                             -- 字数
    
    -- 元数据
    metadata JSONB DEFAULT '{}',                    -- 元数据（包含页码、章节等）
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CONSTRAINT chk_chunk_index CHECK (chunk_index >= 0)
);

-- 索引
CREATE INDEX idx_chunks_doc_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_kb_id ON document_chunks(knowledge_base_id);
CREATE INDEX idx_chunks_created_at ON document_chunks(created_at);

-- 向量索引（HNSW - 核心性能优化）
CREATE INDEX idx_chunks_embedding_hnsw ON document_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 注释
COMMENT ON TABLE document_chunks IS '文档分块表（含向量）';
COMMENT ON COLUMN document_chunks.embedding IS '文本向量（pgvector）';
COMMENT ON COLUMN document_chunks.chunk_index IS '分块在文档中的索引位置';
```

## 2.4 提示词相关表

### 2.4.1 提示词模板表（prompt_templates）

**用途**：存储提示词模板

```sql
CREATE TABLE prompt_templates (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 关联
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- 允许用户删除后保留模板
    is_system BOOLEAN NOT NULL DEFAULT FALSE,       -- 是否系统预设
    
    -- 模板信息
    name VARCHAR(100) NOT NULL,                     -- 模板名称
    description TEXT,                               -- 描述
    category VARCHAR(50),                           -- 分类：编程/文案/翻译等
    
    -- 内容
    template TEXT NOT NULL,                         -- 模板内容
    variables JSONB DEFAULT '[]',                   -- 变量定义（JSON 数组）
    
    -- 版本
    version VARCHAR(20) DEFAULT '1.0.0',            -- 版本号
    is_latest BOOLEAN NOT NULL DEFAULT TRUE,        -- 是否最新版
    
    -- 使用统计
    usage_count INTEGER NOT NULL DEFAULT 0,         -- 使用次数
    
    -- 状态
    is_active BOOLEAN NOT NULL DEFAULT TRUE,        -- 是否启用
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CONSTRAINT chk_version CHECK (version ~ '^\d+\.\d+\.\d+$')
);

-- 索引
CREATE INDEX idx_prompt_templates_user_id ON prompt_templates(user_id);
CREATE INDEX idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX idx_prompt_templates_is_system ON prompt_templates(is_system);
CREATE INDEX idx_prompt_templates_is_active ON prompt_templates(is_active);

-- 注释
COMMENT ON TABLE prompt_templates IS '提示词模板表';
COMMENT ON COLUMN prompt_templates.variables IS '模板变量定义（JSON 数组）';
```

## 2.5 统计相关表

### 2.5.1 使用记录表（usage_records）

**用途**：记录 API 使用详情

```sql
CREATE TABLE usage_records (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 关联
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    
    -- 使用信息
    model VARCHAR(50) NOT NULL,                     -- 使用的模型
    provider VARCHAR(50) NOT NULL,                  -- Provider
    
    -- Token 统计
    prompt_tokens INTEGER NOT NULL DEFAULT 0,       -- 输入 Token
    completion_tokens INTEGER NOT NULL DEFAULT 0,   -- 输出 Token
    total_tokens INTEGER NOT NULL DEFAULT 0,        -- 总 Token
    
    -- 成本
    cost DECIMAL(10, 6) DEFAULT 0,                  -- 成本（美元）
    
    -- 状态
    status SMALLINT NOT NULL DEFAULT 1,             -- 状态：1-成功，0-失败
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CONSTRAINT chk_status CHECK (status IN (0, 1))
);

-- 索引
CREATE INDEX idx_usage_records_user_id ON usage_records(user_id);
CREATE INDEX idx_usage_records_model ON usage_records(model);
CREATE INDEX idx_usage_records_created_at ON usage_records(created_at);

-- 复合索引（优化统计查询）
CREATE INDEX idx_usage_records_user_date ON usage_records(user_id, created_at);

-- 注释
COMMENT ON TABLE usage_records IS 'API 使用记录表';
COMMENT ON COLUMN usage_records.cost IS '成本（美元）';
```

### 2.5.2 每日统计表（daily_statistics）

**用途**：每日聚合统计

```sql
CREATE TABLE daily_statistics (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 关联
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 统计日期
    stat_date DATE NOT NULL,                        -- 统计日期
    
    -- 请求统计
    total_requests INTEGER NOT NULL DEFAULT 0,      -- 总请求数
    successful_requests INTEGER NOT NULL DEFAULT 0, -- 成功请求数
    failed_requests INTEGER NOT NULL DEFAULT 0,     -- 失败请求数
    
    -- Token 统计
    total_tokens INTEGER NOT NULL DEFAULT 0,        -- 总 Token
    prompt_tokens INTEGER NOT NULL DEFAULT 0,       -- 输入 Token
    completion_tokens INTEGER NOT NULL DEFAULT 0,   -- 输出 Token
    
    -- 成本统计
    total_cost DECIMAL(10, 6) DEFAULT 0,            -- 总成本（美元）
    
    -- 模型分布（JSON）
    model_distribution JSONB DEFAULT '{}',          -- 模型使用分布
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CONSTRAINT chk_requests CHECK (total_requests = successful_requests + failed_requests)
);

-- 索引
CREATE UNIQUE INDEX idx_daily_stats_user_date ON daily_statistics(user_id, stat_date);
CREATE INDEX idx_daily_stats_date ON daily_statistics(stat_date);

-- 注释
COMMENT ON TABLE daily_statistics IS '每日统计表（聚合）';
COMMENT ON COLUMN daily_statistics.model_distribution IS '模型使用分布（JSON）';
```

## 2.6 系统配置表

### 2.6.1 模型配置表（model_configs）

**用途**：配置可用的模型

```sql
CREATE TABLE model_configs (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 模型信息
    provider VARCHAR(50) NOT NULL,                  -- Provider 名称
    model_name VARCHAR(100) NOT NULL,               -- 模型名称
    
    -- API 配置
    api_endpoint VARCHAR(500),                      -- API 端点
    api_key_encrypted TEXT,                         -- API Key（加密存储）
    
    -- 配置
    max_tokens INTEGER DEFAULT 4096,                -- 最大 Token 数
    context_window INTEGER,                         -- 上下文窗口
    cost_per_1k_tokens DECIMAL(10, 6),             -- 每 1k Token 成本
    
    -- 路由配置
    priority INTEGER NOT NULL DEFAULT 0,            -- 优先级（数字越大优先级越高）
    weight INTEGER NOT NULL DEFAULT 1,              -- 权重
    is_active BOOLEAN NOT NULL DEFAULT TRUE,        -- 是否启用
    
    -- 额外配置
    config JSONB DEFAULT '{}',                      -- 额外配置
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CONSTRAINT chk_priority CHECK (priority >= 0),
    CONSTRAINT chk_weight CHECK (weight > 0)
);

-- 索引
CREATE UNIQUE INDEX idx_model_configs_provider_name ON model_configs(provider, model_name);
CREATE INDEX idx_model_configs_is_active ON model_configs(is_active);
CREATE INDEX idx_model_configs_priority ON model_configs(priority);

-- 注释
COMMENT ON TABLE model_configs IS '模型配置表';
COMMENT ON COLUMN model_configs.api_key_encrypted IS 'API Key（加密存储）';
```

---

# 三、数据字典

## 3.1 枚举值定义

### 用户状态（user_status）
| 值 | 说明 |
|---|------|
| 1 | 正常 |
| 0 | 禁用 |

### 会话状态（conversation_status）
| 值 | 说明 |
|---|------|
| 1 | 活跃 |
| 0 | 归档 |
| -1 | 删除 |

### 消息角色（message_role）
| 值 | 说明 |
|---|------|
| system | 系统消息 |
| user | 用户消息 |
| assistant | AI 助手消息 |

### 文档状态（document_status）
| 值 | 说明 |
|---|------|
| 0 | 处理中 |
| 1 | 完成 |
| -1 | 失败 |

## 3.2 公共字段说明

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | UUID | 主键，使用 gen_random_uuid() 生成 |
| created_at | TIMESTAMP WITH TIME ZONE | 创建时间，默认当前时间 |
| updated_at | TIMESTAMP WITH TIME ZONE | 更新时间，默认当前时间 |
| metadata | JSONB | 元数据，存储额外信息 |
| status | SMALLINT | 状态字段，使用 CHECK 约束 |

---

# 四、索引设计说明

## 4.1 索引策略

### 主键索引
- 所有表主键使用 UUID
- 使用 `gen_random_uuid()` 函数生成

### 外键索引
- 所有外键字段创建索引
- 优化 JOIN 查询性能

### 查询条件索引
- WHERE 子句常用字段
- ORDER BY 字段
- LIMIT/OFFSET 分页字段

### 复合索引
- 多条件组合查询
- 覆盖索引减少回表

### 向量索引
- 使用 HNSW 索引
- 参数：m=16, ef_construction=64
- 余弦相似度：vector_cosine_ops

## 4.2 核心索引列表

| 表名 | 索引字段 | 索引类型 | 说明 |
|------|---------|---------|------|
| users | username | B-tree | 唯一索引 |
| users | email | B-tree | 唯一索引 |
| conversations | user_id, created_at | B-tree | 复合索引 |
| messages | conversation_id, created_at | B-tree | 复合索引 |
| document_chunks | embedding | HNSW | 向量索引 |
| documents | content | GIN | 全文索引 |
| usage_records | user_id, created_at | B-tree | 复合索引 |

---

# 五、数据关系图

```
users (用户)
├── api_keys (API Key)
├── conversations (会话)
│   └── messages (消息)
├── knowledge_bases (知识库)
│   └── documents (文档)
│       └── document_chunks (分块 + 向量)
├── prompt_templates (提示词模板)
└── usage_records (使用记录)

model_configs (模型配置) - 独立配置表
daily_statistics (每日统计) - 聚合统计表
```

---

# 六、数据迁移策略

## 6.1 迁移工具

- **工具**：Alembic (SQLAlchemy)
- **版本控制**：Git

## 6.2 迁移步骤

```bash
# 1. 创建迁移
alembic revision -m "create initial tables"

# 2. 编辑迁移脚本
# 在 alembic/versions/ 中编辑生成的脚本

# 3. 应用迁移
alembic upgrade head

# 4. 回滚迁移
alembic downgrade -1
```

## 6.3 初始化数据

```sql
-- 插入系统预设提示词模板
INSERT INTO prompt_templates (name, category, template, is_system, is_latest)
VALUES 
('通用助手', 'general', '你是一个有帮助的 AI 助手...', TRUE, TRUE),
('编程助手', 'coding', '你是一个专业的程序员...', TRUE, TRUE);

-- 插入默认模型配置
INSERT INTO model_configs (provider, model_name, api_endpoint, priority, weight, is_active)
VALUES 
('openai', 'gpt-3.5-turbo', 'https://api.openai.com/v1/chat/completions', 10, 1, TRUE),
('openai', 'gpt-4', 'https://api.openai.com/v1/chat/completions', 5, 1, TRUE),
('deepseek', 'deepseek-chat', 'https://api.deepseek.com/v1/chat/completions', 8, 1, TRUE);
```

---

# 七、性能优化建议

## 7.1 分区策略

当数据量增长时，考虑以下分区：

```sql
-- messages 表按月分区
CREATE TABLE messages_y2024m01 PARTITION OF messages
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- usage_records 表按月分区
CREATE TABLE usage_records_y2024m01 PARTITION OF usage_records
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## 7.2 数据归档

```sql
-- 定期归档 3 个月前的会话
CREATE TABLE conversations_archive (LIKE conversations INCLUDING ALL);

INSERT INTO conversations_archive
SELECT * FROM conversations 
WHERE created_at < CURRENT_DATE - INTERVAL '3 months'
  AND status = 0;

DELETE FROM conversations 
WHERE created_at < CURRENT_DATE - INTERVAL '3 months'
  AND status = 0;
```

## 7.3 清理策略

```sql
-- 定期清理临时数据
DELETE FROM document_chunks 
WHERE created_at < CURRENT_DATE - INTERVAL '30 days'
  AND knowledge_base_id IN (
      SELECT id FROM knowledge_bases WHERE is_active = FALSE
  );
```

---

# 八、安全设计

## 8.1 敏感数据保护

- **密码**：bcrypt 加密存储
- **API Key**：SHA256 哈希存储
- **API Key 加密**：使用 Fernet 对称加密

## 8.2 权限控制

```sql
-- 创建只读用户
CREATE ROLE reader WITH LOGIN PASSWORD 'xxx';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO reader;

-- 创建应用用户
CREATE ROLE app_user WITH LOGIN PASSWORD 'xxx';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
```

## 8.3 审计日志

```sql
-- 启用审计日志扩展
CREATE EXTENSION IF NOT EXISTS pgaudit;

-- 配置审计
SET pgaudit.log = 'write';
SET pgaudit.log_relation = on;
```

---

# 九、备份策略

## 9.1 备份方式

```bash
# 全量备份
pg_dump -U postgres ai_gateway > backup_$(date +%Y%m%d).sql

# 增量备份（WAL 归档）
# 配置 postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'
```

## 9.2 备份频率

- **全量备份**：每日 1 次（凌晨 3 点）
- **增量备份**：实时（WAL 归档）
- **保留策略**：保留 30 天

---

# 附录

## A. pgvector 配置

```sql
-- 安装 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 查看支持的向量维度
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 向量维度选择：
-- text-embedding-ada-002: 1536 维
-- text-embedding-3-small: 1536 维
-- text-embedding-3-large: 3072 维
```

## B. HNSW 索引参数调优

| 参数 | 默认值 | 说明 | 调优建议 |
|------|--------|------|---------|
| m | 16 | 最大连接数 | 数据量大时增加到 32 |
| ef_construction | 64 | 构建时搜索深度 | 追求精度时增加到 128 |
| ef_search | 40 | 查询时搜索深度 | 运行时动态调整 |

```sql
-- 查询时调整 ef_search
SET hnsw.ef_search = 100;
```

---

**文档结束**
