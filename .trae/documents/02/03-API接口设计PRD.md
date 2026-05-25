# 个人版 AI 基座 - API 接口设计 PRD

**版本**：v1.0  
**创建日期**：2024-01-XX  
**文档类型**：技术设计文档  
**关联文档**：《个人版 AI 基座 PRD.md》、《数据模型设计 PRD.md》

---

# 一、文档概述

## 1.1 文档目的

本文档详细描述个人版 AI 基座的所有 API 接口设计，包括接口路径、请求参数、响应格式、错误码等，作为后端开发、前端对接、测试用例编写的核心依据。

## 1.2 设计规范

- **协议**：HTTP/1.1 或 HTTP/2（推荐）
- **风格**：RESTful API
- **数据格式**：JSON
- **字符编码**：UTF-8
- **认证方式**：JWT Token / API Key

## 1.3 基础路径

```
生产环境：https://api.yourdomain.com/api/v1
开发环境：http://localhost:8000/api/v1
```

---

# 二、通用规范

## 2.1 请求头（Headers）

### 必需头

```http
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
# 或
X-API-Key: <API_KEY>
```

### 可选头

```http
X-Request-ID: <请求 ID>           # 用于链路追踪
X-Client-Version: <客户端版本>     # 客户端版本号
Accept-Language: zh-CN            # 语言偏好
```

## 2.2 响应格式

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "timestamp": 1704067200000,
  "request_id": "req_abc123"
}
```

### 错误响应

```json
{
  "code": 40001,
  "message": "参数错误",
  "errors": [
    {
      "field": "username",
      "message": "用户名不能为空"
    }
  ],
  "timestamp": 1704067200000,
  "request_id": "req_abc123"
}
```

## 2.3 分页参数

### 请求参数

```json
{
  "page": 1,          // 页码（从 1 开始）
  "page_size": 20,    // 每页数量（默认 20，最大 100）
  "sort": "created_at",  // 排序字段
  "order": "desc"     // 排序方向：asc/desc
}
```

### 响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "pagination": {
      "total": 100,
      "page": 1,
      "page_size": 20,
      "total_pages": 5
    }
  }
}
```

## 2.4 认证方式

### JWT Token 认证

**适用场景**：Web 端、移动端

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API Key 认证

**适用场景**：服务器端、CLI 工具

```http
X-API-Key: sk-abc123def456...
```

---

# 三、认证接口

## 3.1 用户注册

**接口**：`POST /api/v1/auth/register`

**描述**：创建新用户账号

### 请求参数

```json
{
  "username": "string, 必填，3-50 字符",
  "email": "string, 必填，邮箱格式",
  "password": "string, 必填，8-50 字符"
}
```

### 请求示例

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "usr_abc123",
    "username": "testuser",
    "email": "test@example.com",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

### 错误码

| 错误码 | 说明 |
|-------|------|
| 40001 | 用户名已存在 |
| 40002 | 邮箱已被注册 |
| 40003 | 密码格式不正确 |

## 3.2 用户登录

**接口**：`POST /api/v1/auth/login`

**描述**：用户登录获取 Token

### 请求参数

```json
{
  "username": "string, 必填",
  "password": "string, 必填"
}
```

### 请求示例

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": "usr_abc123",
      "username": "testuser",
      "email": "test@example.com"
    }
  }
}
```

### 错误码

| 错误码 | 说明 |
|-------|------|
| 40101 | 用户名或密码错误 |
| 40102 | 账号已被禁用 |

## 3.3 刷新 Token

**接口**：`POST /api/v1/auth/refresh`

**描述**：刷新 Access Token

### 请求参数

```json
{
  "refresh_token": "string, 必填"
}
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

## 3.4 获取当前用户信息

**接口**：`GET /api/v1/auth/me`

**描述**：获取当前登录用户信息

### 请求头

```http
Authorization: Bearer <JWT_TOKEN>
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "usr_abc123",
    "username": "testuser",
    "email": "test@example.com",
    "avatar_url": "https://...",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login_at": "2024-01-15T12:00:00Z"
  }
}
```

## 3.5 创建 API Key

**接口**：`POST /api/v1/auth/api-key`

**描述**：创建新的 API Key

### 请求参数

```json
{
  "name": "string, 可选，API Key 名称",
  "rate_limit": "integer, 可选，每分钟限流次数，默认 60",
  "expires_in_days": "integer, 可选，过期天数"
}
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "key_abc123",
    "name": "My API Key",
    "key": "sk-abc123def456...",  // 仅显示一次
    "key_prefix": "sk-abc123",
    "rate_limit": 60,
    "created_at": "2024-01-15T12:00:00Z",
    "expires_at": "2025-01-15T12:00:00Z"
  }
}
```

### 警告

**重要**：API Key 明文仅在创建时返回一次，后续无法查看！

## 3.6 获取 API Key 列表

**接口**：`GET /api/v1/auth/api-keys`

**描述**：获取当前用户的所有 API Key

### 查询参数

```
page: integer, 可选，页码
page_size: integer, 可选，每页数量
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "key_abc123",
        "name": "My API Key",
        "key_prefix": "sk-abc123",
        "is_active": true,
        "created_at": "2024-01-15T12:00:00Z",
        "last_used_at": "2024-01-16T08:00:00Z",
        "expires_at": "2025-01-15T12:00:00Z"
      }
    ],
    "pagination": {
      "total": 3,
      "page": 1,
      "page_size": 20
    }
  }
}
```

## 3.7 撤销 API Key

**接口**：`DELETE /api/v1/auth/api-key/{id}`

**描述**：撤销/删除 API Key

### 路径参数

```
id: string, API Key ID
```

### 响应示例

```json
{
  "code": 0,
  "message": "success"
}
```

---

# 四、对话接口

## 4.1 创建对话（非流式）

**接口**：`POST /api/v1/chat/completions`

**描述**：创建对话请求（非流式）

### 请求参数

```json
{
  "model": "string, 可选，模型名称，默认 gpt-3.5-turbo",
  "messages": [
    {
      "role": "string, 必填，role: system/user/assistant",
      "content": "string, 必填，消息内容"
    }
  ],
  "temperature": "number, 可选，0-2，默认 0.7",
  "max_tokens": "integer, 可选，最大 Token 数",
  "conversation_id": "string, 可选，会话 ID，不传则创建新会话",
  "system_prompt": "string, 可选，系统提示词",
  "stream": "boolean, 可选，默认 false"
}
```

### 请求示例

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7
  }'
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "chatcmpl_abc123",
    "object": "chat.completion",
    "created": 1704067200,
    "model": "gpt-3.5-turbo",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "Hello! How can I help you today?"
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 10,
      "completion_tokens": 12,
      "total_tokens": 22
    },
    "conversation_id": "conv_xyz789"
  }
}
```

## 4.2 创建对话（流式）

**接口**：`POST /api/v1/chat/completions`

**描述**：创建对话请求（流式输出）

### 请求参数

```json
{
  "model": "string, 可选",
  "messages": [],
  "stream": true  // 设置为 true
}
```

### 响应格式（SSE）

```
data: {"id":"chatcmpl_123","choices":[{"delta":{"content":"Hello"}}]}

data: {"id":"chatcmpl_123","choices":[{"delta":{"content":"!"}}]}

data: {"id":"chatcmpl_123","choices":[{"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

### 请求示例（curl）

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "stream": true
  }' \
  --no-buffer
```

## 4.3 获取会话列表

**接口**：`GET /api/v1/conversations`

**描述**：获取当前用户的会话列表

### 查询参数

```
page: integer, 可选，页码
page_size: integer, 可选，每页数量
status: string, 可选，状态过滤：active/archived
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "conv_abc123",
        "title": "讨论编程问题",
        "model": "gpt-3.5-turbo",
        "message_count": 10,
        "total_tokens": 2500,
        "created_at": "2024-01-15T12:00:00Z",
        "updated_at": "2024-01-15T14:00:00Z"
      }
    ],
    "pagination": {
      "total": 25,
      "page": 1,
      "page_size": 20
    }
  }
}
```

## 4.4 获取会话详情

**接口**：`GET /api/v1/conversations/{id}`

**描述**：获取指定会话详情

### 路径参数

```
id: string, 会话 ID
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "conv_abc123",
    "title": "讨论编程问题",
    "model": "gpt-3.5-turbo",
    "system_prompt": "你是一个编程助手",
    "message_count": 10,
    "total_tokens": 2500,
    "created_at": "2024-01-15T12:00:00Z",
    "updated_at": "2024-01-15T14:00:00Z",
    "metadata": {}
  }
}
```

## 4.5 获取会话消息

**接口**：`GET /api/v1/conversations/{id}/messages`

**描述**：获取指定会话的消息列表

### 路径参数

```
id: string, 会话 ID
```

### 查询参数

```
page: integer, 可选
page_size: integer, 可选
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "msg_001",
        "role": "user",
        "content": "如何学习 Python？",
        "tokens": 10,
        "created_at": "2024-01-15T12:00:00Z"
      },
      {
        "id": "msg_002",
        "role": "assistant",
        "content": "学习 Python 的建议...",
        "tokens": 200,
        "model": "gpt-3.5-turbo",
        "latency_ms": 1500,
        "created_at": "2024-01-15T12:00:05Z"
      }
    ],
    "pagination": {
      "total": 10,
      "page": 1,
      "page_size": 20
    }
  }
}
```

## 4.6 删除会话

**接口**：`DELETE /api/v1/conversations/{id}`

**描述**：删除指定会话

### 路径参数

```
id: string, 会话 ID
```

### 响应示例

```json
{
  "code": 0,
  "message": "success"
}
```

---

# 五、知识库接口

## 5.1 创建知识库

**接口**：`POST /api/v1/knowledge`

**描述**：创建新的知识库

### 请求参数

```json
{
  "name": "string, 必填，知识库名称",
  "description": "string, 可选，描述",
  "embedding_model": "string, 可选，默认 text-embedding-ada-002",
  "chunk_size": "integer, 可选，默认 500",
  "chunk_overlap": "integer, 可选，默认 100",
  "is_private": "boolean, 可选，默认 true"
}
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "kb_abc123",
    "name": "我的知识库",
    "description": "个人学习资料",
    "document_count": 0,
    "chunk_count": 0,
    "created_at": "2024-01-15T12:00:00Z"
  }
}
```

## 5.2 获取知识库列表

**接口**：`GET /api/v1/knowledge`

**描述**：获取知识库列表

### 查询参数

```
page: integer, 可选
page_size: integer, 可选
is_private: boolean, 可选
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "kb_abc123",
        "name": "我的知识库",
        "description": "个人学习资料",
        "document_count": 10,
        "chunk_count": 150,
        "is_private": true,
        "created_at": "2024-01-15T12:00:00Z"
      }
    ],
    "pagination": {
      "total": 3,
      "page": 1,
      "page_size": 20
    }
  }
}
```

## 5.3 上传文档

**接口**：`POST /api/v1/knowledge/{id}/documents`

**描述**：向知识库上传文档

### 路径参数

```
id: string, 知识库 ID
```

### 请求参数（multipart/form-data）

```
file: file, 必填，文件（支持 md/txt/pdf）
title: string, 可选，文档标题（默认文件名）
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "doc_abc123",
    "title": "Python 学习笔记",
    "file_name": "python_notes.md",
    "file_size": 10240,
    "status": "processing",  // processing/completed/failed
    "created_at": "2024-01-15T12:00:00Z"
  }
}
```

## 5.4 获取文档列表

**接口**：`GET /api/v1/knowledge/{id}/documents`

**描述**：获取知识库文档列表

### 路径参数

```
id: string, 知识库 ID
```

### 查询参数

```
page: integer, 可选
page_size: integer, 可选
status: integer, 可选，状态过滤
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "doc_abc123",
        "title": "Python 学习笔记",
        "file_name": "python_notes.md",
        "file_size": 10240,
        "status": 1,
        "chunk_count": 15,
        "word_count": 5000,
        "created_at": "2024-01-15T12:00:00Z"
      }
    ],
    "pagination": {
      "total": 10,
      "page": 1,
      "page_size": 20
    }
  }
}
```

## 5.5 删除文档

**接口**：`DELETE /api/v1/knowledge/{kb_id}/documents/{id}`

**描述**：删除知识库文档

### 路径参数

```
kb_id: string, 知识库 ID
id: string, 文档 ID
```

### 响应示例

```json
{
  "code": 0,
  "message": "success"
}
```

## 5.6 检索知识库

**接口**：`POST /api/v1/knowledge/{id}/search`

**描述**：检索知识库内容

### 路径参数

```
id: string, 知识库 ID
```

### 请求参数

```json
{
  "query": "string, 必填，检索问题",
  "top_k": "integer, 可选，返回数量，默认 5",
  "score_threshold": "number, 可选，相似度阈值，默认 0.7",
  "include_metadata": "boolean, 可选，是否返回元数据，默认 true"
}
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "query": "Python 装饰器",
    "results": [
      {
        "document_id": "doc_001",
        "document_title": "Python 学习笔记",
        "chunk_index": 5,
        "content": "Python 装饰器是一种...",
        "score": 0.92,
        "metadata": {
          "page": 1,
          "section": "高级特性"
        }
      }
    ],
    "total": 1,
    "search_time_ms": 45
  }
}
```

---

# 六、提示词接口

## 6.1 获取提示词模板列表

**接口**：`GET /api/v1/prompts`

**描述**：获取提示词模板列表

### 查询参数

```
category: string, 可选，分类过滤
is_system: boolean, 可选，是否系统预设
page: integer, 可选
page_size: integer, 可选
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "prompt_001",
        "name": "通用助手",
        "category": "general",
        "template": "你是一个有帮助的 AI 助手...",
        "variables": [],
        "is_system": true,
        "usage_count": 1520,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "total": 10,
      "page": 1,
      "page_size": 20
    }
  }
}
```

## 6.2 创建提示词模板

**接口**：`POST /api/v1/prompts`

**描述**：创建自定义提示词模板

### 请求参数

```json
{
  "name": "string, 必填，模板名称",
  "description": "string, 可选，描述",
  "category": "string, 可选，分类",
  "template": "string, 必填，模板内容",
  "variables": [
    {
      "name": "role_name",
      "type": "string",
      "required": true
    }
  ]
}
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "prompt_abc123",
    "name": "编程助手",
    "category": "coding",
    "template": "你是一个专业的程序员...",
    "variables": [],
    "created_at": "2024-01-15T12:00:00Z"
  }
}
```

## 6.3 更新提示词模板

**接口**：`PUT /api/v1/prompts/{id}`

**描述**：更新提示词模板

### 路径参数

```
id: string, 模板 ID
```

### 请求参数

```json
{
  "name": "string, 可选",
  "template": "string, 可选",
  "description": "string, 可选"
}
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "prompt_abc123",
    "name": "编程助手 V2",
    "version": "2.0.0",
    "updated_at": "2024-01-16T12:00:00Z"
  }
}
```

## 6.4 删除提示词模板

**接口**：`DELETE /api/v1/prompts/{id}`

**描述**：删除提示词模板

### 路径参数

```
id: string, 模板 ID
```

### 响应示例

```json
{
  "code": 0,
  "message": "success"
}
```

---

# 七、模型接口

## 7.1 获取可用模型列表

**接口**：`GET /api/v1/models`

**描述**：获取当前可用的模型列表

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "openai/gpt-3.5-turbo",
        "name": "gpt-3.5-turbo",
        "provider": "openai",
        "max_tokens": 4096,
        "context_window": 16385,
        "cost_per_1k_tokens": 0.0015,
        "is_active": true
      },
      {
        "id": "openai/gpt-4",
        "name": "gpt-4",
        "provider": "openai",
        "max_tokens": 8192,
        "context_window": 8192,
        "cost_per_1k_tokens": 0.03,
        "is_active": true
      },
      {
        "id": "deepseek/deepseek-chat",
        "name": "deepseek-chat",
        "provider": "deepseek",
        "max_tokens": 4096,
        "context_window": 32768,
        "cost_per_1k_tokens": 0.001,
        "is_active": true
      }
    ]
  }
}
```

## 7.2 设置默认模型

**接口**：`POST /api/v1/models/default`

**描述**：设置用户默认模型

### 请求参数

```json
{
  "model_id": "string, 必填，模型 ID"
}
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "default_model": "openai/gpt-3.5-turbo"
  }
}
```

---

# 八、统计接口

## 8.1 获取使用统计

**接口**：`GET /api/v1/usage/statistics`

**描述**：获取使用统计信息

### 查询参数

```
start_date: string, 可选，开始日期（YYYY-MM-DD）
end_date: string, 可选，结束日期（YYYY-MM-DD）
group_by: string, 可选，分组：day/week/month/model
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "period": {
      "start_date": "2024-01-01",
      "end_date": "2024-01-31"
    },
    "summary": {
      "total_requests": 1520,
      "total_tokens": 250000,
      "total_cost": 12.5,
      "average_latency_ms": 1500
    },
    "by_model": [
      {
        "model": "gpt-3.5-turbo",
        "requests": 1200,
        "tokens": 200000,
        "cost": 8.0
      },
      {
        "model": "gpt-4",
        "requests": 320,
        "tokens": 50000,
        "cost": 4.5
      }
    ],
    "daily_stats": [
      {
        "date": "2024-01-15",
        "requests": 50,
        "tokens": 8000,
        "cost": 0.4
      }
    ]
  }
}
```

## 8.2 获取使用记录列表

**接口**：`GET /api/v1/usage/records`

**描述**：获取详细使用记录

### 查询参数

```
page: integer, 可选
page_size: integer, 可选
model: string, 可选，模型过滤
start_date: string, 可选
end_date: string, 可选
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "usage_001",
        "model": "gpt-3.5-turbo",
        "provider": "openai",
        "prompt_tokens": 100,
        "completion_tokens": 200,
        "total_tokens": 300,
        "cost": 0.0015,
        "status": 1,
        "created_at": "2024-01-15T12:00:00Z"
      }
    ],
    "pagination": {
      "total": 1520,
      "page": 1,
      "page_size": 20
    }
  }
}
```

---

# 九、健康检查接口

## 9.1 健康检查

**接口**：`GET /health`

**描述**：服务健康检查

### 响应示例

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": 1704067200
}
```

## 9.2 详细健康检查

**接口**：`GET /health/detailed`

**描述**：详细健康检查（包含各组件状态）

### 响应示例

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": 1704067200,
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 5
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 2
    },
    "openai": {
      "status": "healthy",
      "latency_ms": 150
    }
  }
}
```

---

# 十、错误码规范

## 10.1 错误码分类

| 错误码范围 | 分类 |
|----------|------|
| 10000-19999 | 认证相关 |
| 20000-29999 | 用户相关 |
| 30000-39999 | 对话相关 |
| 40000-49999 | 知识库相关 |
| 50000-59999 | 模型相关 |
| 60000-69999 | 系统相关 |

## 10.2 通用错误码

| 错误码 | HTTP 状态码 | 说明 |
|-------|-----------|------|
| 0 | 200 | 成功 |
| 10001 | 400 | 参数错误 |
| 10002 | 401 | 未认证 |
| 10003 | 403 | 无权限 |
| 10004 | 404 | 资源不存在 |
| 10005 | 500 | 服务器内部错误 |
| 10006 | 503 | 服务不可用 |

## 10.3 业务错误码

### 认证相关（1xxxx）

| 错误码 | 说明 |
|-------|------|
| 10101 | Token 无效或过期 |
| 10102 | API Key 无效 |
| 10103 | 账号已被禁用 |
| 10201 | 用户名已存在 |
| 10202 | 邮箱已被注册 |
| 10203 | 密码格式不正确 |

### 对话相关（3xxxx）

| 错误码 | 说明 |
|-------|------|
| 30101 | 会话不存在 |
| 30102 | 消息内容为空 |
| 30103 | 超出上下文窗口限制 |
| 30201 | 模型不可用 |
| 30202 | Provider 调用失败 |

### 知识库相关（4xxxx）

| 错误码 | 说明 |
|-------|------|
| 40101 | 知识库不存在 |
| 40102 | 文档格式不支持 |
| 40103 | 文档正在处理中 |
| 40201 | 向量检索失败 |
| 40202 | Embedding 模型调用失败 |

---

# 十一、限流策略

## 11.1 限流规则

| 接口类型 | 限流规则 | 说明 |
|---------|---------|------|
| 认证接口 | 10 次/分钟 | 防止暴力破解 |
| 对话接口 | 60 次/分钟 | 默认限流 |
| 知识库接口 | 30 次/分钟 | 上传/检索 |
| 统计接口 | 100 次/分钟 | 查询类接口 |

## 11.2 限流响应

```json
{
  "code": 40301,
  "message": "请求过于频繁，请稍后再试",
  "retry_after": 60
}
```

---

# 十二、版本管理

## 12.1 版本号规则

- 格式：`vMAJOR.MINOR.PATCH`
- 示例：`v1.0.0`

## 12.2 版本兼容性

- **向后兼容**：小版本更新（MINOR）
- **破坏性变更**：大版本更新（MAJOR）
- **废弃策略**：提前 1 个版本公告

## 12.3 版本切换

```http
# 通过 URL 路径指定版本
/api/v1/chat/completions
/api/v2/chat/completions

# 或通过 Header 指定
X-API-Version: v1
```

---

# 附录

## A. cURL 示例集合

### 完整对话流程

```bash
# 1. 注册
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# 2. 登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# 3. 创建 API Key
curl -X POST http://localhost:8000/api/v1/auth/api-key \
  -H "Authorization: Bearer <TOKEN>"

# 4. 对话
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "X-API-Key: sk-abc123" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello!"}]}'
```

## B. SDK 示例

### Python SDK

```python
from ai_gateway import AIGateway

client = AIGateway(api_key="sk-abc123")

# 对话
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)

# 流式对话
stream = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True
)

for chunk in stream:
    print(chunk.choices[0].delta.content, end="")
```

---

**文档结束**
