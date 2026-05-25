# RAG 服务完整实战 — 从零搭建 AI 知识库检索系统

> **目标读者**：已经掌握 FastAPI 基础，想实现 AI 对话中的「知识库问答」功能
> 
> **核心目标**：学完后能独立实现一个完整的 RAG 系统，让 AI 能基于你的知识库回答问题
> 
> **预计时间**：4-5 小时（含环境配置和 API 调试）

---

## 目录

- [第一章：RAG 是什么？为什么你需要它](#第一章rag-是什么为什么你需要它)
- [第二章：环境准备（30分钟）](#第二章环境准备30分钟)
- [第三章：Embedding — 把文字变成数字](#第三章embedding--把文字变成数字)
- [第四章：文本分块 — 智能切割长文本](#第四章文本分块--智能切割长文本)
- [第五章：向量存储 — pgvector 入门](#第五章向量存储--pgvector-入门)
- [第六章：相似度搜索 — 核心检索逻辑](#第六章相似度搜索--核心检索逻辑)
- [第七章：Prompt 工程 — 组装给 LLM 的提示词](#第七章prompt-工程--组装给-llm-的提示词)
- [第八章：Function Calling — 让 AI 调用你的工具](#第八章function-calling--让-ai-调用你的工具)
- [第九章：端到端整合 — 完整的 AI 对话流程](#第九章端到端整合--完整的-ai-对话流程)
- [第十章：实战项目 — 中医知识库问答系统](#第十章实战项目--中医知识库问答系统)
- [验收标准与常见问题](#验收标准与常见问题)

---

## 第一章：RAG 是什么？为什么你需要它？

### 1.1 一个场景让你理解 RAG

```
普通 LLM 的局限：

你问 ChatGPT："张医生诊所里那个叫李四的患者上次开的什么方子？"

ChatGPT 回答：
"抱歉，我无法访问您的诊所数据或患者信息..."

原因：ChatGPT 不知道你诊所里的任何数据！


RAG 解决的问题：

你问你的 AI 助手："李四患者上次开的什么方子？"

AI 助手（带 RAG）：
Step 1: 把"李四 患者方子"变成向量 → [0.12, -0.34, ...]
Step 2: 在向量数据库中搜索相似的医案记录
Step 3: 找到匹配结果：
   "患者李四，男，35岁，主诉失眠三个月。
    诊断：心脾两虚。处方：归脾汤加减。
    开药日期：2024-01-15"
Step 4: 把找到的内容 + 你的问题一起发给 LLM
Step 5: LLM 基于这些信息回答：
   "根据记录，李四患者在2024年1月15日就诊时，
    张医生诊断为'心脾两虚'，开具了'归脾汤加减'方剂。"
```

### 1.2 RAG 全流程图解

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG 完整流程                               │
│                                                             │
│  ┌──────────┐                                               │
│  │ 用户提问  │ "我最近失眠怎么办？"                           │
│  └────┬─────┘                                               │
│       ▼                                                      │
│  ┌──────────┐     ┌──────────────┐                          │
│  │ Query    │────→│ Embedding     │ 向量化                   │
│  │ 处理     │     │ Model         │ [0.23, -0.12, ...]      │
│  └──────────┘     └──────┬───────┘                          │
│                          ▼                                   │
│                 ┌──────────────────┐                         │
│                 │ Vector Database  │ pgvector                │
│                 │ (知识库)          │ 相似度搜索              │
│                 └────────┬─────────┘                         │
│                          ▼                                   │
│              ┌──────────────────────┐                        │
│              │ Top-K 相关文档        │                        │
│              │ [医案1, 医案2, ...]   │                        │
│              └──────────┬───────────┘                        │
│                         ▼                                    │
│              ┌──────────────────────┐                        │
│              │ Prompt Assembly       │ 组装提示词             │
│              │ System + Context + Q  │                        │
│              └──────────┬───────────┘                        │
│                         ▼                                    │
│              ┌──────────────────────┐                        │
│              │ LLM (GPT-4o/DeepSeek)│ 生成回答               │
│              └──────────┬───────────┘                        │
│                         ▼                                    │
│              ┌──────────────────────┐                        │
│              │ Safety Check         │ 安全检查               │
│              │ + Disclaimer         │ 免责声明               │
│              └──────────┬───────────┘                        │
│                         ▼                                    │
│              ┌──────────────────────┐                        │
│              │ SSE Stream           │ 流式返回给前端         │
│              └──────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 前端类比理解 RAG

```
RAG 类比于前端的搜索引擎 + AI 总结：

1. Embedding = 给每篇文章生成"指纹"
   （类似 Elasticsearch 的分词索引）

2. Vector Search = 根据查询找相关文章
   （类似 Google 搜索返回相关结果）

3. Prompt Assembly = 把搜索结果整理成上下文
   （类似把搜索结果喂给 AI 让它总结）

4. LLM Generation = 基于上下文生成回答
   （类似 ChatGPT 的回答能力）

区别：
传统搜索：关键词匹配 → 返回原文
RAG：语义理解 → 返回 AI 生成的总结性回答
```

---

## 第二章：环境准备（30分钟）

### 2.1 你需要的东西

```
✅ 已有：
- Python 3.10+
- FastAPI 项目骨架
- 基本的 Python 编程能力

❌ 需要安装：
- PostgreSQL 数据库（带 pgvector 扩展）
- OpenAI API Key 或 DeepSeek API Key（用于 Embedding 和 LLM）
- 几个 Python 库

💰 成本估算：
- OpenAI Embedding API: $0.00002 / 1K tokens（非常便宜）
- OpenAI GPT-4o-mini: $0.15 / 1M tokens（也便宜）
- 或者用 DeepSeek: 更便宜，国内访问快
- 预计学习期间花费 < ¥50
```

### 2.2 安装 PostgreSQL + pgvector

```bash
# Mac 用户（Homebrew）
brew install postgresql@16
brew install pgvector  # 如果没有自带

# 启动 PostgreSQL
brew services start postgresql@16

# 创建数据库
createdb agent_db

# 进入数据库命令行
psql agent_db

# 在 psql 中执行：
CREATE EXTENSION vector;
-- 如果成功说明 pgvector 安装正确
```

```bash
# Docker 用户（推荐，更简单）
docker run -d \
  --name pgvector \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=agent_db \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 等几秒让数据库启动
docker exec -it pgvector psql -U postgres -d agent_db -c "CREATE EXTENSION vector;"
```

### 2.3 安装 Python 依赖

```bash
# 创建虚拟环境（如果还没有）
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install fastapi uvicorn sqlalchemy[asyncio]
pip install asyncpg psycopg2-binary  # PostgreSQL 异步驱动
pip install pgvector  # pgvector Python 绑定
pip install openai  # OpenAI API SDK
pip install python-dotenv  # 环境变量管理
pip install numpy  # 数值计算
pip install httpx  # HTTP 客户端（测试用）

# 验证安装
python -c "
import openai, pgvector, sqlalchemy, numpy
print('所有依赖安装成功！')
"
```

### 2.4 配置 API Key

创建 `.env` 文件（不要提交到 Git！）：

```bash
# .env 文件内容

# OpenAI 配置
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# 或者使用 DeepSeek（更便宜，国内快）
# DEEPSEEK_API_KEY=sk-your-deepseek-key-here
# DEEPSEEK_BASE_URL=https://api.deepseek.com

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_db

# Redis（可选，后面用）
REDIS_URL=redis://localhost:6379/0
```

创建 `app/config.py`：

```python
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置 — 从环境变量读取"""
    
    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    
    # Embedding 模型选择
    embedding_model: str = "text-embedding-ada-002"  # 1536维，$0.00002/1K tokens
    
    # LLM 模型选择
    llm_model: str = "gpt-4o-mini"  # 便宜好用
    
    # 数据库
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # RAG 参数
    rag_chunk_size: int = 400       # 分块大小（字符数）
    rag_chunk_overlap: int = 50     # 分块重叠
    rag_top_k: int = 5              # 检索返回数量
    rag_similarity_threshold: float = 0.7  # 相似度阈值
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

if not settings.openai_api_key:
    print("⚠️ 警告：未设置 OPENAI_API_KEY，请创建 .env 文件")
```

---

## 第三章：Embedding — 把文字变成数字

### 3.1 什么是 Embedding？

```
Embedding = 文字 → 向量（一组数字）

示例：
"失眠怎么办" → [0.0234, -0.1567, 0.8923, ..., 0.0445]  (1536个数字)
"睡眠障碍" → [0.0256, -0.1498, 0.8856, ..., 0.0489]  (1536个数字)
"今天天气不错" → [-0.5678, 0.2345, -0.1234, ..., -0.9876]

特点：
- 语义相近的文字 → 向量也很接近（距离小）
- 语义不同的文字 → 向量距离远

用途：
- 计算两个句子的相似度
- 在大量文档中找最相关的片段
- 为机器学习模型提供数值输入
```

### 3.2 实现 Embedding 服务

创建 `app/services/embedding.py`：

```python
import numpy as np
from openai import AsyncOpenAI
from app.config import settings
from typing import List


class EmbeddingService:
    """
    文本向量化服务
    
    负责：把文本转换成向量（数组）
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.model = settings.embedding_model
        
        self._cache: dict[str, np.ndarray] = {}
    
    async def embed_text(self, text: str) -> np.ndarray:
        """
        将单条文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            numpy 数组，形状为 (embedding_dim,)
        """
        if text in self._cache:
            return self._cache[text]
        
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        
        embedding = np.array(response.data[0].embedding, dtype=np.float32)
        self._cache[text] = embedding
        
        return embedding
    
    async def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        批量将文本转换为向量（更高效）
        
        OpenAI 支持一次请求最多 2048 条文本
        """
        results = []
        
        batch_size = 200
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=batch,
            )
            
            for item in response.data:
                embedding = np.array(item.embedding, dtype=np.float32)
                results.append(embedding)
                
                if len(batch) == 1:
                    self._cache[batch[0]] = embedding
        
        return results
    
    async def compute_similarity(self, text1: str, text2: str) -> float:
        """
        计算两条文本的余弦相似度
        
        Returns:
            0~1 之间的值，越大越相似
        """
        vec1 = await self.embed_text(text1)
        vec2 = await self.embed_text(text2)
        
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()


async def test_embedding():
    """测试 Embedding 服务"""
    service = EmbeddingService()
    
    vec = await service.embed_text("你好世界")
    print(f"向量维度: {len(vec)}")
    print(f"前5个值: {vec[:5]}")
    
    sim1 = await service.compute_similarity("我睡不着", "失眠怎么办")
    sim2 = await service.compute_similarity("我睡不着", "今天天气真好")
    
    print(f"\n相似度测试:")
    print(f"'我睡不着' vs '失眠怎么办': {sim1:.4f}  ← 应该高")
    print(f"'我睡不着' vs '今天天气真好': {sim2:.4f}  ← 应该低")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_embedding())
```

运行测试：

```bash
python -m app.services.embedding

# 预期输出：
# 向量维度: 1536
# 前5个值: [ 0.0234 -0.1567  0.8923 -0.0456  0.1234]
#
# 相似度测试:
# '我睡不着' vs '失眠怎么办': 0.8765  ← 应该高（语义相近）
# '我睡不着' vs '今天天气真好': 0.2345  ← 应该低（语义不同）
```

---

## 第四章：文本分块 — 智能切割长文本

### 4.1 为什么需要分块？

```
问题：LLM 有上下文长度限制

GPT-4o-turbo: 128K tokens（很长，但不是无限）
GPT-4o-mini: 128K tokens
但 Embedding 模型通常限制：8191 tokens

如果你有一篇 10000 字的中医典籍文章：
- 不能直接整个丢进去（太长）
- 需要切成合适大小的段落


分块的挑战：

❌ 盲目按字数切：
   "...肝主疏泄，喜条达而恶抑郁。脾胃为后天之本..."
   切成 400 字一段可能正好在句子中间断开
   
✅ 智能分块：
   - 优先在段落边界切（\n\n）
   - 其次在句子边界切（。！？）
   - 保持一定重叠（避免丢失边界信息）
```

### 4.2 实现智能分块器

创建 `app/services/chunker.py`：

```python
import re
from dataclasses import dataclass
from typing import List
from app.config import settings


@dataclass
class Chunk:
    """文本块"""
    content: str
    index: int
    token_count: int
    metadata: dict = None


class TextChunker:
    """
    智能文本分块器
    
    策略：
    1. 先按双换行（段落）分割
    2. 过长的段落再按句子分割
    3. 每块保持指定大小，并有重叠区域
    """
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.rag_chunk_size
        self.chunk_overlap = chunk_overlap or settings.rag_chunk_overlap
    
    def split_text(self, text: str, metadata: dict = None) -> List[Chunk]:
        if not text or not text.strip():
            return []
        
        chunks = []
        current_content = ""
        chunk_index = 0
        
        paragraphs = re.split(r'\n{2,}', text.strip())
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_content) + len(para) + 1 <= self.chunk_size:
                current_content += ("\n\n" if current_content else "") + para
            else:
                if current_content:
                    chunks.append(self._make_chunk(current_content, chunk_index, metadata))
                    chunk_index += 1
                
                if len(para) > self.chunk_size:
                    sub_chunks = self._split_long_paragraph(para)
                    for sub in sub_chunks[:-1]:
                        chunks.append(self._make_chunk(sub, chunk_index, metadata))
                        chunk_index += 1
                    current_content = sub_chunks[-1] if sub_chunks else ""
                else:
                    current_content = para
        
        if current_content:
            chunks.append(self._make_chunk(current_content, chunk_index, metadata))
        
        chunks = self._add_overlap(chunks)
        
        return chunks
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        parts = []
        current = ""
        sentences = re.split(r'(?<=[。！？；\n])', paragraph)
        
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            
            if len(current) + len(sent) <= self.chunk_size:
                current += sent
            else:
                if current:
                    parts.append(current)
                if len(sent) > self.chunk_size:
                    for i in range(0, len(sent), self.chunk_size - self.chunk_overlap):
                        parts.append(sent[i:i + self.chunk_size])
                    current = ""
                else:
                    current = sent
        
        if current:
            parts.append(current)
        
        return parts if parts else [paragraph]
    
    def _make_chunk(self, content: str, index: int, metadata: dict = None) -> Chunk:
        return Chunk(
            content=content.strip(),
            index=index,
            token_count=self._estimate_tokens(content),
            metadata=metadata,
        )
    
    def _add_overlap(self, chunks: List[Chunk]) -> List[Chunk]:
        if len(chunks) <= 1 or self.chunk_overlap <= 0:
            return chunks
        
        result = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                result.append(chunk)
            else:
                prev_content = result[-1].content
                overlap_text = prev_content[-self.chunk_overlap:] if len(prev_content) > self.chunk_overlap else prev_content
                
                new_content = overlap_text + "\n..." + chunk.content
                result.append(Chunk(
                    content=new_content,
                    index=chunk.index,
                    token_count=self._estimate_tokens(new_content),
                    metadata=chunk.metadata,
                ))
        
        return result
    
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)


def test_chunker():
    long_text = """
中医诊断学基础

一、望诊

望诊是医生运用视觉观察患者的全身、局部及其分泌物、排泄物的变化来了解病情的方法。

1. 望神
神是人体生命活动的外在表现。得神表现为精神饱满、目光明亮、反应灵敏；失神则精神萎靡、目光晦暗。

2. 望色
主要观察面部颜色和光泽。青色主寒证、痛证；赤色主热证；黄色主湿证。

二、闻诊

闻诊包括听声音和嗅气味两个方面。
语声高亢有力多为实证；语声低弱无力多为虚证。
    """.strip()
    
    chunker = TextChunker(chunk_size=300, chunk_overlap=30)
    chunks = chunker.split_text(long_text, metadata={"source": "中医教材"})
    
    print(f"原始文本长度: {len(long_text)} 字符")
    print(f"分块数量: {len(chunks)}")
    
    for chunk in chunks:
        print(f"\n--- Chunk {chunk.index} ({chunk.token_count} tokens) ---")
        preview = chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
        print(preview)


if __name__ == "__main__":
    test_chunker()
```

---

## 第五章：向量存储 — pgvector 入门

### 5.1 创建数据库模型

创建 `app/models/vector.py`：

```python
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid

from app.database import Base


class KnowledgeBase(Base):
    """知识库（集合）"""
    __tablename__ = "knowledge_bases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(50), index=True)
    is_active = Column(default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeChunk(Base):
    """知识库分块（存储向量化的文本）"""
    __tablename__ = "knowledge_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536))  # 向量维度取决于模型
    
    source = Column(String(500))
    metadata_ = Column("metadata", JSON, default=dict)
    
    chunk_index = Column(Integer)
    token_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index(
            'idx_chunk_embeddings',
            embedding,
            postgresql_using='ivfflat',
            postgresql_with={'lists': 100},
            postgresql_operator='vector_cosine_ops',
        ),
    )
```

### 5.2 数据库初始化脚本

创建 `app/db_init.py`：

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import settings
from app.database import Base


async def init_db():
    engine = create_async_engine(settings.database_url, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    
    print("✅ 数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(init_db())
```

---

## 第六章：相似度搜索 — 核心检索逻辑

### 6.1 实现 RAG 服务核心

创建 `app/services/rag.py`：

```python
import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embedding import EmbeddingService
from app.services.chunker import TextChunker, Chunk
from app.models.vector import KnowledgeBase, KnowledgeChunk
from app.config import settings


class SearchResult:
    def __init__(self, content: str, similarity: float, metadata: dict = None, source: str = None):
        self.content = content
        self.similarity = similarity
        self.metadata = metadata or {}
        self.source = source
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "similarity": round(self.similarity, 4),
            "metadata": self.metadata,
            "source": self.source,
        }


class RAGService:
    """
    RAG（检索增强生成）核心服务
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.chunker = TextChunker()
    
    async def ingest_text(
        self,
        knowledge_base_id: uuid.UUID,
        text: str,
        source: str = None,
        metadata: dict = None,
    ) -> int:
        """导入文本到知识库：分块 → 向量化 → 存储"""
        chunks = self.chunker.split_text(text, metadata={**(metadata or {}), "source": source})
        
        if not chunks:
            return 0
        
        texts = [chunk.content for chunk in chunks]
        embeddings = await self.embedding_service.embed_batch(texts)
        
        records = []
        for chunk, embedding in zip(chunks, embeddings):
            record = KnowledgeChunk(
                knowledge_base_id=knowledge_base_id,
                content=chunk.content,
                embedding=embedding.tolist(),
                source=source,
                metadata_=chunk.metadata,
                chunk_index=chunk.index,
                token_count=chunk.token_count,
            )
            records.append(record)
        
        self.db.add_all(records)
        await self.db.commit()
        
        print(f"✅ 成功导入 {len(records)} 个文本块")
        return len(records)
    
    async def search(
        self,
        query: str,
        knowledge_base_id: Optional[uuid.UUID] = None,
        top_k: int = None,
        threshold: float = None,
    ) -> List[SearchResult]:
        """语义搜索"""
        top_k = top_k or settings.rag_top_k
        threshold = threshold or settings.rag_similarity_threshold
        
        query_embedding = await self.embedding_service.embed_text(query)
        
        base_query = select(KnowledgeChunk)
        if knowledge_base_id:
            base_query = base_query.where(KnowledgeChunk.knowledge_base_id == knowledge_base_id)
        
        search_query = base_query.order_by(
            KnowledgeChunk.embedding.cosine_distance(query_embedding.tolist())
        ).limit(top_k)
        
        result = await self.db.execute(search_query)
        rows = result.scalars().all()
        
        search_results = []
        for row in rows:
            similarity = 1 - row.embedding.cosine_distance(query_embedding.tolist())
            if similarity >= threshold:
                search_results.append(SearchResult(
                    content=row.content,
                    similarity=float(similarity),
                    metadata=row.metadata_,
                    source=row.source,
                ))
        
        return search_results
    
    def assemble_context(self, search_results: List[SearchResult], max_context_length: int = 4000) -> str:
        """组装上下文"""
        if not search_results:
            return "未找到相关的参考资料。"
        
        context_parts = []
        total_length = 0
        
        for i, r in enumerate(search_results, 1):
            part = f"[参考资料{i}]（相似度:{r.similarity:.2f}）：\n{r.content}\n"
            if total_length + len(part) > max_context_length:
                context_parts.append("\n[...更多参考资料省略...]")
                break
            context_parts.append(part)
            total_length += len(part)
        
        return "\n".join(context_parts)
```

---

## 第七章：Prompt 工程 — 组装提示词

创建 `app/services/prompt_manager.py`：

```python
from typing import Optional


class PromptTemplates:
    SYSTEM_PROMPTS = {
        "tcm_consultation": """你是一位拥有30年临床经验的资深中医医师助手。

【重要规则】
1. 所有回答必须基于提供的参考资料，不得编造信息
2. 如果参考资料中没有相关信息，明确告知用户
3. 回答要专业准确，同时通俗易懂
4. 对于具体的用药建议，务必提醒用户咨询执业医师
5. 引用资料时注明来源编号""",

        "tcm_followup": """你是诊所的患者随访助手。生成一条温馨自然的随访消息，不超过120字。""",
    }
    
    FEW_SHOT_EXAMPLES = {
        "tcm_consultation": [
            {
                "input": "我最近总是睡不着，躺下要一两个小时才能睡着",
                "output": """您好，感谢信任。从您描述的症状来看，属于典型的"不寐"范畴。

**关键症状分析：**
📍 入睡困难伴多梦 — 往往与心脾两虚有关

**调理建议：**
1. 作息调整：每晚11点前就寝
2. 食疗辅助：桂圆、红枣、小米粥
3. 穴位按摩：内关穴、涌泉穴

⚠️ 如症状持续超过两周，建议前往正规医疗机构面诊。

*参考资料：中医基础理论*""",
            },
        ],
    }
    
    SAFETY_DISCLAIMER = """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 重要声明
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

本系统内容为AI辅助生成的参考信息，
不构成任何医疗诊断或治疗建议。
最终诊断请以执业医师的意见为准。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


class PromptManager:
    def __init__(self):
        self.templates = PromptTemplates()
    
    def build_chat_messages(
        self,
        user_query: str,
        context: str,
        prompt_type: str = "tcm_consultation",
        include_few_shot: bool = True,
        include_disclaimer: bool = True,
    ) -> list[dict]:
        messages = []
        
        system_prompt = self.templates.SYSTEM_PROMPTS.get(prompt_type, "")
        full_system = f"{system_prompt}\n\n参考资料：\n{context}"
        
        if include_disclaimer:
            full_system += self.templates.SAFETY_DISCLAIMER
        
        messages.append({"role": "system", "content": full_system})
        
        if include_few_shot and prompt_type in self.templates.FEW_SHOT_EXAMPLES:
            for example in self.templates.FEW_SHOT_EXAMPLES[prompt_type][:1]:
                messages.append({"role": "user", "content": example["input"]})
                messages.append({"role": "assistant", "content": example["output"]})
        
        messages.append({"role": "user", "content": user_query})
        
        return messages
```

---

## 第八章：Function Calling — 让 AI 调用你的工具

创建 `app/services/function_calling.py`：

```python
import json
import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "get_patient_profile",
            "description": "获取患者详细信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "description": "患者ID"},
                },
                "required": ["patient_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "搜索中医知识库",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询"},
                },
                "required": ["query"],
            },
        },
    },
]


class FunctionHandler:
    def __init__(self, db: AsyncSession, rag_service=None):
        self.db = db
        self.rag_service = rag_service
    
    async def handle_tool_call(self, tool_name: str, tool_args: dict) -> dict:
        handler_map = {
            "get_patient_profile": self._get_patient_profile,
            "search_knowledge_base": self._search_knowledge_base,
        }
        
        handler = handler_map.get(tool_name)
        if not handler:
            return {"error": f"未知工具: {tool_name}"}
        
        try:
            return await handler(**tool_args)
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_patient_profile(self, patient_id: str) -> dict:
        from app.models.patient import Patient
        try:
            pid = uuid.UUID(patient_id)
            patient = await self.db.get(Patient, pid)
            if not patient:
                return {"error": "患者不存在"}
            return {"name": patient.name, "age": patient.age, "chief_complaint": patient.chief_complaint}
        except ValueError:
            return {"error": "无效的ID格式"}
    
    async def _search_knowledge_base(self, query: str) -> dict:
        if not self.rag_service:
            return {"error": "RAG服务未初始化"}
        results = await self.rag_service.search(query, top_k=5)
        return {"results": [r.to_dict() for r in results]}
```

---

## 第九章：端到端整合 — 完整的 AI 对话流程

### 9.1 创建 Chat Service

创建 `app/services/chat_service.py`：

```python
import json
import time
import asyncio
from typing import AsyncGenerator

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.rag import RAGService
from app.services.prompt_manager import PromptManager
from app.services.function_calling import FunctionHandler, TOOLS_DEFINITION


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        self.rag_service = RAGService(db)
        self.prompt_manager = PromptManager()
        self.func_handler = FunctionHandler(db, self.rag_service)
    
    async def chat_stream(
        self,
        message: str,
        conversation_id: str = None,
        use_rag: bool = True,
        use_tools: bool = True,
    ) -> AsyncGenerator[dict, None]:
        start_time = time.time()
        
        yield {"type": "status", "content": "正在分析问题..."}
        
        context = ""
        if use_rag:
            yield {"type": "status", "content": "正在搜索知识库..."}
            search_results = await self.rag_service.search(message, top_k=5)
            context = self.rag_service.assemble_context(search_results)
            yield {"type": "sources", "content": [r.to_dict() for r in search_results]}
        
        messages = self.prompt_manager.build_chat_messages(user_query=message, context=context)
        
        yield {"type": "status", "content": "正在生成回复..."}
        
        full_response = ""
        tool_calls_made = []
        
        stream = await self.client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            tools=TOOLS_DEFINITION if use_tools else None,
            stream=True,
            temperature=0.7,
        )
        
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            
            if delta and delta.content:
                full_response += delta.content
                yield {"type": "chunk", "content": delta.content}
            
            elif delta and delta.tool_calls:
                for tc in delta.tool_calls:
                    tool_calls_made.append(tc)
        
        if tool_calls_made and use_tools:
            yield {"type": "status", "content": "正在查询数据..."}
            
            for tc in tool_calls_made:
                func_result = await self.func_handler.handle_tool_call(tc.function.name, json.loads(tc.function.arguments))
                yield {"type": "tool_result", "content": func_result}
        
        latency = (time.time() - start_time) * 1000
        yield {"type": "done", "content": {"model": settings.llm_model, "latency_ms": round(latency, 2)}}
    
    async def chat_non_stream(self, message: str, **kwargs) -> dict:
        full_response = ""
        async for event in self.chat_stream(message, **kwargs):
            if event["type"] == "chunk":
                full_response += event["content"]
            elif event["type"] == "done":
                return event["content"]
        return {"full_response": full_response}
```

### 9.2 创建 API 接口

更新 `app/routers/chat.py`：

```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import json

from app.deps import get_current_user, get_db_session
from app.services.chat_service import ChatService
from app.database import AsyncSession

router = APIRouter(prefix="/api/v1/chat", tags=["AI 对话"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None
    use_rag: bool = True
    use_tools: bool = True
    stream: bool = True


@router.post("/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    chat_service = ChatService(db)
    
    async def event_generator():
        try:
            async for event in chat_service.chat_stream(
                message=request.message,
                conversation_id=request.conversation_id,
                use_rag=request.use_rag,
                use_tools=request.use_tools,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type':'error','content':{'message':str(e)}})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("")
async def chat_endpoint(request: ChatRequest, user=Depends(get_current_user), db: AsyncSession=Depends(get_db_session)):
    chat_service = ChatService(db)
    result = await chat_service.chat_non_stream(message=request.message)
    return {"code": 200, "data": result}
```

---

## 第十章：验收标准

### ✅ 学完你应该能：

- [ ] 解释 RAG 的完整流程
- [ ] 调用 OpenAI Embedding API 获取向量
- [ ] 实现智能文本分块
- [ ] 使用 pgvector 存储和检索向量
- [ ] 设计有效的 System Prompt
- [ ] 实现 Function Calling
- [ ] 实现 SSE 流式输出
- [ ] 整合所有组件成完整的 AI 对话系统

### ❓ 自测题

1. **RAG 和纯 LLM 对话有什么区别？什么时候该用 RAG？**
   
2. **chunk_size 设太大或太小会有什么问题？**
   
3. **similarity_threshold 设太高或太低会怎样？**

---

> **下一步**：继续学习 [03-SQLAlchemy+PostgreSQL实战.md](./03-SQLAlchemy+PostgreSQL实战.md)，掌握数据持久化能力。
