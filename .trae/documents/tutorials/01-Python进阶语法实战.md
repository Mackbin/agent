# Python 进阶语法实战 — 前端工程师的 2 小时速成

> **目标读者**：熟悉 JavaScript/TypeScript，想快速补齐 Python 进阶语法
> 
> **核心策略**：每个概念都用前端代码做对比，你一看就懂
> 
> **预计时间**：1.5-2 小时

---

## 目录

- [第一章：类型系统 — TS 开发者 10 分钟上手](#第一章类型系统--ts-开发者-10-分钟上手)
- [第二章：装饰器 — 前端的 HOC / Middleware](#第二章装饰器--前端的-hoc--middleware)
- [第三章：生成器 — 懒加载 / 流式处理](#第三章生成器--懒加载--流式处理)
- [第四章：上下文管理器 — try/finally 的优雅版](#第四章上下文管理器--tryfinally-的优雅版)
- [第五章：dataclass 和 TypedDict — interface 的 Python 版](#第五章dataclass-和-typeddict--interface-的-python-版)
- [第六章：实战练习 — 写一个完整的工具库](#第六章实战练习--写一个完整的工具库)
- [验收标准](#验收标准)

---

## 第一章：类型系统 — TS 开发者 10 分钟上手

### 1.1 对照表（直接迁移你的 TS 知识）

```typescript
// TypeScript
let name: string = "hello";
let age: number = 25;
let isActive: boolean = true;
let data: string | null = null;
let items: string[] = ["a", "b"];
let user: { name: string; age?: number } = { name: "张三" };
```

```python
# Python（几乎一模一样！）
name: str = "hello"
age: int = 25
is_active: bool = True
data: str | None = None  # 或 Optional[str] = None
items: list[str] = ["a", "b"]
user: dict[str, Any] = {"name": "张三"}
```

### 1.2 你需要重点学的差异点

#### 差异1：Python 没有 `undefined`，只有 `None`

```typescript
// TypeScript 有两个"空值"
let a: string | undefined = undefined;  // 未定义
let b: string | null = null;            // 空值
```

```python
# Python 只有一个空值
a: str | None = None  # 统一用 None
# 不存在 undefined 这个概念
```

#### 差异2：Union 类型用 `|` 而不是 `&`（注意！）

```typescript
// TypeScript：联合类型
type Status = 'loading' | 'success' | 'error';
type UserOrAdmin = User | Admin;

// TypeScript：交叉类型（合并对象）
type WithTimestamp = User & { createdAt: Date };
```

```python
# Python：联合类型（一样）
Status = Literal["loading", "success", "error"]
UserOrAdmin = User | Admin

# Python：没有交叉类型！用 dataclass 继承代替
@dataclass
class WithTimestamp(User):
    created_at: datetime
```

#### 差异3：泛型写法不同

```typescript
// TypeScript 泛型
function first<T>(items: T[]): T {
    return items[0];
}
const num = first([1, 2, 3]);        // 推断为 number
const str = first(["a", "b", "c"]);   // 推断为 string
```

```python
# Python 泛型
from typing import TypeVar, Generic

T = TypeVar("T")

def first(items: list[T]) -> T:
    return items[0]

num: int = first([1, 2, 3])          # 需要显式标注或让 IDE 推断
str_val: str = first(["a", "b", "c"])
```

### 1.3 动手练习：定义一个 API 响应类型

```python
from typing import TypedDict, Optional, Any, Literal
from datetime import datetime


class ApiSuccessResponse(TypedDict):
    """成功响应"""
    code: Literal[200]
    message: str
    data: Any


class ApiErrorResponse(TypedDict):
    """错误响应"""
    code: int  # 400/401/403/404/500 等
    message: str
    error_type: str
    details: Optional[list[dict]] = None


class PaginatedData(TypedDict):
    """分页数据结构"""
    items: list[Any]
    total: int
    page: int
    page_size: int
    has_more: bool


class PatientInfo(TypedDict):
    """患者信息"""
    id: int
    name: str
    gender: Literal["男", "女"]
    age: int
    chief_complaint: str
    symptoms: list[str]
    is_active: bool
    created_at: str  # ISO 格式日期字符串
```

**练习**：模仿上面，自己定义一个 `ChatMessage` 类型，包含 `role`、`content`、`timestamp`、`token_count` 字段。

---

## 第二章：装饰器 — 前端的 HOC / Middleware

### 2.1 核心概念

```
装饰器 = 给函数"穿衣服"

类比：
React HOC：
const withAuth = (WrappedComponent) => {
  return (props) => {
    if (!isLoggedIn()) return <Redirect to="/login" />
    return <WrappedComponent {...props} />
  }
}

Express/Koa 中间件：
app.use((req, res, next) => {
  console.log(`${req.method} ${req.url}`)
  next()  // 放行到下一个中间件
})

Python 装饰器：
@log_execution_time
def my_function():
    ...
# 等价于：my_function = log_execution_time(my_function)
```

### 2.2 从零实现一个计时装饰器

**Step 1：最简单的装饰器**

```python
import time
import functools


def my_decorator(func):
    """最简单的装饰器 — 不改变原函数行为"""
    
    def wrapper(*args, **kwargs):
        print(f"--- 函数 {func.__name__} 被调用了 ---")
        result = func(*args, **kwargs)
        print(f"--- 函数 {func.__name__} 执行完毕 ---")
        return result
    
    return wrapper


# 使用方式1：手动装饰
def say_hello(name):
    print(f"Hello, {name}!")

say_hello = my_decorator(say_hello)  # 手动把函数"包装"一下
say_hello("张三")
# 输出：
# --- 函数 say_hello 被调用了 ---
# Hello, 张三!
# --- 函数 say_hello 执行完毕 ---


# 使用方式2：语法糖 @（推荐）
@my_decorator
def say_goodbye(name):
    print(f"Goodbye, {name}!")

say_goodbye("李四")
# 输出：
# --- 函数 say_goodbye 被调用了 ---
# Goodbye, 李四!
# --- 函数 say_goodbye 执行完毕 ---
```

**Step 2：带参数的装饰器**

```python
def timer(show_args=False):
    """
    计时装饰器 — 可以配置是否显示参数
    
    用法：
    @timer()                    # 默认不显示参数
    @timer(show_args=True)      # 显示参数
    """
    def decorator(func):
        @functools.wraps(func)  # 重要！保留原函数的名称和文档
        def wrapper(*args, **kwargs):
            start = time.time()
            
            if show_args:
                print(f"[调用] {func.__name__}(args={args}, kwargs={kwargs})")
            
            result = func(*args, **kwargs)
            
            elapsed = (time.time() - start) * 1000
            print(f"[完成] {func.__name__} 耗时 {elapsed:.2f}ms")
            
            return result
        
        return wrapper
    
    return decorator


@timer()
def slow_operation():
    time.sleep(0.5)
    return "done"


@timer(show_args=True)
def greet(name: str, greeting: str = "你好"):
    return f"{greeting}，{name}！"


slow_operation()
# 输出：[完成] slow_operation 耗时 500.xxms

greet("张三")
# 输出：
# [调用] greet(args=('张三',), kwargs={'greeting': '你好'})
# [完成] greet 耗时 0.02ms
```

**Step 3：带返回值的装饰器**

```python
def cache_result(ttl_seconds=60):
    """
    缓存装饰器 — 相同参数不重复计算
    
    类比：React 的 useMemo / Vue 的 computed
    """
    cache: dict[tuple, tuple] = {}  # {(args, kwargs): (result, timestamp)}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存 key（参数的元组形式）
            key = (args, frozenset(kwargs.items()))
            
            now = time.time()
            
            # 检查缓存是否存在且未过期
            if key in cache:
                result, cached_at = cache[key]
                if now - cached_at < ttl_seconds:
                    print(f"[缓存命中] {func.__name__}")
                    return result
            
            # 缓存未命中，执行原函数
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            print(f"[缓存写入] {func.__name__}")
            
            return result
        
        wrapper.cache_clear = lambda: cache.clear()  # 清除缓存的方法
        return wrapper
    
    return decorator


import random

@cache_result(ttl_seconds=10)
def expensive_computation(x: int, y: int) -> int:
    """模拟耗时计算"""
    time.sleep(0.3)
    return x * y + random.randint(0, 100)


# 第一次调用：执行函数并缓存
print(expensive_computation(3, 4))
# 输出：[缓存写入] expensive_computation → 结果（耗时约300ms）

# 第二次调用（相同参数）：直接返回缓存
print(expensive_computation(3, 4))
# 输出：[缓存命中] expensive_computation → 结果（瞬间返回）

# 不同参数：重新计算
print(expensive_computation(5, 6))
# 输出：[缓存写入] expensive_computation → 新结果
```

**Step 4：异步函数的装饰器**

```python
async def retry(max_retries: int = 3, delay: float = 1.0):
    """
    重试装饰器 — 失败自动重试
    
    适用场景：调用外部 API 时网络不稳定
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt > 1:
                        wait_time = delay * (2 ** (attempt - 2))  # 指数退避
                        print(f"[重试] 第{attempt}次尝试，等待{wait_time:.1f}s...")
                        await asyncio.sleep(wait_time)
                    
                    return await func(*args, **kwargs)
                
                except Exception as e:
                    last_exception = e
                    print(f"[失败] 第{attempt}次: {e}")
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time as _time
            last_exception = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt > 1:
                        wait_time = delay * (2 ** (attempt - 2))
                        _time.sleep(wait_time)
                    return func(*args, **kwargs)
                
                except Exception as e:
                    last_exception = e
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


import asyncio


@retry(max_retries=3, delay=1)
async def unstable_api_call():
    """模拟不稳定的 API 调用"""
    if random.random() < 0.6:  # 60% 概率失败
        raise ConnectionError("连接超时")
    return {"status": "ok", "data": "success"}


async def main():
    result = await unstable_api_call()
    print(f"最终结果: {result}")

asyncio.run(main())
# 可能输出：
# [失败] 第1次: 连接超时
# [重试] 第2次尝试，等待1.0s...
# [失败] 第2次: 连接超时
# [重试] 第3次尝试，等待2.0s...
# 最终结果: {'status': 'ok', 'data': 'success'}
```

### 2.3 FastAPI 中常见的装饰器用法

```python
# 这些你在项目中会经常看到：

@app.get("/api/users")           # 路由装饰器 — 注册 GET 接口
@app.post("/api/users")          # 路由装饰器 — 注册 POST 接口
@app.exception_handler(404)      # 异常处理器装饰器
@app.on_event("startup")         # 启动事件装饰器

# Pydantic 校验装饰器
@field_validator("email")        # 字段校验器
@model_validator(mode="before")  # 模型校验器

# 第三方库的装饰器
@lru_cache(maxsize=128)          # 内置缓存
@rate_limit(calls=10, period=60) # 限流（第三方库）
```

---

## 第三章：生成器 — 懒加载 / 流式处理

### 3.1 核心概念

```
普通函数 vs 生成器函数：

普通函数：
def get_all_users():
    users = db.query_all()  # 一次性加载100万条数据到内存
    return users            # 返回整个列表

问题：内存爆炸！

生成器函数：
def stream_users():
    for user in db.cursor():  # 逐条从数据库读取
        yield user            # 每次只产生一条数据

优势：
- 内存友好：同一时间只有一条数据在内存中
- 惰性求值：用到的时候才计算
- 可无限：可以表示无限序列
```

### 3.2 动手实现

**示例1：逐行读取大文件**

```python
def read_large_file(filepath: str):
    """
    逐行读取大文件 — 内存 O(1)
    
    对比：
    普通方式：lines = open(file).readlines()  # 文件多大，内存就占多少
    生成器方式：每次只读一行到内存
    """
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            yield line.strip()


# 使用方式
for line in read_large_file("big_data.txt"):
    process(line)  # 每次只处理一行
```

**示例2：分页查询（SSE 流式输出场景）**

```python
def paginate_results(query_fn, page_size: int = 100):
    """
    分页生成结果 — 适用于大量数据的流式处理
    
    场景：导出数据、批量处理、SSE 推送
    """
    offset = 0
    while True:
        results = query_fn(limit=page_size, offset=offset)
        
        if not results:
            break
        
        yield results  # 产出当前页的数据
        
        offset += page_size
        
        if len(results) < page_size:
            break  # 最后一页


# 使用示例
for page in paginate_results(db.fetch_users, page_size=50):
    send_to_frontend(page)  # 每次发送一页数据
```

**示例3：无限序列（测试数据生成）**

```python
def generate_test_data(count: int):
    """生成测试患者数据"""
    names = ["张三", "李四", "王五", "赵六", "钱七"]
    symptoms = [["失眠"], ["头痛", "头晕"], ["胃胀", "食欲不振"]]
    
    for i in range(count):
        yield {
            "id": i + 1,
            "name": names[i % len(names)] + str(i // len(names)),
            "symptoms": symptoms[i % len(symptoms)],
            "created_at": datetime.now().isoformat(),
        }


# 使用：只取需要的数量
test_patients = list(generate_test_data(100))  # 取100条
first_10 = list(islice(generate_test_data(1000), 10))  # 只取前10条
```

**示例4：管道式数据处理（类似 Linux 管道）**

```python
def read_lines(filepath):
    """读取文件的每一行"""
    with open(filepath) as f:
        for line in f:
            yield line


def filter_lines(lines, keyword):
    """过滤包含关键词的行"""
    for line in lines:
        if keyword in line:
            yield line


def transform_line(lines):
    """转换每行的格式"""
    for line in lines:
        yield line.strip().upper()


def batch(lines, size=100):
    """按批次打包"""
    batch_list = []
    for item in lines:
        batch_list.append(item)
        if len(batch_list) >= size:
            yield batch_list
            batch_list = []
    if batch_list:
        yield batch_list


# 组合使用（管道模式）
pipeline = batch(
    transform_line(
        filter_lines(
            read_lines("data.txt"),
            keyword="ERROR"
        )
    ),
    size=50
)

for batch_items in pipeline:
    save_to_database(batch_items)  # 每批50条入库
```

### 3.3 生成器表达式（列表推导式的惰性版本）

```python
# 列表推导式（立即执行，占用内存）
squares = [x * x for x in range(1000000)]  # 生成100万个数字的列表

# 生成器表达式（惰性执行，不占内存）
squares_gen = (x * x for x in range(1000000))  # 生成器对象，还没计算

print(next(squares_gen))  # 0
print(next(squares_gen))  # 1
print(next(squares_gen))  # 4
# 只有调用 next() 才会计算下一个值

# 常见用途：传给 sum/max/min/any/all 等函数
total = sum(x * x for x in range(1000000))  # 不需要创建完整列表
max_value = max(len(word) for word in words)  # 找最长单词的长度
has_error = any("ERROR" in line for line in lines)  # 是否有错误日志
```

---

## 第四章：上下文管理器 — try/finally 的优雅版

### 4.1 核心概念

```javascript
// 前端：try/finally 确保资源释放
async function fetchData() {
  const connection = await createConnection();
  try {
    const data = await connection.query('SELECT * FROM users');
    return data;
  } finally {
    await connection.close();  // 无论成功失败都会执行
  }
}
```

```python
# Python：with 语句更简洁
async def fetch_data():
    async with create_connection() as conn:
        data = await conn.execute('SELECT * FROM users')
        return data
    # 自动关闭连接，无需 finally
```

### 4.2 常见的 with 用法

**用法1：文件操作（最常见）**

```python
# ❌ 不好的写法（可能忘记关闭文件）
f = open("config.json", "r")
data = json.load(f)
f.close()

# ✅ 好的写法（自动关闭）
with open("config.json", "r", encoding="utf-8") as f:
    data = json.load(f)
# 离开 with 块后，文件自动关闭（即使发生异常）


# 同时操作多个文件
with open("input.txt", "r") as fin, open("output.txt", "w") as fout:
    for line in fin:
        processed = process(line)
        fout.write(processed)
```

**用法2：数据库事务**

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def transfer_money(
    session: AsyncSession,
    from_id: int,
    to_id: int,
    amount: float,
):
    """
    转账操作 — 必须在事务中执行
    
    要么全部成功（commit），要么全部回滚（rollback）
    """
    async with session.begin():  # 自动开始事务
        # 扣款
        from_account = await session.get(Account, from_id)
        from_account.balance -= amount
        
        # 收款
        to_account = await session.get(Account, to_id)
        to_account.balance += amount
        
        # 如果这里抛出异常，事务自动回滚
        # await session.commit()  # 正常结束自动 commit
```

**用法3：锁操作**

```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def acquire_lock(redis, lock_key: str, timeout: int = 10):
    """分布式锁的上下文管理器"""
    acquired = False
    try:
        acquired = await redis.set(lock_key, "locked", nx=True, ex=timeout)
        if not acquired:
            raise RuntimeError(f"无法获取锁: {lock_key}")
        yield  # 锁已获取，执行业务逻辑
    finally:
        if acquired:
            await redis.delete(lock_key)  # 释放锁


# 使用
async def critical_section(redis, task_id: str):
    async with acquire_lock(redis, f"lock:{task_id}", timeout=30):
        # 这里的代码在同一时刻只有一个进程能执行
        result = await do_something_critical()
        return result
```

**用法4：计时上下文（调试神器）**

```python
from contextlib import contextmanager
import time

@contextmanager
def timer(operation_name: str):
    """计时上下文管理器"""
    start = time.perf_counter()
    print(f"[开始] {operation_name}")
    try:
        yield  # 执行被计时的代码块
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        print(f"[完成] {operation_name} — 耗时 {elapsed:.2f}ms")


# 使用
with timer("数据库查询"):
    patients = await db.fetch_all("SELECT * FROM patients")

with timer("AI 生成回复"):
    response = await llm.generate(prompt)

# 输出：
# [开始] 数据库查询
# [完成] 数据库查询 — 耗时 45.23ms
# [开始] AI 生成回复
# [完成] AI 生成回复 — 耗时 1234.56ms
```

---

## 第五章：dataclass 和 TypedDict — interface 的 Python 版

### 5.1 dataclass：可变的数据对象

```python
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from enum import Enum


class Gender(str, Enum):
    MALE = "男"
    FEMALE = "女"


@dataclass
class Patient:
    """患者数据模型 — 类似 TypeScript 的 class/interface"""
    
    id: int
    name: str
    gender: Gender
    age: int
    phone: str
    chief_complaint: str
    symptoms: list[str] = field(default_factory=list)
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def full_display_name(self) -> str:
        """实例方法"""
        return f"{self.name}（{self.gender}，{self.age}岁）"
    
    @property
    def is_new_patient(self) -> bool:
        """计算属性 — 类似 Vue 的 computed / getter"""
        return (datetime.now() - self.created_at).days <= 7
    
    def update_symptoms(self, new_symptoms: list[str]):
        """修改方法"""
        self.symptoms = new_symptoms
        self.updated_at = datetime.now()


# 创建实例
patient = Patient(
    id=1,
    name="张三",
    gender=Gender.MALE,
    age=35,
    phone="13800138000",
    chief_complaint="失眠三个月余",
    symptoms=["失眠", "多梦"],
)

# 访问属性
print(patient.name)              # 张三
print(patient.full_display_name())  # 张三（男，35岁）
print(patient.is_new_patient)     # True/False

# 修改属性
patient.update_symptoms(["失眠", "多梦", "心烦"])

# 转换为字典（用于 JSON 序列化）
patient_dict = asdict(patient)
# {'id': 1, 'name': '张三', ...}

import json
json_str = json.dumps(patient_dict, ensure_ascii=False, default=str)
```

### 5.2 TypedDict：不可变的类型提示

```python
from typing import TypedDict, Required, NotRequired


class ChatMessage(TypedDict):
    """
    聊天消息的类型定义
    
    类似 TypeScript：
    interface ChatMessage {
      role: 'user' | 'assistant' | 'system'
      content: string
      timestamp: number
      tokenCount?: number
      metadata?: Record<string, any>
    }
    """
    role: Required[str]  # 必填字段
    content: Required[str]
    timestamp: Required[float]
    token_count: NotRequired[int]  # 可选字段
    metadata: NotRequired[dict]


# 使用（像字典一样操作，但有类型检查）
message: ChatMessage = {
    "role": "user",
    "content": "我最近失眠怎么办？",
    "timestamp": 1700000000.0,
    # token_count 是可选的，可以不传
}

# 类型安全的访问
role: str = message["role"]       # IDE 能推断出是 str
content: str = message["content"]  # IDE 能推断出是 str
```

### 5.3 Enum：枚举常量

```python
from enum import Enum, auto


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    DOCTOR = "doctor"
    ASSISTANT = "assistant"
    PATIENT = "patient"


class MessageRole(str, Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class LLMProvider(str, Enum):
    """LLM 提供商枚举"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    CLAUDE = "claude"
    QWEN = "qwen"


# 在业务逻辑中使用
def get_permissions(role: UserRole) -> list[str]:
    """根据角色获取权限列表"""
    permissions = {
        UserRole.ADMIN: ["read", "write", "delete", "manage_users"],
        UserRole.DOCTOR: ["read", "write", "diagnose"],
        UserRole.ASSISTANT: ["read", "ai_chat", "followup"],
        UserRole.PATIENT: ["read_own_profile"],
    }
    return permissions.get(role, [])


# 类型安全：只能传入预定义的值
perms = get_permissions(UserRole.DOCTOR)  # ✅ 正确
# perms = get_permissions("manager")     # ❌ 类型错误（IDE 会报错）
```

### 5.4 实战：定义一套完整的业务数据模型

```python
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime
from enum import Enum


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class Conversation:
    """对话"""
    id: str
    user_id: int
    title: str
    status: ConversationStatus = ConversationStatus.ACTIVE
    message_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Message:
    """消息"""
    id: str
    conversation_id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    token_count: int = 0
    model_used: Optional[str] = None
    latency_ms: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FollowUpPlan:
    """随访计划"""
    id: str
    patient_id: int
    planned_date: datetime
    content: str
    status: str = "pending"  # pending / sent / completed
    created_by: int = 0  # 操作人 ID
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class KnowledgeBase:
    """知识库"""
    id: str
    name: str
    description: str
    category: str  # 医案 / 方剂 / 理论 / 食疗
    chunk_count: int = 0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


# 工厂方法：方便创建实例
@dataclass
class MessageFactory:
    """消息工厂 — 封装创建逻辑"""
    
    @staticmethod
    def create_user_message(conversation_id: str, content: str) -> Message:
        return Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="user",
            content=content,
            created_at=datetime.now(),
        )
    
    @staticmethod
    def create_assistant_message(
        conversation_id: str,
        content: str,
        model: str = "gpt-4o-mini",
        tokens: int = 0,
        latency_ms: int = 0,
    ) -> Message:
        return Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            token_count=tokens,
            model_used=model,
            latency_ms=latency_ms,
            created_at=datetime.now(),
        )
```

---

## 第六章：实战练习 — 写一个完整的工具库

### 6.1 练习要求

创建 `app/utils.py`，包含以下工具函数：

```python
"""
app/utils.py — 通用工具库

要求实现以下功能：
1. format_response() — 统一 API 响应格式
2. retry_decorator — 重试装饰器
3. timer_context — 计时上下文管理器
4. paginate() — 分页生成器
5. mask_sensitive_data() — 数据脱敏
"""

import time
import functools
import re
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generator, Optional


def format_response(
    code: int = 200,
    message: str = "success",
    data: Any = None,
) -> dict:
    """
    统一 API 响应格式
    
    TODO: 实现这个函数
    要求：返回 {"code": ..., "message": ..., "data": ...}
    """


@contextmanager
def timer(operation_name: str) -> Generator[None, None, None]:
    """
    计时上下文管理器
    
    TODO: 实现这个函数
    要求：
    - 进入时打印 "[开始] {operation_name}"
    - 退出时打印 "[完成] {operation_name} — 耗时 xxx.xxmms"
    """


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
):
    """
    重试装饰器
    
    TODO: 实现这个装饰器
    要求：
    - 支持 async 和 sync 函数
    - 失败后指数退避重试
    - 打印每次重试的信息
    """


def paginate(items: list, page_size: int = 20) -> Generator[list, None, None]:
    """
    分页生成器
    
    TODO: 实现这个生成器
    要求：将列表按 page_size 分成多个小列表
    示例：paginate([1,2,3,4,5], 2) → [[1,2], [3,4], [5]]
    """


def mask_phone(phone: str) -> str:
    """手机号脱敏：138****8000"""


def mask_id_card(id_card: str) -> str:
    """身份证脱敏：110***********1234"""


def mask_name(name: str) -> str:
    """姓名脱敏：张** （保留姓）"""


def mask_sensitive_data(data: dict, fields: list[str] = None) -> dict:
    """
    数据脱敏 — 自动识别敏感字段并脱敏
    
    TODO: 实现这个函数
    要求：
    - 自动识别 phone/id_card/name 字段
    - 递归处理嵌套字典和列表
    - 返回脱敏后的新字典（不修改原数据）
    """


if __name__ == "__main__":
    # 测试代码
    print("=== 测试 format_response ===")
    print(format_response())
    print(format_response(code=404, message="未找到"))
    
    print("\n=== 测试 timer ===")
    with timer("测试操作"):
        time.sleep(0.1)
    
    print("\n=== 测试 paginate ===")
    for page in paginate(list(range(10)), 3):
        print(page)
    
    print("\n=== 测试脱敏 ===")
    test_data = {
        "name": "张三丰",
        "phone": "13800138000",
        "id_card": "110101199001011234",
        "nested": {
            "name": "李四",
            "phone": "13900139000",
        },
        "list": [
            {"name": "王五", "phone": "13700137000"},
        ],
    }
    print(mask_sensitive_data(test_data))
```

### 6.2 参考答案

<details>
<summary>点击查看参考答案</summary>

```python
def format_response(
    code: int = 200,
    message: str = "success",
    data: Any = None,
) -> dict:
    return {"code": code, "message": message, "data": data}


@contextmanager
def timer(operation_name: str) -> Generator[None, None, None]:
    start = time.perf_counter()
    print(f"[开始] {operation_name}")
    try:
        yield
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        print(f"[完成] {operation_name} — 耗时 {elapsed:.2f}ms")


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
):
    import asyncio
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt > 1:
                        wait = delay * (2 ** (attempt - 2))
                        print(f"[重试] 第{attempt}次，等待{wait}s")
                        await asyncio.sleep(wait)
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    print(f"[失败] 第{attempt}次: {e}")
            raise last_exc
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt > 1:
                        wait = delay * (2 ** (attempt - 2))
                        time.sleep(wait)
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
            raise last_exc
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def paginate(items: list, page_size: int = 20) -> Generator[list, None, None]:
    for i in range(0, len(items), page_size):
        yield items[i : i + page_size]


def mask_phone(phone: str) -> str:
    if len(phone) >= 7:
        return phone[:3] + "****" + phone[-4:]
    return "****"


def mask_id_card(id_card: str) -> str:
    if len(id_card) >= 14:
        return id_card[:3] + "*" * (len(id_card) - 7) + id_card[-4:]
    return "****"


def mask_name(name: str) -> str:
    if len(name) >= 2:
        return name[0] + "**"
    return "*"


def mask_sensitive_data(data: dict, fields: list[str] = None) -> dict:
    if fields is None:
        fields = ["phone", "手机", "id_card", "身份证", "name", "姓名"]
    
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = mask_sensitive_data(value, fields)
        elif isinstance(value, list):
            result[key] = [
                mask_sensitive_data(item, fields) if isinstance(item, dict) else item
                for item in value
            ]
        elif key.lower().replace(" ", "_") in [f.lower().replace(" ", "_") for f in fields]:
            if "phone" in key.lower() or "手机" in key:
                result[key] = mask_phone(str(value))
            elif "id_card" in key.lower() or "身份证" in key:
                result[key] = mask_id_card(str(value))
            elif "name" in key.lower() or "姓名" in key:
                result[key] = mask_name(str(value))
            else:
                result[key] = value
        else:
            result[key] = value
    
    return result
```

</details>

---

## 验收标准

学完本教程后，你应该能够：

### ✅ 必须掌握

- [ ] 能看懂并写出带参数的装饰器（计时/缓存/重试）
- [ ] 能区分同步和异步装饰器的写法
- [ ] 能用生成器处理大数据集（分页/流式读取）
- [ ] 能用 `with` 语句管理资源（文件/数据库事务/锁）
- [ ] 能用 `dataclass` 定义业务数据模型
- [ ] 能用 `TypedDict` 定义 API 请求/响应类型
- [ ] 能用 `Enum` 定义常量枚举

### ✅ 应该掌握

- [ ] 能解释 `@functools.wraps()` 的作用
- [ ] 知道什么时候用生成器表达式代替列表推导式
- [ ] 能自定义上下文管理器（`@contextmanager`）

### 自测题

1. **装饰器和中间件有什么区别？什么时候用哪个？**
   
2. **`yield` 和 `return` 在函数中的区别是什么？**
   
3. **为什么数据库操作要用 `with session.begin():` 而不是手动 commit/rollback？**
   
4. **`dataclass` 和 `TypedDict` 应该怎么选择？**

---

> **下一步**：继续学习 [02-FastAPI实战指南.md](./02-FastAPI实战指南.md)，把这些语法应用到实际的 Web 开发中。
