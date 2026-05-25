# Agent 管理平台 - 产品需求 PRD

**版本**：v1.0  
**创建日期**：2024-01-XX  
**文档类型**：应用层产品 PRD  
**关联文档**：《个人版 AI 基座 PRD.md》、《ASR_TTS 功能扩展 PRD.md》

---

# 一、文档概述

## 1.1 文档目的

本文档描述基于 AI 基座构建的 Agent 管理平台，该平台作为应用层，专注于业务编排和场景落地，调用基座层能力快速创建各类 AI Agent 应用。

## 1.2 产品定位

**Agent 管理平台** = Agent 编排工厂 + 工作流引擎 + 场景应用市场

- **Agent 编排工厂**：可视化创建、配置、部署 Agent
- **工作流引擎**：编排复杂业务流程
- **场景应用市场**：提供丰富的场景化 Agent 应用

## 1.3 与基座层的关系

```
┌─────────────────────────────────┐
│   Agent 管理平台（应用层）       │  ← 本文档
│   - Agent 编排                  │
│   - 工作流引擎                  │
│   - 场景应用                    │
└──────────────┬──────────────────┘
               │ API 调用
               ▼
┌─────────────────────────────────┐
│   AI 中间基座（基座层）          │  ← 已实现
│   - LLM 路由                    │
│   - ASR/TTS                     │
│   - RAG 知识库                  │
│   - 记忆系统                    │
└─────────────────────────────────┘
```

---

# 二、核心功能设计

## 2.1 Agent 编排中心

### 2.1.1 Agent 创建

**功能描述**：可视化创建 AI Agent

**核心配置**：
- **基本信息**：名称、描述、头像、分类
- **角色设定**：系统提示词、人设、风格
- **能力绑定**：选择基座能力（LLM、ASR、TTS、RAG）
- **模型配置**：选择默认模型、温度、最大 Token
- **知识库绑定**：选择关联的知识库
- **记忆配置**：短期记忆/长期记忆开关

**界面原型**：
```
┌─────────────────────────────────┐
│  创建 Agent                      │
├─────────────────────────────────┤
│  基本信息                        │
│  ┌─────────────────────────┐   │
│  │ 名称：[编程助手        ] │   │
│  │ 描述：[专业的编程顾问  ] │   │
│  │ 分类：[技术支援 ▼      ] │   │
│  └─────────────────────────┘   │
│                                 │
│  角色设定                        │
│  ┌─────────────────────────┐   │
│  │ 系统提示词：            │   │
│  │ [你是一个专业的程序员  ] │   │
│  │ [擅长解答编程问题      ] │   │
│  └─────────────────────────┘   │
│                                 │
│  能力配置                        │
│  ☑ LLM 对话能力                 │
│  ☑ ASR 语音识别                 │
│  ☑ TTS 语音合成                 │
│  ☑ RAG 知识库检索               │
│  ☐ 长期记忆                     │
│                                 │
│  模型选择                        │
│  默认模型：[gpt-3.5-turbo ▼]   │
│  温度：[0.7 ───○───] 1.0       │
│                                 │
│  [取消]  [保存]                  │
└─────────────────────────────────┘
```

### 2.1.2 Agent 管理

**功能列表**：
- Agent 列表查看（分页、搜索、过滤）
- Agent 编辑（修改配置）
- Agent 启用/禁用
- Agent 删除（软删除）
- Agent 复制（快速创建相似 Agent）
- Agent 测试（在线调试）

### 2.1.3 Agent 发布

**发布流程**：
```
创建 Agent
  ↓
配置能力
  ↓
测试验证
  ↓
发布审核（可选）
  ↓
上线部署
  ↓
生成访问链接/API
```

**访问方式**：
- Web 聊天界面
- API 接口
- 嵌入第三方
- 移动端分享

## 2.2 工作流引擎

### 2.2.1 可视化编排

**功能描述**：拖拽式工作流设计器

**核心节点**：

#### 节点类型
1. **开始节点**：工作流入口
2. **输入节点**：接收用户输入（文字/语音）
3. **LLM 节点**：调用基座 LLM 能力
4. **RAG 节点**：知识库检索
5. **条件节点**：条件分支判断
6. **循环节点**：循环处理
7. **并行节点**：并行任务
8. **输出节点**：返回结果
9. **ASR 节点**：语音识别
10. **TTS 节点**：语音合成

**界面原型**：
```
┌─────────────────────────────────────────────────────┐
│  工作流设计器：编程助手                              │
├─────────────────────────────────────────────────────┤
│  节点库          │  画布                             │
│ ┌─────────────┐  │                                   │
│ │ ○ 开始      │  │   ┌───┐                          │
│ │ ⚡ LLM      │──┼──▶│开始│                          │
│ │ 📚 RAG      │  │   └─┬─┘                          │
│ │ 🔀 条件     │  │     │                            │
│ │ 🔁 循环     │  │     ▼                            │
│ │ 🔊 ASR      │  │   ┌─────┐                        │
│ │ 🔈 TTS      │  │   │输入 │                        │
│ │ ○ 输出      │  │   └─────┘                        │
│ └─────────────┘  │     │                            │
│                  │     ▼                            │
│                  │   ┌─────────┐                    │
│                  │   │RAG 检索  │                    │
│                  │   └─────────┘                    │
│                  │     │                            │
│                  │     ▼                            │
│                  │   ┌─────────┐                    │
│                  │   │LLM 回答  │                    │
│                  │   └─────────┘                    │
│                  │     │                            │
│                  │     ▼                            │
│                  │   ┌─────────┐                    │
│                  │   │  输出   │                    │
│                  │   └─────────┘                    │
└──────────────────┴───────────────────────────────────┘
```

### 2.2.2 工作流示例

#### 示例 1：智能客服工作流
```
开始
  ↓
用户提问
  ↓
RAG 知识库检索 ──→ 未找到 ──┐
  ↓                        │
找到答案                    │
  ↓                        │
LLM 整理答案                │
  ↓                        │
输出答案 ←────────────────┘
```

#### 示例 2：语音对话工作流
```
开始
  ↓
用户语音输入
  ↓
ASR 语音识别
  ↓
LLM 处理
  ↓
TTS 语音合成
  ↓
播放音频
```

#### 示例 3：文档分析工作流
```
开始
  ↓
上传文档
  ↓
解析文档内容
  ↓
RAG 向量化
  ↓
用户提问
  ↓
检索相关片段
  ↓
LLM 总结回答
  ↓
输出答案
```

### 2.2.3 工作流执行

**执行模式**：
- **同步执行**：等待所有节点完成
- **异步执行**：后台执行，webhook 通知
- **流式执行**：边执行边返回

**错误处理**：
- 节点失败重试（可配置次数）
- 失败回滚机制
- 异常捕获处理
- 超时处理

## 2.3 场景应用市场

### 2.3.1 预设 Agent 应用

#### 编程助手 Agent
**能力**：
- 代码编写辅助
- Bug 调试建议
- 代码审查
- 技术方案咨询

**配置**：
- 模型：GPT-4
- 知识库：编程知识库
- 提示词：专业程序员角色

#### 中医顾问 Agent
**能力**：
- 中医养生咨询
- 体质辨识
- 调理建议
- 药膳推荐

**配置**：
- 模型：GPT-3.5
- 知识库：中医知识库
- 提示词：老中医角色

#### 读书助理 Agent
**能力**：
- 书籍推荐
- 读书笔记整理
- 内容总结
- 阅读计划制定

**配置**：
- 模型：GPT-3.5
- 知识库：书籍摘要库
- 提示词：读书博主角色

#### 文案创作 Agent
**能力**：
- 营销文案
- 社交媒体内容
- 邮件撰写
- 创意写作

**配置**：
- 模型：GPT-4
- 知识库：优秀文案库
- 提示词：资深文案角色

### 2.3.2 Agent 分类

| 分类 | 示例 Agent | 数量 |
|------|-----------|------|
| 技术支援 | 编程助手、技术顾问 | 5+ |
| 教育学习 | 学习导师、语言教练 | 5+ |
| 健康养生 | 中医顾问、健身教练 | 3+ |
| 创作写作 | 文案创作、小说助手 | 5+ |
| 生活服务 | 旅游规划、美食推荐 | 5+ |
| 办公效率 | 会议纪要、邮件助手 | 5+ |

### 2.3.3 Agent 市场

**功能**：
- Agent 展示（分类、搜索、推荐）
- Agent 详情（介绍、评价、使用次数）
- Agent 使用（Web 聊天、API 调用）
- Agent 收藏
- Agent 分享
- Agent 评价

## 2.4 多 Agent 协作

### 2.4.1 协作场景

**场景 1：专家会诊**
```
用户问题
  ↓
主 Agent 接收
  ↓
分发给多个专家 Agent
  ├→ 编程专家
  ├→ 架构专家
  └→ 安全专家
  ↓
汇总各方意见
  ↓
整合回答
  ↓
返回用户
```

**场景 2：工作流接力**
```
用户请求
  ↓
Agent A 处理（ASR 识别）
  ↓
Agent B 处理（LLM 回答）
  ↓
Agent C 处理（TTS 合成）
  ↓
返回结果
```

### 2.4.2 协作配置

**配置项**：
- 主 Agent（协调者）
- 参与 Agent（专家）
- 分发策略（轮询/投票/并行）
- 结果整合策略（选择最佳/汇总）

---

# 三、管理后台

## 3.1 用户管理

**功能**：
- 用户列表
- 用户详情
- 用户状态管理（启用/禁用）
- 用户角色管理
- 用户行为审计

## 3.2 权限管理

**角色定义**：
- **超级管理员**：所有权限
- **运营人员**：Agent 管理、用户管理
- **普通用户**：创建 Agent、使用 Agent

**权限粒度**：
- Agent 创建
- Agent 编辑
- Agent 删除
- Agent 发布
- 工作流编排
- 知识库管理

## 3.3 数据看板

**核心指标**：
- 用户数（总数、日活、月活）
- Agent 数（总数、上线数）
- 请求数（日请求、月请求）
- Token 消耗（按 Agent、按用户）
- 成本统计（按 Provider）

**可视化图表**：
- 请求趋势图（日/周/月）
- Agent 使用排行
- Token 消耗分布
- 成本趋势

## 3.4 计费管理

**计费模式**：
- 免费额度（每日/每月）
- 按量计费（按 Token）
- 套餐包（月包、年包）
- 企业定制

**计费功能**：
- 账单生成
- 支付管理
- 发票管理
- 余额提醒

---

# 四、技术架构

## 4.1 技术栈选型

### 后端
- **框架**：FastAPI（与基座层统一）
- **数据库**：PostgreSQL（与基座层共享）
- **缓存**：Redis（与基座层共享）
- **消息队列**：RabbitMQ/Kafka（工作流异步）

### 前端
- **框架**：Vue 3
- **UI 库**：Element Plus
- **流程图**：X6 / LogicFlow
- **状态管理**：Pinia

### 部署
- **容器化**：Docker
- **编排**：Docker Compose
- **反向代理**：Nginx

## 4.2 与基座层集成

### 集成方式一：API 调用
```python
# Agent 平台调用基座 API
class AIGatewayClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
    
    async def chat(self, messages, **kwargs):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/chat/completions",
                headers={"X-API-Key": self.api_key},
                json={"messages": messages, **kwargs}
            )
            return response.json()
```

### 集成方式二：SDK 封装
```python
# 使用基座 SDK
from ai_gateway import AIGateway

client = AIGateway(api_key="xxx")

# 对话
response = await client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[...]
)

# ASR
response = await client.asr.transcribe(audio_url="...")

# TTS
response = await client.tts.synthesize(text="...", voice="zh-CN-XiaoxiaoNeural")
```

### 集成方式三：WebSocket
```javascript
// 实时语音对话
const ws = new WebSocket('ws://ai-gateway/ws/voice/chat');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'start',
    config: {...}
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'tts_audio') {
    playAudio(data.audio);
  }
};
```

## 4.3 数据模型

### 4.3.1 Agent 表

```sql
CREATE TABLE agents (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 关联
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 基本信息
    name VARCHAR(100) NOT NULL,                     -- Agent 名称
    description TEXT,                               -- 描述
    avatar_url VARCHAR(500),                        -- 头像
    category VARCHAR(50),                           -- 分类
    
    -- 角色设定
    system_prompt TEXT,                             -- 系统提示词
    persona JSONB,                                  -- 人设配置
    
    -- 能力配置
    capabilities JSONB DEFAULT '{}',                -- 能力配置
    -- 示例：{"llm": true, "asr": false, "tts": true, "rag": true}
    
    -- 模型配置
    default_model VARCHAR(50),                      -- 默认模型
    temperature DECIMAL(3, 2) DEFAULT 0.70,         -- 温度
    max_tokens INTEGER,                             -- 最大 Token
    
    -- 知识库绑定
    knowledge_base_ids UUID[],                      -- 知识库 ID 列表
    
    -- 记忆配置
    enable_short_memory BOOLEAN DEFAULT TRUE,       -- 短期记忆
    enable_long_memory BOOLEAN DEFAULT FALSE,       -- 长期记忆
    
    -- 工作流
    workflow_id UUID,                               -- 关联工作流
    workflow_config JSONB,                          -- 工作流配置
    
    -- 状态
    status SMALLINT NOT NULL DEFAULT 0,             -- 状态：0-草稿，1-上线，-1-下线
    is_public BOOLEAN DEFAULT FALSE,                -- 是否公开
    
    -- 统计
    usage_count INTEGER NOT NULL DEFAULT 0,         -- 使用次数
    like_count INTEGER NOT NULL DEFAULT 0,          -- 点赞数
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CONSTRAINT chk_status CHECK (status IN (-1, 0, 1))
);

-- 索引
CREATE INDEX idx_agents_user_id ON agents(user_id);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_category ON agents(category);
CREATE INDEX idx_agents_is_public ON agents(is_public);
CREATE INDEX idx_agents_created_at ON agents(created_at);

-- 注释
COMMENT ON TABLE agents IS 'Agent 信息表';
```

### 4.3.2 工作流表

```sql
CREATE TABLE workflows (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 关联
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 基本信息
    name VARCHAR(100) NOT NULL,                     -- 工作流名称
    description TEXT,                               -- 描述
    
    -- 流程配置
    nodes JSONB NOT NULL,                           -- 节点配置（JSON）
    edges JSONB NOT NULL,                           -- 连接关系（JSON）
    
    -- 执行配置
    timeout INTEGER DEFAULT 300,                    -- 超时时间（秒）
    retry_count INTEGER DEFAULT 3,                  -- 重试次数
    
    -- 状态
    status SMALLINT NOT NULL DEFAULT 1,             -- 状态：1-启用，0-禁用
    
    -- 统计
    execution_count INTEGER NOT NULL DEFAULT 0,     -- 执行次数
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CONSTRAINT chk_status CHECK (status IN (0, 1))
);

-- 索引
CREATE INDEX idx_workflows_agent_id ON workflows(agent_id);
CREATE INDEX idx_workflows_user_id ON workflows(user_id);
CREATE INDEX idx_workflows_status ON workflows(status);

-- 注释
COMMENT ON TABLE workflows IS '工作流配置表';
COMMENT ON COLUMN workflows.nodes IS '节点配置（JSON 格式）';
COMMENT ON COLUMN workflows.edges IS '节点连接关系（JSON 格式）';
```

---

# 五、实施计划

## 5.1 阶段划分

### 阶段一：Agent 管理基础（3 周）
- Agent CRUD
- Agent 配置
- Agent 测试
- Agent 列表

### 阶段二：工作流引擎（4 周）
- 可视化设计器
- 核心节点实现
- 工作流执行
- 错误处理

### 阶段三：场景应用（3 周）
- 预设 Agent（10+）
- Agent 市场
- 用户使用界面
- 分享功能

### 阶段四：完善优化（2 周）
- 多 Agent 协作
- 性能优化
- 测试完善
- 文档完善

**总计：12 周（3 个月）**

## 5.2 与基座层并行开发

```
时间轴：
第 1-2 月：基座层 MVP 开发
第 3 月：基座层完善 + Agent 平台启动
第 4-5 月：Agent 平台开发
第 6 月：集成测试 + 上线
```

---

# 六、验收标准

## 6.1 功能验收

- ✅ 可以创建、编辑、删除 Agent
- ✅ 可以编排工作流
- ✅ 可以执行工作流
- ✅ 预设 10+ Agent 应用
- ✅ Agent 市场正常展示
- ✅ 用户可以正常使用 Agent

## 6.2 性能验收

- ✅ Agent 创建 < 2 秒
- ✅ 工作流执行 < 5 秒（简单流程）
- ✅ 页面加载 < 2 秒
- ✅ 支持 50 人并发使用

## 6.3 集成验收

- ✅ 与基座层 API 调用正常
- ✅ 与基座层 WebSocket 连接正常
- ✅ 数据同步正常

---

# 七、总结

## 7.1 核心价值

**Agent 管理平台的价值**：
1. **降低使用门槛**：可视化编排，无需编程
2. **快速场景落地**：预设模板，快速创建
3. **能力复用**：一套基座，多个应用
4. **生态建设**：Agent 市场，促进交流

## 7.2 商业模式

**盈利模式**：
- Agent 使用付费（按 Token）
- 高级功能订阅（月费/年费）
- 企业定制（私有化部署）
- Agent 创作者分成

## 7.3 发展路径

```
阶段一（1-3 月）：基座层 MVP
  ↓
阶段二（4-6 月）：Agent 平台 MVP
  ↓
阶段三（7-9 月）：丰富场景应用
  ↓
阶段四（10-12 月）：开放生态
```

---

**文档结束**
