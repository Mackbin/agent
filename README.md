# AI Gateway - 统一的 AI 模型接入平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)

一个高性能、可扩展的 AI 模型统一接入平台，整合多个第三方 AI 模型 API（OpenAI、Claude 等），提供标准化的接口、智能路由、负载均衡、监控告警等功能。

## ✨ 特性

### 核心功能
- 🔄 **统一接口** - 标准化的 RESTful API，兼容 OpenAI 格式
- 🎯 **智能路由** - 基于延迟、成本、可靠性的多策略路由
- ⚡ **流式响应** - 完整的 SSE（Server-Sent Events）支持
- 🔐 **认证授权** - JWT Token + API Key 双重认证
- 📊 **使用统计** - 详细的 Token 使用和成本统计
- 💬 **会话管理** - 完整的对话历史和上下文管理

### 高可用特性
- 🛡️ **熔断降级** - 自动熔断故障服务，支持降级策略
- ⚖️ **负载均衡** - 多种负载均衡策略（轮询、最少连接、加权等）
- 🔄 **故障转移** - 自动故障检测和转移
- 📈 **实时监控** - Prometheus + Grafana 监控告警

### 支持的模型提供商
- ✅ OpenAI (GPT-3.5, GPT-4, GPT-4 Turbo)
- ✅ Anthropic Claude (Claude 2, Claude 3)
- 🔄 百度文心一言（开发中）
- 🔄 阿里通义千问（开发中）
- 🔄 腾讯混元（开发中）

## 🚀 快速开始

### 环境要求
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose（可选）

### 方式一：Docker Compose（推荐）

1. **克隆项目**
```bash
git clone https://github.com/yourusername/ai-gateway.git
cd ai-gateway
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和 API Key
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **访问服务**
- API 服务：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 监控面板：http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### 方式二：本地开发

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置数据库**
```bash
# 创建数据库
createdb ai_gateway

# 运行迁移
alembic upgrade head
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件
```

4. **启动服务**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📖 API 使用示例

### 1. 用户注册
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 2. 用户登录
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 3. 创建 API Key
```bash
curl -X POST "http://localhost:8000/api/v1/auth/api-key" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### 4. 聊天完成（非流式）
```bash
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7
  }'
```

### 5. 聊天完成（流式）
```bash
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "stream": true
  }' \
  --no-buffer
```

### 6. 获取会话列表
```bash
curl -X GET "http://localhost:8000/api/v1/conversations" \
  -H "X-API-Key: YOUR_API_KEY"
```

## 🏗️ 架构设计

### 系统架构
```
┌─────────────┐
│  客户端层   │
│ Web/Mobile  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Nginx     │ ← 负载均衡、限流
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  FastAPI    │ ← 应用服务
│   App       │
└──────┬──────┘
       │
       ├──────────┬──────────┐
       ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│PostgreSQL│ │ Redis   │ │Prometheus│
│ 数据库   │ │ 缓存    │ │ 监控     │
└─────────┘ └─────────┘ └─────────┘
```

### 核心模块
- **app/main.py** - 应用入口和配置
- **app/config.py** - 配置管理
- **app/models.py** - 数据模型
- **app/schemas.py** - Pydantic 模式
- **app/auth.py** - 认证授权
- **app/database.py** - 数据库连接
- **app/redis.py** - Redis 连接
- **app/services/** - 业务服务层
  - `user_service.py` - 用户服务
  - `ai_router.py` - AI 路由服务
  - `conversation_service.py` - 对话服务
- **app/providers/** - 模型提供商适配器
  - `base.py` - 基类定义
  - `openai.py` - OpenAI 适配
  - `claude.py` - Claude 适配
- **app/routers/** - API 路由
  - `auth.py` - 认证路由
  - `chat.py` - 聊天路由
  - `conversations.py` - 会话路由
  - `models.py` - 模型路由

## 📊 监控指标

### 核心指标
- `app_requests_total` - 总请求数
- `app_request_latency_seconds` - 请求延迟
- `up` - 服务健康状态

### Grafana 仪表板
导入预定义的仪表板（ID: 12345）或自定义仪表板。

## 🔧 配置说明

### 环境变量
```bash
# 应用配置
APP_NAME=AI Gateway
APP_ENV=production
DEBUG=false
SECRET_KEY=your-secret-key

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/ai_gateway
DATABASE_POOL_SIZE=10

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# 模型提供商配置
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1

CLAUDE_API_KEY=sk-xxx
CLAUDE_BASE_URL=https://api.anthropic.com/v1

# 限流配置
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100
```

## 🛠️ 开发指南

### 添加新的模型提供商

1. **创建 Provider 类**
```python
# app/providers/your_provider.py
from app.providers.base import BaseProvider

class YourProvider(BaseProvider):
    name = "your_provider"
    
    async def chat_completion(self, ...):
        # 实现聊天逻辑
        pass
    
    async def chat_completion_stream(self, ...):
        # 实现流式逻辑
        pass
```

2. **注册 Provider**
```python
# app/main.py
from app.providers.your_provider import YourProvider

ai_router.register_provider("your_provider", provider)
```

3. **添加模型配置**
```sql
INSERT INTO model_configs (provider, model_name, is_active, weight)
VALUES ('your_provider', 'your-model', true, 1);
```

## 📝 数据库迁移

```bash
# 创建新迁移
alembic revision -m "add new feature"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history
```

## 🧪 测试

```bash
# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html
```

## 📈 性能优化

- 使用连接池管理数据库连接
- Redis 缓存热点数据
- 异步 IO 处理提高并发能力
- Nginx 反向代理和负载均衡
- Gzip 压缩减少传输大小

## 🔒 安全建议

1. **生产环境必须修改 SECRET_KEY**
2. **使用 HTTPS** - 配置 SSL 证书
3. **限制 API Key 权限** - 最小权限原则
4. **定期轮换密钥** - 定期更新 API Key
5. **启用限流** - 防止 DDoS 攻击
6. **监控异常** - 及时发现和处理异常

## 📋 待办事项

- [ ] 添加更多模型提供商（文心一言、通义千问等）
- [ ] 实现 Token 缓存机制
- [ ] 添加请求重试机制
- [ ] 实现更复杂的路由策略
- [ ] 添加管理后台界面
- [ ] 支持多模态模型
- [ ] 添加计费系统
- [ ] 完善单元测试

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📞 联系方式

- Email: your.email@example.com
- GitHub Issues: [提交 Issue](https://github.com/yourusername/ai-gateway/issues)

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Pydantic](https://docs.pydantic.dev/)
- [Prometheus](https://prometheus.io/)
- [Grafana](https://grafana.com/)

---

**注意**: 这是一个学习项目，生产使用请根据实际情况进行调整和优化。
