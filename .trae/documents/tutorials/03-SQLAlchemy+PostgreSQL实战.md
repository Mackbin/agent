# SQLAlchemy + PostgreSQL 完整实战 — 后端数据持久化核心能力

> **目标读者**：有前端经验，想系统掌握 Python 后端数据库开发
> 
> **核心目标**：学完后能独立设计数据库表结构、编写复杂查询、优化性能
> 
> **预计时间**：4-5 小时（含环境搭建和实践）

---

## 目录

- [第一章：为什么选 PostgreSQL？（前端视角）](#第一章为什么选-postgresql前端视角)
- [第二章：环境准备与快速上手](#第二章环境准备与快速上手)
- [第三章：SQL 基础速查 — 你必须掌握的 SQL](#第三章sql-基础速查--你必须掌握的-sql)
- [第四章：SQLAlchemy ORM — 用 Python 操作数据库](#第四章sqlalchemy-orm--用-python-操作数据库)
- [第五章：模型设计与关联关系](#第五章模型设计与关联关系)
- [第六章：CRUD 完整实现](#第六章crud-完整实现)
- [第七章：复杂查询实战](#第七章复杂查询实战)
- [第八章：事务与并发控制](#第八章事务与并发控制)
- [第九章：pgvector 向量操作](#第九章pgvector-向量操作)
- [第十章：性能优化](#第十章性能优化)
- [第十一章：综合项目 — 完整的诊所数据层](#第十一章综合项目--完整的诊所数据层)
- [验收标准](#验收标准)

---

## 第一章：为什么选 PostgreSQL？（前端视角）

### 1.1 主流数据库对比

```
你作为前端转后端，会遇到的数据库选择：

┌──────────────┬──────────────┬──────────────┬──────────────┐
│              │   MySQL      │ PostgreSQL   │   MongoDB    │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 类型         │ 关系型       │ 关系型       │ 文档型        │
│ 适用场景     │ 传统Web应用  │ 复杂查询/AI  │ 快速原型      │
│ JSON支持     │ 一般         │ 强（原生JSONB）│ 天生JSON     │
│ 向量搜索     │ 需要插件     │ ✅ pgvector  │ ❌           │
│ 全文检索     │ 一般         │ 强（内置）    │ 一般          │
│ 学习曲线     │ 低           │ 中           │ 低           │
│ AI生态兼容性 │ 中           │ 🔴🔴🔴最好   │ 差           │
│ 大厂使用     │ 阿里/字节    │ 腾讯/华为    │ 小公司多      │
└──────────────┴──────────────┴──────────────┴──────────────┘

你的情况：做 AI 应用 → **PostgreSQL 是唯一正确选择**
原因：
1. pgvector = 向量数据库内置，RAG 必需
2. JSONB 类型 = 存储灵活数据（症状字典等）
3. 强大的查询能力 = 复杂分析场景
4. 开源免费 = 个人项目零成本
```

### 1.2 前端类比理解数据库概念

| 数据库概念 | 前端类比 | 说明 |
|-----------|---------|------|
| **Table（表）** | TypeScript Interface | 定义数据结构 |
| **Row（行）** | Object 实例 | 一条具体数据 |
| **Column（列）** | Property 字段 | 数据的一个属性 |
| **Primary Key** | id: string (uuid) | 唯一标识符 |
| **Foreign Key** | 引用其他对象的 ID | 关联关系 |
| **Index** | 搜索索引 | 加速查询 |
| **Transaction** | 批量操作的原子性 | 要么全成功要么全失败 |
| **JOIN** | 展开关联对象 | 合并两张表的数据 |
| **Migration** | Schema 变更脚本 | 表结构的版本管理 |

---

## 第二章：环境准备与快速上手

### 2.1 安装 PostgreSQL（二选一）

#### 方式A：Docker（推荐，最简单）

```bash
# 创建 docker-compose.yml（如果还没有）
# 或直接运行：

docker run -d \
  --name postgres-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=agent_db \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  pgvector/pgvector:pg16

# 等待启动（约3-5秒）
docker ps  # 看到 postgres-db 在运行就 OK

# 测试连接
docker exec -it postgres-db psql -U postgres -d agent_db -c "SELECT version();"
# 应该输出 PostgreSQL 版本信息
```

#### 方式B：Homebrew（Mac 本地安装）

```bash
brew install postgresql@16
brew services start postgresql@16

createdb agent_db
psql agent_db

# 进入后执行：
CREATE EXTENSION IF NOT EXISTS vector;
\q  # 退出
```

### 2.2 安装 Python 依赖

```bash
cd your_project
source venv/bin/activate  # 激活虚拟环境

pip install sqlalchemy[asyncio]
pip install asyncpg        # 异步驱动（推荐）
pip install psycopg2-binary # 同步驱动（备选）
pip install pgvector        # 向量扩展
pip install alembic         # 数据库迁移工具
pip install python-dotenv   # 环境变量

# 验证
python -c "
import sqlalchemy, asyncpg, pgvector, alembic
print('✅ 所有依赖安装成功')
"
```

### 2.3 配置数据库连接

更新 `.env` 文件：

```bash
# .env

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_db
# 格式说明：postgresql+asyncpg://用户名:密码@主机:端口/数据库名

# 同步连接（用于 Alembic 迁移）
SYNC_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agent_db
```

创建 `app/database.py`：

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,  # True 时打印所有 SQL（调试用，生产关掉）
    pool_size=10,             # 连接池大小
    max_overflow=20,          # 最大溢出连接数
    pool_pre_ping=True,       # 连接前先检测是否存活
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,   # 提交后不过期，允许访问属性
)


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


async def get_session() -> AsyncSession:
    """FastAPI 依赖注入用 — 每个请求一个 session"""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """初始化数据库（创建所有表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")
```

### 2.4 第一个测试：连接数据库

创建 `test_db_connection.py`：

```python
"""
测试数据库连接

运行：python test_db_connection.py
"""

import asyncio
from sqlalchemy import text
from app.database import engine


async def test_connection():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"✅ 数据库连接成功！")
            print(f"   版本: {version}")
            
            # 测试 pgvector 扩展
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            print("   pgvector 扩展已启用")
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())
```

运行测试：

```bash
python test_db_connection.py

# 预期输出：
# ✅ 数据库连接成功！
#    版本: PostgreSQL 16.x ...
#    pgvector 扩展已启用
```

---

## 第三章：SQL 基础速查 — 你必须掌握的 SQL

> **重要**：即使你用 ORM，也必须懂 SQL！ORM 只是帮你写 SQL 的工具。
> 当遇到性能问题时，你需要看懂底层 SQL 来优化。

### 3.1 CRUD SQL 对照表

```sql
-- ════════════════════════════════════
-- CREATE（创建）
-- ════════════════════════════════════

INSERT INTO patients (name, gender, age, phone, chief_complaint)
VALUES ('张三', '男', 35, '13800138000', '失眠三个月');

-- 返回插入的数据（PostgreSQL 特有）
INSERT INTO patients (name, gender, age) 
VALUES ('李四', '女', 28)
RETURNING *;


-- ════════════════════════════════════
-- READ（读取）
-- ════════════════════════════════════

-- 查询全部
SELECT * FROM patients;

-- 条件查询
SELECT * FROM patients WHERE age > 30 AND gender = '男';

-- 模糊搜索
SELECT * FROM patients WHERE name LIKE '%张%';

-- 排序 + 限制
SELECT * FROM patients ORDER BY created_at DESC LIMIT 20;


-- ════════════════════════════════════
-- UPDATE（更新）
-- ════════════════════════════════════

UPDATE patients 
SET age = 36, updated_at = NOW()
WHERE id = 1;

-- 更新并返回
UPDATE patients SET name = '张三丰' WHERE id = 1 RETURNING *;


-- ════════════════════════════════════
-- DELETE（删除）
-- ════════════════════════════════════

DELETE FROM patients WHERE id = 1;

-- 删除并返回
DELETE FROM patients WHERE age > 100 RETURNING *;
```

### 3.2 JOIN — 关联查询（后端天天用）

```sql
-- 场景：患者 + 对话 + 消息 三表联查

-- 内连接（只返回匹配的数据）
SELECT 
    u.name AS 用户名,
    c.title AS 对话标题,
    m.content AS 消息内容,
    m.created_at AS 发送时间
FROM users u
INNER JOIN conversations c ON c.user_id = u.id
INNER JOIN messages m ON m.conversation_id = c.id
WHERE u.id = 1
ORDER BY m.created_at DESC;


-- 左连接（保留左表所有数据，右边没匹配的填 NULL）
SELECT 
    p.name AS 患者姓名,
    COUNT(m.id) AS 消息数量
FROM patients p
LEFT JOIN messages m ON m.patient_id = p.id
GROUP BY p.id, p.name
ORDER BY 消息数量 DESC;
```

### 3.3 聚合统计（数据看板必备）

```sql
-- 基础统计
SELECT 
    COUNT(*) AS 总患者数,
    AVG(age) AS 平均年龄,
    MAX(age) AS 最大年龄,
    MIN(age) AS 最小年龄
FROM patients
WHERE is_active = true;


-- 按分组统计
SELECT 
    gender AS 性别,
    COUNT(*) AS 人数,
    ROUND(AVG(age), 1) AS 平均年龄
FROM patients
GROUP BY gender;


-- 时间维度统计（最近30天新增对话）
SELECT 
    DATE(created_at) AS 日期,
    COUNT(*) AS 新增对话数,
    COUNT(DISTINCT user_id) AS 活跃用户数
FROM conversations
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY 日期 DESC;


-- HAVING 过滤分组结果
SELECT 
    doctor_id AS 医生ID,
    COUNT(*) AS 接诊数
FROM consultations
GROUP BY doctor_id
HAVING COUNT(*) >= 10  -- 只看接诊>=10次的医生
ORDER BY 接诊数 DESC;
```

### 3.4 子查询和 CTE

```sql
-- 子查询：找出"就诊次数最多的患者"
SELECT * FROM patients 
WHERE id = (
    SELECT patient_id FROM consultations 
    GROUP BY patient_id 
    ORDER BY COUNT(*) DESC 
    LIMIT 1
);


-- CTE（更清晰）：最近活跃的用户及其最新消息
WITH 最近活跃 AS (
    SELECT user_id, MAX(created_at) AS 最后活跃时间
    FROM conversations
    WHERE created_at >= NOW() - INTERVAL '7 days'
    GROUP BY user_id
),
用户信息 AS (
    SELECT u.*, a.最后活跃时间
    FROM users u
    JOIN 最近活跃 a ON a.user_id = u.id
)
SELECT * FROM 用户信息 ORDER BY 最后活跃时间 DESC;
```

### 3.5 窗口函数（进阶但有用）

```sql
-- ROW_NUMBER：给每个患者的消息编号
SELECT 
    patient_id,
    content,
    created_at,
    ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY created_at DESC) AS 最新排序
FROM messages
WHERE patient_id = 1;


-- RANK / DENSE_RANK：患者就诊次数排名
SELECT 
    patient_id,
    COUNT(*) AS 就诊次数,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS 排名
FROM consultations
GROUP BY patient_id;
```

---

## 第四章：SQLAlchemy ORM — 用 Python 操作数据库

### 4.1 什么是 ORM？

```
ORM = Object Relational Mapping（对象关系映射）

作用：让你用 Python 类/对象来操作数据库，而不是手写 SQL

对比：

❌ 手写 SQL：
cursor.execute("INSERT INTO patients (name, age) VALUES (%s, %s)", ("张三", 35))

✅ ORM 方式：
patient = Patient(name="张三", age=35)
session.add(patient)
session.commit()


优势：
- 类型安全（IDE 能提示字段名）
- 防止 SQL 注入（自动参数化）
- 数据库无关（换数据库只需改连接字符串）
- 代码更 Pythonic

劣势：
- 复杂查询不如原生 SQL 直观
- 有一定性能开销（通常可忽略）
- 需要学习 ORM 的 API
```

### 4.2 定义模型（= TypeScript Interface）

创建 `app/models/patient.py`：

```python
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Patient(Base):
    """患者模型"""
    
    __tablename__ = "patients"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 基本信息
    name = Column(String(100), nullable=False, index=True)
    gender = Column(String(10), nullable=False)  # 男/女
    age = Column(Integer, nullable=False)
    phone = Column(String(20), unique=True, index=True)
    
    # 医疗信息
    chief_complaint = Column(Text, nullable=False)  # 主诉
    symptoms = Column(JSON, default=list)  # ["失眠", "头晕"] → 自动存为 JSON
    diagnosis = Column(Text)  # 诊断
    prescription = Column(Text)  # 处方
    
    # 标签和分类
    tags = Column(ARRAY(String), default=list)  # ["慢性病", "复诊"]
    
    # 状态和时间戳
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow  # 更新时自动刷新
    )
    
    # 关联关系（后面详细讲）
    # conversations = relationship("Conversation", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient {self.name} ({self.gender}, {self.age}岁)>"
    
    @property
    def display_name(self) -> str:
        """计算属性 — 类似 Vue computed"""
        mask_name = self.name[0] + "**"
        return f"{mask_name}({self.age}{('岁' if self.age else '')})"
```

### 4.3 同步 vs 异步 SQLAlchemy

```python
# ══════════════════════════════════════════
# 同步方式（传统，简单但不适合高并发）
# ══════════════════════════════════════════

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

sync_engine = create_engine("postgresql://user:pass@localhost/db")
SyncSession = sessionmaker(bind=sync_engine)

def sync_example():
    session = SyncSession()
    
    # 查询（阻塞）
    patient = session.query(Patient).filter_by(id=1).first()
    
    session.close()

# ══════════════════════════════════════════
# 异步方式（FastAPI 推荐，非阻塞）
# ══════════════════════════════════════════

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

async_engine = create_async_engine("postgresql+asyncpg://...")
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession)

async def async_example():
    async with AsyncSessionLocal() as session:
        
        # select() 是异步的，不会阻塞事件循环
        from sqlalchemy import select
        stmt = select(Patient).where(Patient.id == 1)
        result = await session.execute(stmt)
        patient = result.scalar_one_or_none()
        
        # 或者用更简洁的方式
        patient = await session.get(Patient, 1)


# ⚠️ 重要区别：
# 1. 连接字符串不同：postgresql:// vs postgresql+asyncpg://
# 2. 所有 DB 操作都要 await
# 3. 用 select() 代替 query()
# 4. 用 execute().scalar()/.scalars() 获取结果
```

---

## 第五章：模型设计与关联关系

### 5.1 一对多关系（最常见的）

```
场景：一个用户可以有多个对话

User (1) ──────< Conversation (N)
                    │
                    ├─< Message (N)
```

```python
# app/models/user.py
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True)
    role = Column(String(20), default="user")  # admin/doctor/assistant/patient
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联：一个用户有多个对话
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",  # 删除用户时级联删除对话
        lazy="selectin",  # 预加载（避免 N+1 问题）
    )


# app/models/conversation.py
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200))
    status = Column(String(20), default="active")  # active/archived/deleted
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 反向关联：属于哪个用户
    user = relationship("User", back_populates="conversations")
    
    # 一个对话有多条消息
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        lazy="selectin",
    )


# app/models/message.py
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user/assistant/system/tool
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    model_used = Column(String(50))
    latency_ms = Column(Integer, default=0)
    metadata_ = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")
```

### 5.2 使用关联关系查询

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def demo_relationships(session: AsyncSession):
    
    # ════════════════════════════════════
    # 1. 查询用户及其所有对话（预加载）
    # ════════════════════════════════════
    stmt = (
        select(User)
        .where(User.username == "zhangsan")
        .options(selectinload(User.conversations))  # 预加载对话
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        print(f"用户: {user.username}")
        for conv in user.conversations:  # 已经加载好了，不再查询
            print(f"  对话: {conv.title} ({conv.message_count}条消息)")
    
    
    # ════════════════════════════════════
    # 2. 查询对话及其所有消息
    # ════════════════════════════════════
    conv_stmt = (
        select(Conversation)
        .where(Conversation.id == some_uuid)
        .options(selectinload(Conversation.messages).selectinload(Message.conversation))
    )
    result = await session.execute(conv_stmt)
    conversation = result.scalar_one_or_none()
    
    if conversation:
        for msg in conversation.messages:
            print(f"[{msg.role}] {msg.content[:50]}...")


# ════════════════════════════════════
# Lazy Loading 策略对比
# ════════════════════════════════════

# lazy="select"（默认）— 访问时才查询（可能产生 N+1 问题）
user = await session.get(User, 1)
convs = user.conversations  # 这里触发额外的 SQL 查询

# lazy="selectin" — 查询主对象时自动 JOIN 加载关联（推荐用于确定要用的关联）
stmt = select(User).options(selectinload(User.conversations))

# lazy="joined" — 用一条 SQL JOIN 查询
stmt = select(User).options(joinedload(User.conversations))

# lazy="noload" — 不加载（节省资源）
stmt = select(User).options(noload(User.conversations))

# lazy="raise" — 访问未加载的关联时抛异常（强制显式加载）
```

### 5.3 多对多关系

```
场景：一个知识库可以包含多个标签，一个标签可以属于多个知识库

KnowledgeBase <──> Tag
```

```python
# app/models/tag.py
class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    
    # 多对多关联
    knowledge_bases = relationship(
        "KnowledgeBase",
        secondary="knowledge_base_tags",  # 中间表
        back_populates="tags",
    )


# app/models/knowledge_base.py
class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    category = Column(String(50))
    
    tags = relationship(
        "Tag",
        secondary="knowledge_base_tags",
        back_populates="knowledge_bases",
    )


# 中间表（association table）
from sqlalchemy import Table, Column, ForeignKey, Integer

knowledge_base_tags = Table(
    "knowledge_base_tags",
    Base.metadata,
    Column("knowledge_base_id", UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)
```

---

## 第六章：CRUD 完整实现

### 6.1 创建 Service 层（封装业务逻辑）

创建 `app/services/patient_service.py`：

```python
import uuid
from typing import Optional, Tuple, List
from datetime import datetime
from sqlalchemy import select, func, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.patient import Patient
from app.models.schemas import PatientCreate, PatientUpdate, PaginatedResponse


class PatientService:
    """患者服务 — 封装所有患者相关的数据库操作"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ════════════════════════════════════
    # Create
    # ════════════════════════════════════
    
    async def create(self, data: PatientCreate) -> Patient:
        """创建患者"""
        now = datetime.utcnow()
        
        patient = Patient(
            **data.model_dump(),
            id=uuid.uuid4(),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        
        try:
            self.db.add(patient)
            await self.db.commit()
            await self.db.refresh(patient)
            return patient
            
        except IntegrityError as e:
            await self.db.rollback()
            if "phone" in str(e):
                raise ValueError("该手机号已被注册")
            raise ValueError("数据冲突，请检查输入")
    
    # ════════════════════════════════════
    # Read
    # ════════════════════════════════════
    
    async def get_by_id(self, patient_id: uuid.UUID) -> Optional[Patient]:
        """根据 ID 获取"""
        return await self.db.get(Patient, patient_id)
    
    async def get_by_phone(self, phone: str) -> Optional[Patient]:
        """根据手机号获取"""
        stmt = select(Patient).where(Patient.phone == phone)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_paginated(
        self,
        page: int = 1,
        size: int = 20,
        keyword: Optional[str] = None,
        gender: Optional[str] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        is_active: bool = True,
    ) -> Tuple[List[Patient], int]:
        """
        分页列表
        
        Returns:
            (患者列表, 总数)
        """
        # 构建过滤条件
        conditions = [Patient.is_active == is_active]
        
        if keyword:
            search_filter = or_(
                Patient.name.ilike(f"%{keyword}%"),
                Patient.chief_complaint.ilike(f"%{keyword}%"),
                Patient.phone.ilike(f"%{keyword}%"),
            )
            conditions.append(search_filter)
        
        if gender:
            conditions.append(Patient.gender == gender)
        
        if min_age is not None:
            conditions.append(Patient.age >= min_age)
        
        if max_age is not None:
            conditions.append(Patient.age <= max_age)
        
        # 查询总数
        count_stmt = select(func.count()).select_from(
            select(Patient.id).where(and_(*conditions)).subquery()
        )
        total = (await self.db.execute(count_stmt)).scalar() or 0
        
        # 分页查询
        query_stmt = (
            select(Patient)
            .where(and_(*conditions))
            .order_by(Patient.updated_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        
        result = await self.db.execute(query_stmt)
        patients = list(result.scalars().all())
        
        return patients, total
    
    async def search_by_symptom(self, symptom: str, limit: int = 20) -> List[Patient]:
        """按症状模糊搜索"""
        stmt = (
            select(Patient)
            .where(
                Patient.is_active == True,
                or_(
                    Patient.symptoms.cast(Text).ilike(f"%{symptom}%"),
                    Patient.chief_complaint.ilike(f"%{symptom}%"),
                )
            )
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    # ════════════════════════════════════
    # Update
    # ════════════════════════════════════
    
    async def update(self, patient_id: uuid.UUID, data: PatientUpdate) -> Patient:
        """更新患者"""
        patient = await self.get_by_id(patient_id)
        if not patient:
            raise ValueError("患者不存在")
        
        update_data = data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(patient, key, value)
        
        patient.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(patient)
        
        return patient
    
    async def partial_update(self, patient_id: uuid.UUID, **kwargs) -> Patient:
        """部分更新（只传要改的字段）"""
        patient = await self.get_by_id(patient_id)
        if not patient:
            raise ValueError("患者不存在")
        
        for key, value in kwargs.items():
            if hasattr(patient, key):
                setattr(patient, key, value)
        
        patient.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(patient)
        
        return patient
    
    # ════════════════════════════════════
    # Delete
    # ════════════════════════════════════
    
    async def delete(self, patient_id: uuid.UUID) -> bool:
        """硬删除"""
        patient = await self.get_by_id(patient_id)
        if not patient:
            return False
        
        await self.db.delete(patient)
        await self.db.commit()
        return True
    
    async def soft_delete(self, patient_id: uuid.UUID) -> bool:
        """软删除（标记为不活跃）"""
        patient = await self.get_by_id(patient_id)
        if not patient:
            return False
        
        patient.is_active = False
        patient.updated_at = datetime.utcnow()
        await self.db.commit()
        return True
    
    # ════════════════════════════════════
    # Statistics
    # ════════════════════════════════════
    
    async def get_statistics(self) -> dict:
        """统计数据"""
        
        # 总数
        total = (await self.db.execute(
            select(func.count()).where(Patient.is_active == True)
        )).scalar() or 0
        
        # 本月新增
        this_month = (await self.db.execute(
            select(func.count()).where(
                Patient.is_active == True,
                Patient.created_at >= datetime.now().replace(day=1),
            )
        )).scalar() or 0
        
        # 性别分布
        gender_stats = await self.db.execute(
            select(
                Patient.gender,
                func.count(Patient.id).label('count'),
            )
            .where(Patient.is_active == True)
            .group_by(Patient.gender)
        )
        gender_dist = {row[0]: row[1] for row in gender_stats.all()}
        
        # 年龄段分布
        age_ranges = [
            ("0-18", Patient.age.between(0, 18)),
            ("19-35", Patient.age.between(19, 35)),
            ("36-55", Patient.age.between(36, 55)),
            ("56+", Patient.age >= 56),
        ]
        age_dist = {}
        for label, condition in age_ranges:
            count = (await self.db.execute(
                select(func.count()).where(Patient.is_active == True, condition)
            )).scalar() or 0
            age_dist[label] = count
        
        return {
            "total_patients": total,
            "new_this_month": this_month,
            "gender_distribution": gender_dist,
            "age_distribution": age_dist,
        }
```

### 6.2 Pydantic Schema（配合 Service 使用）

创建 `app/models/schemas.py`：

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class GenderEnum(str, Enum):
    MALE = "男"
    FEMALE = "女"


class PatientCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    gender: GenderEnum
    age: int = Field(..., ge=0, le=150)
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    chief_complaint: str = Field(..., max_length=2000)
    symptoms: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=5000)


class PatientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    gender: Optional[GenderEnum] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    chief_complaint: Optional[str] = Field(None, max_length=2000)
    symptoms: Optional[List[str]] = None
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    notes: Optional[str] = None


class PatientResponse(BaseModel):
    id: str
    name: str
    display_name: str
    gender: str
    age: int
    phone: str  # 生产环境应脱敏
    chief_complaint: str
    symptoms: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    data: List
    total: int
    page: int
    size: int
    has_more: bool
```

---

## 第七章：复杂查询实战

### 7.1 动态条件构建

```python
from sqlalchemy import and_, or_, not_

async def advanced_search(
    session: AsyncSession,
    params: dict,
):
    """
    动态构建查询条件
    
    前端传来的参数可能是任意的组合，
    我们需要根据实际传入的参数动态构建 WHERE 条件
    """
    base_query = select(Patient).where(Patient.is_active == True)
    
    filters = []
    
    # 关键词搜索（匹配名字或主诉）
    if keyword := params.get("keyword"):
        filters.append(or_(
            Patient.name.ilike(f"%{keyword}%"),
            Patient.chief_complaint.ilike(f"%{keyword}%"),
        ))
    
    # 性别筛选
    if gender := params.get("gender"):
        filters.append(Patient.gender == gender)
    
    # 年龄范围
    if min_age := params.get("min_age"):
        filters.append(Patient.age >= min_age)
    
    if max_age := params.get("max_age"):
        filters.append(Patient.age <= max_age)
    
    # 标签筛选（JSON 数组包含某个值）
    if tag := params.get("tag"):
        filters.append(Patient.tags.contains([tag]))
    
    # 日期范围
    if created_after := params.get("created_after"):
        filters.append(Patient.created_at >= created_after)
    
    if created_before := params.get("created_before"):
        filters.append(Patient.created_at <= created_before)
    
    # 组合所有条件
    if filters:
        base_query = base_query.where(and_(*filters))
    
    # 排序（动态排序字段）
    sort_field = params.get("sort_by", "updated_at")
    sort_order = params.get("sort_order", "desc")
    
    sort_column = getattr(Patient, sort_field, None)
    if sort_column:
        if sort_order == "desc":
            base_query = base_query.order_by(sort_column.desc())
        else:
            base_query = base_query.order_by(sort_column.asc())
    
    # 分页
    page = params.get("page", 1)
    size = params.get("size", 20)
    base_query = base_query.offset((page - 1) * size).limit(size)
    
    result = await session.execute(base_query)
    return list(result.scalars().all())
```

### 7.2 聚合查询

```python
async def dashboard_statistics(session: AsyncSession):
    """仪表盘统计数据"""
    
    # 1. 患者增长趋势（按月）
    monthly_growth = await session.execute(
        select(
            func.to_char(Patient.created_at, 'YYYY-MM').label('month'),
            func.count(Patient.id).label('count'),
        )
        .where(Patient.is_active == True)
        .group_by(func.to_char(Patient.created_at, 'YYYY-MM'))
        .order_by(text('month'))
        .limit(12)
    )
    
    # 2. 各医生接诊量排名
    doctor_ranking = await session.execute(
        select(
            Consultation.doctor_id,
            func.count(Consultation.id).label('total'),
            func.avg(
                func.extract('epoch', Consultation.end_time - Consultation.start_time)
            ).label('avg_duration_min'),
        )
        .group_by(Consultation.doctor_id)
        .order_by(text('total DESC'))
        .limit(10)
    )
    
    # 3. 常见症状 TOP 10
    common_symptoms = await session.execute(
        select(
            func.unnest(Patient.symptoms).label('symptom'),
            func.count().label('frequency'),
        )
        .where(Patient.is_active == True, Patient.symptoms.isnot(None))
        .group_by(text('symptom'))
        .order_by(text('frequency DESC'))
        .limit(10)
    )
    
    return {
        "monthly_growth": [dict(row._mapping) for row in monthly_growth],
        "doctor_ranking": [dict(row._mapping) for row in doctor_ranking],
        "common_symptoms": [{"symptom": r[0], "count": r[1]} for r in common_symptoms],
    }
```

### 7.3 JSON 字段查询（PostgreSQL 特有）

```python
# PostgreSQL 的 JSONB 类型强大到可以当 NoSQL 用

async def query_json_fields(session: AsyncSession):
    """查询 JSON 字段中的特定内容"""
    
    # 假设 Patient 有个 metadata 字段存的是 JSON：
    # {"source": "线上咨询", "urgency": "high", "tags": ["慢性", "复诊"]}
    
    # 1. 查找 metadata.urgency = "high" 的患者
    stmt = select(Patient).where(
        Patient.metadata_["urgency"].astext() == "high"
    )
    
    # 2. 查找 tags 数组包含 "慢性" 的
    stmt = select(Patient).where(
        Patient.metadata_["tags"].contains(["慢性"])
    )
    
    # 3. 查找 metadata 中存在某个 key 的
    stmt = select(Patient).where(
        Patient.metadata_.has_key("source")
    )
    
    # 4. 更新 JSON 字段中的某个值
    from sqlalchemy import update
    await session.execute(
        update(Patient)
        .where(Patient.id == some_uuid)
        .values(metadata_=Patient.metadata_.merge({"last_contact": "2024-01-15"}))
    )
    
    # 5. 只返回 JSON 中的某些字段
    stmt = select(
        Patient.name,
        Patient.metadata_["source"].label("来源"),
        Patient.metadata_["urgency"].label("紧急程度"),
    )
```

---

## 第八章：事务与并发控制

### 8.1 为什么需要事务？

```
场景：转账操作

步骤1：从账户A扣款 100 元
步骤2：向账户B加款 100 元

问题：如果步骤1成功后，步骤2失败了怎么办？
→ A的钱扣了，B没收到 → 数据不一致！

解决方案：事务（Transaction）
→ 把多个操作包在一起，要么全部成功，要么全部失败回滚
```

### 8.2 事务使用方式

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def transfer_money(
    session: AsyncSession,
    from_account_id: int,
    to_account_id: int,
    amount: float,
):
    """
    转账 — 必须在事务中执行
    """
    async with session.begin():  # 自动开始事务，结束时自动 commit 或 rollback
        
        # 1. 查询并锁定两个账户（防止并发修改）
        from_acc = await session.get(Account, from_account_id, with_for_update=True)
        to_acc = await session.get(Account, to_account_id, with_for_update=True)
        
        if not from_acc or not to_acc:
            raise ValueError("账户不存在")
        
        if from_acc.balance < amount:
            raise ValueError("余额不足")
        
        # 2. 扣款
        from_acc.balance -= amount
        
        # 3. 收款
        to_acc.balance += amount
        
        # 如果这里抛出异常，自动 rollback
        # 否则正常结束，自动 commit
        
        # 记录转账日志
        log = TransferLog(
            from_account=from_account_id,
            to_account=to_account_id,
            amount=amount,
        )
        session.add(log)
        
        # 不需要手动 commit！session.begin() 会自动处理


# ════════════════════════════════════
# 手动控制事务（更精细的控制）
# ════════════════════════════════════

async def manual_transaction(session: AsyncSession):
    """手动事务控制"""
    
    try:
        # 开始事务
        await session.begin()
        
        # ... 执行多个操作 ...
        patient = Patient(name="测试", gender="男", age=30, phone="13900000000", chief_complaint="测试")
        session.add(patient)
        
        message = Message(conversation_id=some_id, role="user", content="测试消息")
        session.add(message)
        
        # 手动提交
        await session.commit()
        
    except Exception as e:
        # 出错时回滚
        await session.rollback()
        raise e
    finally:
        # 关闭 session
        await session.close()
```

### 8.3 并发控制

```python
# ════════════════════════════════════
# 悲观锁（Pessimistic Locking）
# ════════════════════════════════════

async def pessimistic_lock_demo(session: AsyncSession, patient_id: uuid.UUID):
    """
    悲观锁：直接锁住记录，其他人不能修改
    
    适用：竞争激烈的场景（如抢购、库存扣减）
    """
    
    # FOR UPDATE 锁定这行记录，直到事务结束
    patient = await session.execute(
        select(Patient)
        .where(Patient.id == patient_id)
        .with_for_update()  # ← 关键
    )
    patient = patient.scalar_one()
    
    # 此时其他事务无法修改这条记录
    # 它们会等待当前事务完成
    
    patient.age += 1
    await session.commit()


# ════════════════════════════════════
# 乐观锁（Optimistic Locking）
# ════════════════════════════════════

async def optimistic_lock_demo(session: AsyncSession, patient_id: uuid.UUID):
    """
    乐观锁：假设不会冲突，提交时检查版本号
    
    适用：读多写少的场景（如编辑资料）
    """
    
    patient = await session.get(Patient, patient_id)
    original_version = patient.version  # 假设有 version 字段
    
    # ... 业务逻辑 ...
    patient.name = "新名字"
    
    # 提交时检查版本是否变化
    await session.execute(
        update(Patient)
        .where(
            Patient.id == patient_id,
            Patient.version == original_version,  # 版本没变才能更新
        )
        .values(name="新名字", version=original_version + 1)
    )
    
    # 如果 affected rows = 0，说明被别人改过了
```

---

## 第九章：pgvector 向量操作

### 9.1 向量模型定义

```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Text, UUID, Integer
import uuid
from app.database import Base


class DocumentChunk(Base):
    """文档分块（带向量）"""
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(UUID(as_uuid=True), index=True)
    
    content = Column(Text, nullable=False)
    
    # 向量列 — 维度取决于 Embedding 模型
    # OpenAI ada-002: 1536维
    # OpenAI text-embedding-3-small: 1536维
    # 本地模型可能不同
    embedding = Column(Vector(1536))
    
    metadata_ = Column(JSON, default=dict)
    chunk_index = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        # IVFFlat 索引：适合中等规模数据
        Index(
            'idx_doc_chunk_embeddings',
            embedding,
            postgresql_using='ivfflat',
            postgresql_with={'lists': 100},
            postgresql_operator='vector_cosine_ops',
        ),
    )
```

### 9.2 向量存储和检索

```python
import numpy as np
from pgvector.sqlalchemy import Vector

async def store_embedding(session: AsyncSession, content: str, embedding_array: np.ndarray):
    """存储向量"""
    chunk = DocumentChunk(
        content=content,
        embedding=embedding_array.tolist(),  # numpy → list
    )
    session.add(chunk)
    await session.commit()


async def similarity_search(
    session: AsyncSession,
    query_vector: np.ndarray,
    top_k: int = 5,
    threshold: float = 0.7,
):
    """
    相似度搜索
    
    Args:
        query_vector: 查询向量
        top_k: 返回数量
        threshold: 相似度阈值（0~1）
    """
    query_vec_list = query_vector.tolist()
    
    # 余弦距离排序（越小越相似）
    stmt = (
        select(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vec_list))
        .limit(top_k)
    )
    
    result = await session.execute(stmt)
    chunks = result.scalars().all()
    
    # 过滤低相似度结果并转换格式
    results = []
    for chunk in chunks:
        distance = chunk.embedding.cosine_distance(query_vec_list)
        similarity = 1 - float(distance)  # cosine_distance → similarity
        
        if similarity >= threshold:
            results.append({
                "content": chunk.content,
                "similarity": round(similarity, 4),
                "metadata": chunk.metadata_,
            })
    
    return results
```

### 9.3 批量导入性能优化

```python
async def bulk_import_embeddings(
    session: AsyncSession,
    chunks_data: list[dict],  # [{content: "...", embedding: np.array, ...}]
    batch_size: int = 500,
):
    """
    批量导入向量数据（性能优化版）
    
    优化点：
    1. 分批提交（避免单次事务太大）
    2. copy_from 方式（比逐条 INSERT 快 10-100 倍）
    3. 临时禁用索引（导入完再重建）
    """
    total = len(chunks_data)
    imported = 0
    
    for i in range(0, total, batch_size):
        batch = chunks_data[i : i + batch_size]
        
        records = [
            DocumentChunk(
                content=item["content"],
                embedding=item["embedding"].tolist(),
                metadata_=item.get("metadata"),
                chunk_index=item.get("index", imported),
            )
            for item in batch
        ]
        
        session.add_all(records)
        await session.flush()  # 发送到数据库但不提交
        imported += len(batch)
        
        if imported % 1000 == 0:
            print(f"已导入 {imported}/{total}")
    
    await session.commit()
    print(f"✅ 批量导入完成：共 {imported} 条")
```

---

## 第十章：性能优化

### 10.1 索引策略

```sql
-- ════════════════════════════════════
-- 常用索引类型
-- ════════════════════════════════════

-- B-Tree 索引（默认，适合等值查询和范围查询）
CREATE INDEX idx_patients_name ON patients(name);
CREATE INDEX idx_patients_created ON patients(created_at);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);

-- 唯一索引（防止重复）
CREATE UNIQUE INDEX idx_patients_phone ON patients(phone);

-- 复合索引（多列联合查询时）
CREATE INDEX idx_patients_user_status ON patients(user_id, is_active, created_at DESC);

-- 部分索引（只索引部分数据，更小更快）
CREATE INDEX idx_active_patients_age ON patients(age) WHERE is_active = true;

-- 表达式索引（对计算结果建索引）
CREATE INDEX idx_patients_lower_name ON patients(lower(name));

-- GIN 索引（适合全文搜索和数组/JSON）
CREATE INDEX idx_patients_symptoms_gin ON patients USING gin(symptoms);
CREATE INDEX idx_patients_metadata_gin ON patients USING gin(metadata_);

-- pgvector 索引（向量相似度搜索）
CREATE INDEX idx_chunks_embeddings ON document_chunks
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 10.2 EXPLAIN 分析慢查询

```python
async def analyze_slow_query(session: AsyncSession):
    """分析查询执行计划"""
    
    slow_query = select(Patient).join(Conversation).join(Message).where(
        Patient.name.like("%张%"),
        Message.role == "user",
    )
    
    # 获取执行计划
    explained = await session.execute(
        f"EXPLAIN ANALYZE {str(slow_query.compile(dialect=asyncpg.dialect()))}"
    )
    
    for row in explained.all():
        print(row[0])
    
    # 输出示例：
    # Index Scan using idx_patients_name on patients (cost=... rows=...)
    # Hash Join (cost=... rows=...)
    # Sort (cost=...)
    # Planning Time: 0.5ms
    # Execution Time: 23.4ms  ← 这是你关注的数字
```

### 10.3 N+1 问题检测和解决

```python
# ════════════════════════════════════
# ❌ N+1 问题（性能杀手）
# ════════════════════════════════════

async def n_plus_one_problem(session: AsyncSession):
    """错误示范：产生 N+1 次查询"""
    
    # 第1次查询：获取所有用户（1次）
    users_result = await session.execute(select(User))
    users = users_result.scalars().all()
    
    for user in users:
        # 每次访问 .conversations 都触发一次额外查询（N次）
        # 总共 1 + N 次查询！
        print(f"{user.username}: {len(user.conversations)} 个对话")


# ════════════════════════════════════
# ✅ 解决方案1：eager loading（预加载）
# ════════════════════════════════════

async def solution_eager_loading(session: AsyncSession):
    """正确做法：一次查询搞定"""
    
    stmt = (
        select(User)
        .options(selectinload(User.conversations))  # 预加载！
    )
    result = await session.execute(stmt)
    users = result.scalars().all()
    
    for user in users:
        # conversations 已经在内存里了，不再查询数据库
        print(f"{user.username}: {len(user.conversations)} 个对话")


# ════════════════════════════════════
# ✅ 解决方案2：JOIN 查询
# ════════════════════════════════════

async def solution_join(session: AsyncSession):
    """用 JOIN 一次查出所有数据"""
    
    stmt = (
        select(User, Conversation)
        .outerjoin(Conversation)
        .order_by(User.id)
    )
    
    result = await session.execute(stmt)
    
    current_user = None
    conversations = []
    
    for row in result.all():
        user, conv = row
        if user != current_user:
            if current_user:
                print(f"{current_user.username}: {len(conversations)} 个对话")
            current_user = user
            conversations = []
        if conv:
            conversations.append(conv)
```

---

## 第十一章：综合项目 — 完整的诊所数据层

### 11.1 项目目录结构

```
app/
├── database.py           # 数据库连接和 Session 管理
├── config.py             # 配置
│
├── models/
│   ├── __init__.py
│   ├── user.py           # User 模型
│   ├── patient.py        # Patient 模型
│   ├── conversation.py   # Conversation 模型
│   ├── message.py         # Message 模型
│   ├── knowledge_base.py  # KnowledgeBase + Chunk
│   └── schemas.py         # Pydantic schemas
│
├── services/
│   ├── __init__.py
│   ├── patient_service.py # 患者 CRUD
│   ├── chat_service.py    # 对话服务
│   └── rag_service.py     # RAG 服务
│
└── routers/
    ├── patients.py        # 患者接口
    ├── chat.py            # AI 对话接口
    └── knowledge.py        # 知识库接口
```

### 11.2 完整的 Router 示例

创建 `app/routers/patients_complete.py`：

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.deps import get_current_user, get_db_session
from app.services.patient_service import PatientService
from app.models.schemas import (
    PatientCreate, PatientUpdate, PatientResponse, PaginatedResponse,
)

router = APIRouter(prefix="/api/v1/patients", tags=["患者管理"])


@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    """新建患者"""
    service = PatientService(db)
    try:
        patient = await service.create(data)
        return patient
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,  # UUID string
    db: AsyncSession = Depends(get_db_session),
):
    """获取患者详情"""
    import uuid
    service = PatientService(db)
    patient = await service.get_by_id(uuid.UUID(patient_id))
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    return patient


@router.get("", response_model=PaginatedResponse)
async def list_patients(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    min_age: Optional[int] = Query(None),
    max_age: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_session),
):
    """患者列表（支持多条件筛选 + 分页）"""
    service = PatientService(db)
    patients, total = await service.list_paginated(
        page=page,
        size=size,
        keyword=keyword,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
    )
    
    return PaginatedResponse(
        data=patients,
        total=total,
        page=page,
        size=size,
        has_more=(page * size) < total,
    )


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """更新患者"""
    import uuid
    service = PatientService(db)
    try:
        patient = await service.update(uuid.UUID(patient_id), data)
        return patient
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """删除患者（软删除）"""
    import uuid
    service = PatientService(db)
    success = await service.soft_delete(uuid.UUID(patient_id))
    if not success:
        raise HTTPException(status_code=404, detail="患者不存在")
    return {"code": 200, "message": "删除成功"}


@router.get("/statistics/dashboard")
async def patient_statistics(db: AsyncSession = Depends(get_db_session)):
    """患者统计数据（仪表盘用）"""
    service = PatientService(db)
    stats = await service.get_statistics()
    return {"code": 200, "data": stats}
```

---

## 验收标准

### ✅ 学完你应该能：

**基础能力**
- [ ] 能独立设计数据库表结构（考虑字段类型、索引、约束）
- [ ] 能写出完整的 SQLAlchemy ORM 模型（含关联关系）
- [ ] 能实现 CRUD + 分页 + 多条件筛选
- [ ] 能使用事务保证数据一致性
- [ ] 能做 EXPLAIN 分析并优化慢查询

**进阶能力**
- [ ] 能处理一对多/多对多关系
- [ ] 能解决 N+1 查询问题
- [ ] 能使用 pgvector 进行向量存储和相似度搜索
- [ ] 能使用 PostgreSQL 的 JSONB 类型
- [ ] 能做聚合统计和数据看板查询

### ❓ 自测题

1. **`selectinload` 和 `joinedload` 有什么区别？什么时候用哪个？**

2. **什么是事务的 ACID 特性？在什么场景下必须用事务？**

3. **N+1 问题是怎么产生的？怎么检测和解决？**

4. **IVFFlat 和 HNSW 索引有什么区别？分别适用于什么场景？**

5. **什么时候应该用 `async with session.begin()` 而不是手动 `begin()/commit()/rollback()`？**

---

> **下一步**：你已经掌握了后端的核心数据能力。继续学习 [04-RAG服务实战.md](./04-RAG服务实战.md)，把数据和 AI 结合起来，打造你的核心竞争力产品！
