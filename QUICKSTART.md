# 快速开始指南

## 1. 环境准备

### 必需软件
- Python 3.11+
- PostgreSQL 15+ (或使用 Docker)
- Redis 7+ (或使用 Docker)

### 可选软件
- Docker & Docker Compose
- Nginx

## 2. 安装方式

### 方式一：Docker Compose（最简单）

```bash
# 1. 克隆项目
git clone <repository-url>
cd ai-gateway

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，设置你的 API Key

# 3. 一键启动
docker-compose up -d

# 4. 查看日志
docker-compose logs -f app

# 5. 访问服务
# API 文档：http://localhost:8000/docs
# 监控：http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### 方式二：本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动数据库和 Redis
# 可以使用 Docker
docker-compose up -d db redis

# 3. 运行数据库迁移
alembic upgrade head

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env

# 5. 启动应用
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. 访问 http://localhost:8000/docs
```

## 3. 配置说明

### 必需配置

```bash
# .env 文件

# 数据库（Docker 模式）
DATABASE_URL=postgresql://ai_user:ai_password@localhost:5432/ai_gateway

# Redis（Docker 模式）
REDIS_URL=redis://localhost:6379/0

# 安全密钥（生产环境必须修改）
SECRET_KEY=your-super-secret-key-change-in-production

# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-key

# Claude API Key
CLAUDE_API_KEY=sk-your-claude-key
```

### 可选配置

```bash
# 日志级别
LOG_LEVEL=INFO

# 限流配置
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100

# JWT 过期时间（分钟）
JWT_EXPIRATION_MINUTES=1440
```

## 4. 使用示例

### 4.1 注册账号

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 4.2 登录获取 Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 4.3 创建 API Key

```bash
curl -X POST http://localhost:8000/api/v1/auth/api-key \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4.4 调用聊天 API

```bash
# 非流式
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'

# 流式
curl -X POST http://localhost:8000/api/v1/chat/completions \
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

## 5. 数据库迁移

```bash
# 创建新迁移
alembic revision -m "description"

# 应用所有迁移
alembic upgrade head

# 回滚一个版本
alembic downgrade -1

# 查看当前版本
alembic current
```

## 6. 监控和日志

### 查看应用日志

```bash
# Docker 模式
docker-compose logs -f app

# 本地模式
tail -f logs/app.log
```

### 访问监控面板

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- API 文档：http://localhost:8000/docs

### 健康检查

```bash
curl http://localhost:8000/health
```

## 7. 常见问题

### Q: 数据库连接失败？
A: 确保 PostgreSQL 正在运行，检查 DATABASE_URL 配置

### Q: Redis 连接失败？
A: 确保 Redis 正在运行，检查 REDIS_URL 配置

### Q: API Key 无效？
A: 检查 .env 中的 API Key 是否正确，确保没有多余的空格

### Q: 模型不可用？
A: 检查模型配置表，确保模型已启用

## 8. 生产部署建议

1. **使用 HTTPS** - 配置 SSL 证书
2. **修改 SECRET_KEY** - 使用强随机密钥
3. **配置防火墙** - 只开放必要端口
4. **启用限流** - 防止 DDoS 攻击
5. **配置备份** - 定期备份数据库
6. **监控告警** - 配置 Prometheus 告警规则
7. **日志收集** - 使用 ELK 或类似工具
8. **自动扩展** - 使用 Kubernetes 或类似工具

## 9. 性能测试

```bash
# 使用 ab 进行压力测试
ab -n 1000 -c 10 http://localhost:8000/health

# 使用 wrk
wrk -t12 -c400 -d30s http://localhost:8000/health
```

## 10. 下一步

- [ ] 阅读 API 文档：http://localhost:8000/docs
- [ ] 配置你的 AI 模型 Provider
- [ ] 测试聊天功能
- [ ] 配置监控告警
- [ ] 阅读架构文档了解内部实现

---

更多详细文档请参考 [README.md](README.md)
