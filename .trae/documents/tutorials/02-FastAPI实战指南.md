# FastAPI 完整实战指南 — 从 Hello World 到生产级 API

> **目标读者**：有前端经验（React/Vue/Express），想快速掌握 Python 后端开发
> 
> **学习方式**：每一步都照着写代码，运行看结果。不要只看不练。
> 
> **预计时间**：3-4 小时（分2-3次完成）

---

## 目录

- [第一章：5分钟跑通第一个接口](#第一章5分钟跑通第一个接口)
- [第二章：请求与响应（Pydantic 模型）](#第二章请求与响应pydantic-模型)
- [第三章：CRUD 完整实现（增删改查）](#第三章crud-完整实现增删改查)
- [第四章：依赖注入系统](#第四章依赖注入系统)
- [第五章：中间件与全局处理](#第五章中间件与全局处理)
- [第六章：SSE 流式响应（AI 对话必备）](#第六章sse-流式响应ai-对话必备)
- [第七章：错误处理体系](#第七章错误处理体系)
- [第八章：综合练习项目](#第八章综合练习项目)
- [验收标准清单](#验收标准清单)

---

## 第一章：5分钟跑通第一个接口

### 1.1 你需要准备的环境

```bash
# 1. 确认 Python 版本（需要 3.10+）
python --version
# 输出应该是 Python 3.10.x 或更高

# 2. 创建虚拟环境（隔离依赖）
python -m venv venv

# 3. 激活虚拟环境
# Mac/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 4. 安装 FastAPI + 运行服务器
pip install fastapi uvicorn

# 5. 创建项目目录结构
mkdir -p my_api/app
cd my_api
```

### 1.2 写你的第一个文件

创建 `app/main.py`：

```python
from fastapi import FastAPI

app = FastAPI(title="我的第一个API", version="1.0.0")


@app.get("/")
def read_root():
    """首页 — 类似前端路由的 /"""
    return {"message": "Hello World", "status": "ok"}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    """
    路径参数 — 类似 :id
    
    前端对比：
    Express: app.get('/items/:id', (req, res) => { ... })
    React Router: <Route path="/items/:id" element={<ItemDetail />} />
    """
    return {"item_id": item_id, "name": f"商品{item_id}"}


@app.get("/search")
def search(keyword: str, page: int = 1):
    """
    查询参数 — 类似 req.query
    
    访问方式: /search?keyword=手机&page=2
    
    前端对比：
    const params = new URLSearchParams({ keyword: '手机', page: '2' });
    fetch(`/search?${params}`)
    """
    return {
        "keyword": keyword,
        "page": page,
        "results": [
            {"id": 1, "title": f"{keyword}相关结果1"},
            {"id": 2, "title": f"{keyword}相关结果2"},
        ]
    }
```

### 1.3 启动服务

```bash
# 在终端运行
uvicorn app.main:app --reload --port 8000

# 你会看到这样的输出：
# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process [12345]
# INFO:     Started server process [12346]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
```

### 1.4 测试你的接口

打开浏览器或用命令行测试：

```bash
# 测试1：根路径
curl http://localhost:8000/
# 返回: {"message":"Hello World","status":"ok"}

# 测试2：路径参数
curl http://localhost:8000/items/42
# 返回: {"item_id":42,"name":"商品42"}

# 测试3：查询参数
curl "http://localhost:8000/search?keyword=手机&page=1"
# 返回: {"keyword":"手机","page":1,"results":[...]}

# 测试4：自动生成的交互式文档（这个很强大！）
# 打开浏览器访问：http://localhost:8000/docs
```

### 1.5 自动生成的 API 文档

FastAPI 最棒的功能之一：**自动生成交互式 API 文档**

访问 `http://localhost:8000/docs`，你会看到：

```
┌─────────────────────────────────────────────┐
│  📖 Swagger UI — 交互式 API 文档              │
│                                             │
│  GET  /          → Try it out → Execute     │
│  GET  /items/{item_id} → 输入参数 → Execute │
│  GET  /search?keyword=&page= → Execute      │
│                                             │
│  每个接口都可以直接在网页上测试！             │
│  相当于 Postman 内置在项目里                 │
└─────────────────────────────────────────────┘
```

**前端对比**：这就像你用了 TypeScript 写了完整的 JSDoc，然后自动生成了 API 文档页面。

---

## 第二章：请求与响应（Pydantic 模型）

### 2.1 什么是 Pydantic？

```
前端类比：

TypeScript interface:
interface CreateUserRequest {
  name: string;
  email: string;
  age?: number;           // 可选
}

Python Pydantic model:
class CreateUserRequest(BaseModel):
    name: str
    email: str
    age: int | None = None   # 可选

区别：
- TS 只做类型检查（开发时）
- Pydantic 做数据验证（运行时！）
  - 类型不对 → 自动返回 422 错误
  - 字段缺失 → 自动返回 422 错误
  - 格式不对（如email格式）→ 可以自定义校验
```

### 2.2 动手写一个用户注册接口

在 `app/main.py` 中添加：

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import re

app = FastAPI(title="用户管理API")


# ════════════════════════════════════════════
# 定义数据模型（= TypeScript interface）
# ════════════════════════════════════════════

class UserCreate(BaseModel):
    """创建用户的请求体"""
    
    name: str = Field(
        ...,  # ... 表示必填（相当于 required: true）
        min_length=2,
        max_length=50,
        description="用户姓名",
        examples=["张三"],
    )
    email: EmailStr  # 自动校验邮箱格式！
    age: Optional[int] = Field(None, ge=0, le=150, description="年龄")
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    
    @field_validator("name")
    @classmethod
    def name_must_not_contain_special_chars(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("姓名不能为纯空格")
        return v.strip()


class UserResponse(BaseModel):
    """返回给前端的用户信息"""
    
    id: int
    name: str
    email: str
    age: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ApiResponse(BaseModel):
    """统一响应格式（类似前端封装的 axios response）"""
    
    code: int
    message: str
    data: Optional[dict | list] = None


# ════════════════════════════════════════════
# 模拟数据库（后面会换成真正的数据库）
# ════════════════════════════════════════════

fake_db: dict[int, dict] = {}  # {id: user_data}
user_id_counter = 1


# ════════════════════════════════════════════
# 接口实现
# ════════════════════════════════════════════

@app.post("/api/users", response_model=ApiResponse)
def create_user(user: UserCreate):
    """
    创建用户 — POST 接口
    
    前端调用方式：
    ```ts
    const res = await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: '张三',
        email: 'zhangsan@test.com',
        age: 25,
        phone: '13800138000'
      })
    })
    const data = await res.json()
    // data = { code: 200, message: "创建成功", data: {...} }
    ```
    """
    global user_id_counter
    
    # 检查邮箱是否已存在
    for existing in fake_db.values():
        if existing["email"] == user.email:
            raise HTTPException(
                status_code=409,
                detail={"code": 409, "message": "该邮箱已被注册", "data": None},
            )
    
    # 创建用户记录
    new_user = {
        "id": user_id_counter,
        "name": user.name,
        "email": user.email,
        "age": user.age,
        "phone": user.phone,
        "created_at": datetime.now().isoformat(),
    }
    fake_db[user_id_counter] = new_user
    user_id_counter += 1
    
    return ApiResponse(code=200, message="创建成功", data=new_user)


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    """获取单个用户"""
    if user_id not in fake_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return fake_db[user_id]


@app.get("/api/users", response_model=list[UserResponse])
def list_users(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
):
    """用户列表（支持分页）"""
    users = list(fake_db.values())
    paginated_users = users[skip : skip + limit]
    return paginated_users


@app.put("/api/users/{user_id}", response_model=ApiResponse)
def update_user(user_id: int, user_update: UserCreate):
    """更新用户"""
    if user_id not in fake_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    fake_db[user_id].update({
        "name": user_update.name,
        "email": user_update.email,
        "age": user_update.age,
        "phone": user_update.phone,
    })
    
    return ApiResponse(code=200, message="更新成功", data=fake_db[user_id])


@app.delete("/api/users/{user_id}", response_model=ApiResponse)
def delete_user(user_id: int):
    """删除用户"""
    if user_id not in fake_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    del fake_db[user_id]
    return ApiResponse(code=200, message="删除成功", data=None)
```

### 2.3 安装额外依赖并测试

```bash
# Pydantic 的 EmailStr 需要 email-validator
pip install email-validator pydantic[email]

# 重启服务
uvicorn app.main:app --reload --port 8000
```

### 2.4 用 Swagger UI 测试

打开 `http://localhost:8000/docs`，试试以下操作：

```
步骤1：点击 POST /api/users → Try it out
步骤2：输入请求体（注意看字段说明和校验规则）：
{
  "name": "张三",
  "email": "zhang@test.com",
  "age": 25,
  "phone": "13800138000"
}
步骤3：点击 Execute → 看返回结果

然后尝试这些"坏数据"，观察返回的错误：
❌ {"name": ""}                    → 应该报错（太短）
❌ {"name": "A"}                   → 应该报错（太短）
❌ {"email": "not-an-email"}       → 应该报错（不是邮箱）
❌ {"age": 200}                    → 应该报错（超过150）
❌ {"phone": "12345678901"}        → 应该报错（不是手机号格式）
```

### 2.5 Pydantic 校验能力一览表

| 功能 | 写法 | 效果 |
|------|------|------|
| 必填字段 | `name: str` | 不传则报 422 |
| 可选字段 | `age: int \| None = None` | 不传则为 null |
| 默认值 | `page: int = 1` | 不传则用默认值 |
| 最小长度 | `min_length=2` | 少于2字符报错 |
| 最大值 | `le=150` | 大于150报错 |
| 正则匹配 | `pattern=r"^1[3-9]\\d{9}$"` | 格式不匹配报错 |
| 自定义校验 | `@field_validator` | 复杂逻辑校验 |
| 邮箱格式 | `EmailStr` | 自动校验邮箱 |
| URL 格式 | `HttpUrl` | 自动校验 URL |

---

## 第三章：CRUD 完整实现（增删改查）

### 3.1 CRUD 是什么？

```
CRUD = Create(创建) Read(读取) Update(更新) Delete(删除)

对应 HTTP 方法：
POST    → Create  （新建资源）
GET     → Read    （查询资源）
PUT     → Update  （完整更新）
PATCH   → Update  （部分更新）
DELETE  → Delete  （删除资源）

前端类比：
REST Client / Axios 封装：
const api = {
  create: (data) => axios.post('/resource', data),
  getById: (id) => axios.get(`/resource/${id}`),
  list: (params) => axios.get('/resource', { params }),
  update: (id, data) => axios.put(`/resource/${id}`, data),
  delete: (id) => axios.delete(`/resource/${id}`),
}
```

### 3.2 实战：患者管理模块（中医诊所场景）

创建 `app/models.py`：

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class GenderEnum(str, Enum):
    MALE = "男"
    FEMALE = "女"
    OTHER = "其他"


class PatientCreate(BaseModel):
    """创建患者"""
    name: str = Field(..., min_length=2, max_length=50)
    gender: GenderEnum
    age: int = Field(..., ge=0, le=150)
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    chief_complaint: str = Field(..., max_length=2000, description="主诉")
    symptoms: Optional[list[str]] = None  # ["失眠", "头晕"]
    notes: Optional[str] = Field(None, max_length=5000)


class PatientUpdate(BaseModel):
    """更新患者（所有字段可选）"""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    gender: Optional[GenderEnum] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    chief_complaint: Optional[str] = Field(None, max_length=2000)
    symptoms: Optional[list[str]] = None
    notes: Optional[str] = Field(None, max_length=5000)


class PatientResponse(BaseModel):
    """患者详情（返回给前端）"""
    id: int
    name: str
    gender: str
    age: int
    phone: str  # 生产环境应该脱敏
    chief_complaint: str
    symptoms: Optional[list[str]] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    """通用分页响应"""
    data: list
    total: int
    page: int
    size: int
    has_more: bool
```

创建 `app/routers/patients.py`：

```python
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime
from app.models import (
    PatientCreate, PatientUpdate, PatientResponse, PaginatedResponse,
)

router = APIRouter(prefix="/api/v1/patients", tags=["患者管理"])


# ━━━ 模拟数据库存储 ━━━
patients_db: dict[int, dict] = {}
patient_id_counter = 1


@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(patient: PatientCreate):
    """
    新建患者
    
    前端调用示例：
    ```ts
    await fetch('/api/v1/patients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: '李四',
        gender: '女',
        age: 35,
        phone: '13900139000',
        chief_complaint: '失眠三个月余，入睡困难',
        symptoms: ['失眠', '多梦', '心烦'],
        notes: '既往体健'
      })
    })
    ```
    """
    global patient_id_counter
    
    now = datetime.now()
    
    new_patient = {
        "id": patient_id_counter,
        **patient.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    patients_db[patient_id_counter] = new_patient
    patient_id_counter += 1
    
    return new_patient


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: int):
    """获取患者详情"""
    patient = patients_db.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail={
            "code": 404,
            "message": f"患者ID {patient_id} 不存在",
            "data": None,
        })
    return patient


@router.get("", response_model=PaginatedResponse)
async def list_patients(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    gender: Optional[str] = Query(None, description="性别筛选"),
    min_age: Optional[int] = Query(None, ge=0, description="最小年龄"),
    max_age: Optional[int] = Query(None, le=150, description="最大年龄"),
):
    """
    患者列表 — 支持多条件筛选 + 分页 + 关键词搜索
    
    前端调用示例：
    ```ts
    const params = new URLSearchParams({
      page: '1',
      size: '10',
      keyword: '李',
      gender: '女'
    })
    const res = await fetch(`/api/v1/patients?${params}`)
    const data = await res.json()
    // data = { data: [...], total: 42, page: 1, size: 10, has_more: true }
    ```
    """
    # 1. 过滤
    filtered = list(patients_db.values())
    
    if keyword:
        filtered = [
            p for p in filtered
            if keyword in p["name"] or keyword in p["chief_complaint"]
        ]
    
    if gender:
        filtered = [p for p in filtered if p["gender"] == gender]
    
    if min_age is not None:
        filtered = [p for p in filtered if p["age"] >= min_age]
    
    if max_age is not None:
        filtered = [p for p in filtered if p["age"] <= max_age]
    
    # 2. 排序（按最新修改时间倒序）
    filtered.sort(key=lambda x: x["updated_at"], reverse=True)
    
    # 3. 分页
    total = len(filtered)
    start = (page - 1) * size
    end = start + size
    paginated = filtered[start:end]
    
    return PaginatedResponse(
        data=paginated,
        total=total,
        page=page,
        size=size,
        has_more=end < total,
    )


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: int, update_data: PatientUpdate):
    """
    更新患者（完整更新）
    
    注意：PatientUpdate 中所有字段都是 Optional，
    但 PUT 语义是"完整更新"，所以实际项目中可能需要区分 PUT/PATCH
    """
    existing = patients_db.get(patient_id)
    if not existing:
        raise HTTPException(status_code=404, detail="患者不存在")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for key, value in update_dict.items():
        existing[key] = value
    
    existing["updated_at"] = datetime.now()
    
    return existing


@router.patch("/{patient_id}", response_model=PatientResponse)
async def partial_update_patient(patient_id: int, update_data: PatientUpdate):
    """
    部分更新患者（只传要改的字段）
    
    前端调用示例：
    ```ts
    // 只更新主诉
    await fetch(`/api/v1/patients/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chief_complaint: '失眠改善，仍有头晕' })
    })
    ```
    """
    existing = patients_db.get(patient_id)
    if not existing:
        raise HTTPException(status_code=404, detail="患者不存在")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for key, value in update_dict.items():
        existing[key] = value
    
    existing["updated_at"] = datetime.now()
    
    return existing


@router.delete("/{patient_id}")
async def delete_patient(patient_id: int):
    """删除患者"""
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="患者不存在")
    
    del patients_db[patient_id]
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None,
    }


@router.get("/search/symptoms")
async def search_by_symptom(symptom: str = Query(..., min_length=1)):
    """
    按症状搜索患者（模糊匹配）
    
    前端调用示例：
    ```ts
    const res = await fetch('/api/v1/patients/search/symptoms?symptom=失眠')
    ```
    """
    results = []
    for patient in patients_db.values():
        if patient.get("symptoms"):
            if any(symptom in s for s in patient["symptoms"]):
                results.append(patient)
        elif symptom in patient.get("chief_complaint", ""):
            results.append(patient)
    
    return {"code": 200, "data": results, "total": len(results)}
```

### 3.3 注册路由到主应用

修改 `app/main.py`：

```python
from fastapi import FastAPI
from app.routers import patients

app = FastAPI(title="中医诊所管理系统", version="1.0.0")

# 注册路由模块
app.include_router(patients.router)

@app.get("/")
def root():
    return {"message": "API 服务正常运行", "version": "1.0.0"}
```

### 3.4 测试全部接口

```bash
# 启动服务
uvicorn app.main:app --reload --port 8000

# 打开 http://localhost:8000/docs
# 你会看到「患者管理」分组下的 7 个接口
```

---

## 第四章：依赖注入系统

### 4.1 什么是依赖注入？

```
前端类比：

React Context / Vue provide-inject：
// React
const ThemeContext = createContext('light');
function App() {
  return <ThemeContext.Provider value="dark">
    <Toolbar />
  </ThemeContext.Provider>;
}
function Toolbar() {
  const theme = useContext(ThemeContext);  // 注入依赖
}

FastAPI Depends()：
# Python
def get_db_session():  # 提供者
    session = create_session()
    try:
        yield session
    finally:
        session.close()

@app.get("/users")
def list_users(db = Depends(get_db_session)):  # 消费者
    return db.query(User).all()


共同点：
- 在"上层"提供依赖（数据库连接/用户认证/配置）
- 在"下层"通过声明的方式使用
- 解耦：使用者不需要知道依赖是怎么来的
```

### 4.2 实战：认证系统

创建 `app/deps.py`：

```python
from fastapi import Depends, HTTPException, Header
from typing import Optional
import jwt
import time
from datetime import datetime, timedelta

# 密钥（生产环境应该从环境变量读取）
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"


class TokenData:
    """Token 解析后的数据"""
    def __init__(self, user_id: int, username: str, role: str = "user"):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.exp = datetime.utcnow() + timedelta(hours=24)


def create_token(user_id: int, username: str, role: str = "user") -> str:
    """生成 JWT Token"""
    payload = {
        "sub": str(user_id),  # subject（用户标识）
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),  # issued at
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_token(token: str) -> dict:
    """验证 Token 并返回解码后的数据"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")


# ════════════════════════════════════════════
# 依赖注入函数
# ════════════════════════════════════════════

async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> dict:
    """
    获取当前登录用户 — 类似前端的路由守卫
    
    使用方式：
    @app.get("/protected")
    async def protected_route(user = Depends(get_current_user)):
        return {"user_id": user["sub"]}
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={"code": 401, "message": "未提供认证信息", "data": None},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="认证格式错误，应为 Bearer Token",
        )
    
    payload = verify_token(token)
    return payload


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    权限检查 — 只有管理员才能访问
    
    这是依赖嵌套的例子：
    get_admin_user 依赖于 get_current_user
    先验证是否登录，再验证是否有管理员权限
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail={"code": 403, "message": "需要管理员权限", "data": None},
        )
    return current_user


async def get_rate_limit_info(x_forwarded_for: Optional[str] = Header(None)) -> dict:
    """
    获取客户端 IP 用于限流
    
    前端类比：类似中间件提取 request.ip
    """
    client_ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else "unknown"
    return {"ip": client_ip, "timestamp": time.time()}
```

### 4.3 使用依赖注入保护接口

在 `app/routers/patients.py` 中添加认证：

```python
from fastapi import APIRouter, HTTPException, Query, Depends
from app.deps import get_current_user, get_admin_user
from app.models import PatientCreate, PatientUpdate, PatientResponse, PaginatedResponse

router = APIRouter(prefix="/api/v1/patients", tags=["患者管理"])


# 公开接口：不需要登录
@router.get("/public/list")
async def public_patient_list(page: int = Query(1)):
    """公开的患者列表（无需认证）"""
    ...


# 需要登录的接口
@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(
    patient: PatientCreate,
    current_user: dict = Depends(get_current_user),  # ← 注入当前用户
):
    """新建患者 — 需要登录"""
    print(f"操作人: {current_user['username']} (角色: {current_user['role']})")
    ...


# 需要管理员权限的接口
@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    admin_user: dict = Depends(get_admin_user),  # ← 注入管理员用户
):
    """删除患者 — 仅管理员"""
    print(f"管理员操作: {admin_user['username']}")
    ...
```

### 4.4 登录接口

在 `app/routers/auth.py` 中：

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.deps import create_token

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# 模拟用户数据库
USERS_DB = {
    "admin": {"password": "admin123", "role": "admin", "id": 1},
    "doctor": {"password": "doctor123", "role": "doctor", "id": 2},
    "assistant": {"password": "assist123", "role": "assistant", "id": 3},
}


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """
    用户登录 — 获取 Token
    
    前端调用示例：
    ```ts
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'admin', password: 'admin123' })
    })
    const { access_token } = await res.json()
    localStorage.setItem('token', access_token)
    
    // 后续请求带上 token
    fetch('/api/v1/patients', {
      headers: { 'Authorization': `Bearer ${access_token}` }
    })
    ```
    """
    user = USERS_DB.get(login_data.username)
    
    if not user or user["password"] != login_data.password:
        raise HTTPException(
            status_code=401,
            detail={"code": 401, "message": "用户名或密码错误", "data": None},
        )
    
    token = create_token(
        user_id=user["id"],
        username=login_data.username,
        role=user["role"],
    )
    
    return LoginResponse(
        access_token=token,
        user={
            "id": user["id"],
            "username": login_data.username,
            "role": user["role"],
        },
    )


@router.post("/logout")
async def logout():
    """登出（前端删除 token 即可）"""
    return {"code": 200, "message": "已登出"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "code": 200,
        "data": {
            "user_id": current_user["sub"],
            "username": current_user["username"],
            "role": current_user["role"],
        },
    }
```

---

## 第五章：中间件与全局处理

### 5.1 什么是中间件？

```
请求生命周期：

Client Request
    ↓
[Middleware 1]  ← 所有请求都会经过这里（类似 Koa/Express middleware）
[Middleware 2]
    ↓
[Router]        ← 匹配路由，执行处理函数
    ↓
[Middleware 2]  ← 响应也会经过这里（后置处理）
[Middleware 1]
    ↓
Client Response


常见用途：
✅ 日志记录（记录每个请求的信息）
✅ CORS 跨域处理
✅ 请求耗时统计
✅ 错误捕获
✅ 请求/响应转换
```

### 5.2 实现常用中间件

在 `app/middleware.py` 中：

```python
import time
import json
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """请求计时中间件 — 统计每个接口的响应时间"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 处理请求
        response = await call_next(request)
        
        # 计算耗时
        process_time = (time.time() - start_time) * 1000
        
        # 添加自定义响应头（方便前端调试）
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        
        # 记录日志
        logger.info(
            f"{request.method} {request.url.path} "
            f"— {response.status_code} — {process_time:.2f}ms"
        )
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """详细日志中间件 — 记录请求和响应的详细信息"""
    
    async def dispatch(self, request: Request, call_next):
        # 记录请求信息
        request_log = {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", ""),
        }
        
        # 如果是 POST/PUT/PATCH，尝试记录请求体（不记录敏感字段）
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                if body:
                    try:
                        body_json = json.loads(body)
                        # 脱敏
                        if "password" in body_json:
                            body_json["password"] = "***"
                        if "phone" in body_json:
                            body_json["phone"] = body_json["phone"][:3] + "****" + body_json["phone][-4:]
                        request_log["body"] = body_json
                    except json.JSONDecodeError:
                        request_log["body_size"] = len(body)
                
                # 重要：需要重新设置 body，因为已经被消费了
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
            except Exception:
                pass
        
        logger.info(f"REQUEST: {json.dumps(request_log, ensure_ascii=False)}")
        
        # 处理请求
        response = await call_next(request)
        
        logger.info(
            f"RESPONSE: {request.method} {request.url.path} "
            f"— Status: {response.status_code}"
        )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """全局错误处理中间件 — 捕获未处理的异常"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            # HTTPException 是预期的异常，正常返回
            raise e
        except Exception as e:
            # 未预期的异常，记录日志并返回友好提示
            logger.error(
                f"未处理的异常: {request.method} {request.url.path}",
                exc_info=True,
            )
            
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": "服务器内部错误，请稍后重试",
                    "data": None,
                    "request_id": getattr(request, "state", {}).get("request_id", ""),
                },
            )


# ════════════════════════════════════════════
# 注册中间件的便捷函数
# ════════════════════════════════════════════

def setup_middlewares(app):
    """一次性注册所有中间件"""
    
    # 1. CORS（必须最先注册）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",   # React 开发服务器
            "http://localhost:5173",   # Vite 开发服务器
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time"],
    )
    
    # 2. 请求计时
    app.add_middleware(TimingMiddleware)
    
    # 3. 详细日志
    app.add_middleware(LoggingMiddleware)
    
    # 4. 全局错误处理（最后注册，确保最外层捕获）
    app.add_middleware(ErrorHandlingMiddleware)
```

### 5.3 在主应用中启用中间件

修改 `app/main.py`：

```python
from fastapi import FastAPI
from app.routers import patients, auth
from app.middleware import setup_middlewares

app = FastAPI(
    title="中医诊所管理系统",
    version="1.0.0",
    description="基于 FastAPI 构建的诊所管理后台 API",
)

# 注册中间件
setup_middlewares(app)

# 注册路由
app.include_router(patients.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "API 服务正常运行", "version": "1.0.0"}
```

---

## 第六章：SSE 流式响应（AI 对话必备）

### 6.1 为什么需要 SSE？

```
普通请求 vs SSE 流式：

普通请求（你熟悉的）：
Client ──发送请求──→ Server
Client ←──等待...──── Server（处理中...可能要30秒）
Client ←──完整响应─── Server（一次性返回所有内容）

问题：用户等待期间看到的是加载动画，体验差

SSE 流式（ChatGPT 用的就是这种）：
Client ──发送请求──→ Server
Client ←─chunk 1───── Server（"你好"）
Client ←─chunk 2───── Server（"，我是"）
Client ←─chunk 3───── Server（"AI助手"）
...
Client ←─[DONE]────── Server（结束）

优势：文字逐渐出现，用户体验好
适用：AI 对话、实时日志、进度推送
```

### 6.2 实现 AI 对话的 SSE 接口

创建 `app/routers/chat.py`：

```python
import json
import asyncio
import random
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from app.deps import get_current_user

router = APIRouter(prefix="/api/v1/chat", tags=["AI 对话"])


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None
    stream: bool = Field(default=True, description="是否流式输出")


async def mock_ai_response(message: str):
    """
    模拟 AI 流式响应
    
    TODO: 替换为真实的 LLM API 调用（OpenAI / DeepSeek）
    """
    responses = [
        f"关于您提到的「{message[:20]}」这个问题，让我从中医角度来分析一下。\n\n",
        "首先，我们需要了解您的具体情况。请问您目前的症状持续多久了？\n\n",
        "从中医辨证的角度来看，这种情况可能与以下几个方面有关：\n",
        "1. 气血运行是否通畅\n",
        "2. 脏腑功能是否协调\n",
        "3. 情绪状态对身体的影响\n\n",
        "建议您到正规医疗机构进行专业诊断。\n\n",
        "---\n*以上内容仅供参考，不构成医疗建议*",
    ]
    
    for part in responses:
        yield part
        await asyncio.sleep(0.15)  # 模拟网络延迟


@router.post("")
async def chat_non_stream(
    request: ChatRequest,
    user: dict = Depends(get_current_user),
):
    """
    非流式对话（一次性返回）
    
    适用场景：不需要实时显示的场景（如后台任务）
    """
    full_response = ""
    async for chunk in mock_ai_response(request.message):
        full_response += chunk
    
    return {
        "code": 200,
        "data": {
            "reply": full_response,
            "model": "tcm-assistant-v1",
            "tokens_used": len(full_response),
        },
    }


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    user: dict = Depends(get_current_user),
):
    """
    SSE 流式对话 — AI 对话的核心接口
    
    前端接收代码（你已经写过类似的！）：
    ```ts
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMessage, stream: true })
    })
    
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const text = decoder.decode(value)
      const lines = text.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') break
          
          const parsed = JSON.parse(data)
          onChunk(parsed.content)  // 逐字显示
        }
      }
    }
    ```
    """
    
    async def event_generator():
        """SSE 事件生成器"""
        
        # 发送初始连接确认
        yield f"data: {json.dumps({'type': 'connected'}, ensure_ascii=False)}\n\n"
        
        try:
            async for chunk in mock_ai_response(request.message):
                # SSE 格式：每条消息以 "data: " 开头，以 "\n\n" 结尾
                payload = {
                    "type": "chunk",
                    "content": chunk,
                    "conversation_id": request.conversation_id,
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)  # 让出控制权
            
            # 发送结束标记
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_payload = {
                "type": "error",
                "content": f"生成过程中出错: {str(e)}",
            }
            yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁止 Nginx 缓冲
            "Access-Control-Allow-Origin": "*",
        },
    )
```

### 6.3 测试 SSE 接口

```bash
# 方式1：用 curl 测试（能看到流式输出）
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token-here" \
  -d '{"message": "我最近总是睡不着怎么办", "stream": true}'

# 你会看到逐行输出的内容：
# data: {"type":"connected"}
#
# data: {"type":"chunk","content":"关于您提到的..."}
#
# data: {"type":"chunk","content":"首先，我们..."}
#
# ...
# data: [DONE]


# 方式2：用浏览器 JavaScript 控制台测试
# 打开 http://localhost:8000/docs，用 Swagger 测试 stream 接口
```

---

## 第七章：错误处理体系

### 7.1 分层错误处理策略

```
错误处理的层次：

Layer 1: Pydantic 校验（自动）
→ 数据格式不对 → 自动返回 422 Unprocessable Entity
→ 你不需要写任何代码

Layer 2: 业务逻辑异常
→ 用户不存在、权限不足、数据冲突等
→ 手动抛出 HTTPException

Layer 3: 全局异常处理器
→ 捕获所有未处理的异常
→ 统一返回格式，隐藏内部错误细节

Layer 4: 中间件兜底
→ 最后的安全网
→ 确保永远不会返回 500 的原始堆栈给前端
```

### 7.2 实现统一错误处理

创建 `app/exceptions.py`：

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging
import traceback

logger = logging.getLogger(__name__)


class BusinessException(Exception):
    """
    自定义业务异常 — 用于业务逻辑中的可预期错误
    
    使用方式：
    raise BusinessException("余额不足", code=40001)
    """
    def __init__(self, message: str, code: int = 400, data=None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)


class NotFoundError(BusinessException):
    """资源不存在"""
    def __init__(self, resource_name: str = "资源"):
        super().__init__(f"{resource_name}不存在", code=404)


class UnauthorizedError(BusinessException):
    """未授权"""
    def __init__(self, message: str = "请先登录"):
        super().__init__(message, code=401)


class ForbiddenError(BusinessException):
    """无权限"""
    def __init__(self, message: str = "没有操作权限"):
        super().__init__(message, code=403)


class ConflictError(BusinessException):
    """资源冲突（如重复创建）"""
    def __init__(self, message: str = "资源已存在"):
        super().__init__(message, code=409)


def format_error_response(
    status_code: int,
    message: str,
    error_type: str = "error",
    details: list = None,
    request_id: str = None,
) -> dict:
    """统一的错误响应格式"""
    response = {
        "code": status_code,
        "message": message,
        "error_type": error_type,
        "data": None,
    }
    if details:
        response["details"] = details
    if request_id:
        response["request_id"] = request_id
    return response


def register_exception_handlers(app: FastAPI):
    """注册所有异常处理器"""
    
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        """处理自定义业务异常"""
        logger.warning(
            f"业务异常 [{exc.code}]: {exc.message} | "
            f"{request.method} {request.url.path}"
        )
        return JSONResponse(
            status_code=exc.code if exc.code >= 400 else 400,
            content=format_error_response(
                status_code=exc.code,
                message=exc.message,
                error_type="business_error",
                data=exc.data,
            ),
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理 HTTP 标准异常"""
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(
                status_code=exc.status_code,
                message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
                error_type="http_error",
            ),
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """处理请求参数校验失败（Pydantic 校验不通过）"""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        
        logger.warning(f"参数校验失败: {errors}")
        
        return JSONResponse(
            status_code=422,
            content=format_error_response(
                status_code=422,
                message="请求参数校验失败",
                error_type="validation_error",
                details=errors,
            ),
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """兜底：处理所有未预期异常"""
        logger.error(
            f"未预期异常: {request.method} {request.url.path}\n"
            f"{traceback.format_exc()}",
            exc_info=True,
        )
        
        return JSONResponse(
            status_code=500,
            content=format_error_response(
                status_code=500,
                message="服务器内部错误，请稍后重试",
                error_type="internal_error",
                request_id=getattr(request.state, "request_id", None),
            ),
        )
```

### 7.3 在主应用中注册

修改 `app/main.py`：

```python
from fastapi import FastAPI
from app.routers import patients, auth, chat
from app.middleware import setup_middlewares
from app.exceptions import register_exception_handlers

app = FastAPI(
    title="中医诊所管理系统",
    version="1.0.0",
)

# 注册异常处理器
register_exception_handlers(app)

# 注册中间件
setup_middlewares(app)

# 注册路由
app.include_router(patients.router)
app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {"message": "API 服务正常运行"}
```

### 7.4 使用自定义异常

```python
from app.exceptions import NotFoundError, UnauthorizedError, ForbiddenError

# 在路由中使用
@router.get("/patients/{patient_id}")
async def get_patient(patient_id: int):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise NotFoundError("患者")  # → 404 {"code":404,"message":"患者不存在"}
    return patient


@router.post("/patients")
async def create_patient(data: PatientCreate, user = Depends(get_current_user)):
    if user["role"] == "patient":
        raise ForbiddenError("患者不能创建患者记录")  # → 403
    ...
```

---

## 第八章：综合练习项目

### 8.1 项目需求

把上面学到的所有知识整合起来，实现一个**简化版的中医诊所 AI 助手 API**：

```
功能清单：
✅ 用户认证（登录/登出/获取当前用户）
✅ 患者 CRUD（创建/查看列表/查看详情/更新/删除/按症状搜索）
✅ AI 对话（普通模式 + SSE 流式模式）
✅ 统一错误处理
✅ 请求日志 + 耗时统计
✅ CORS 跨域支持
✅ 自动 API 文档
```

### 8.2 最终目录结构

```
my_api/
├── app/
│   ├── __init__.py
│   ├── main.py              # 应用入口 + 注册所有组件
│   ├── models.py            # Pydantic 数据模型
│   ├── deps.py              # 依赖注入（认证/限流等）
│   ├── exceptions.py        # 自定义异常 + 异常处理器
│   ├── middleware.py         # 中间件（日志/CORS/计时/错误）
│   └── routers/
│       ├── __init__.py
│       ├── auth.py          # 认证接口
│       ├── patients.py      # 患者管理接口
│       └── chat.py          # AI 对话接口
├── requirements.txt
└── run.sh                   # 启动脚本
```

### 8.3 requirements.txt

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic[email]>=2.5.0
pydantic-settings>=2.1.0
python-jwt[crypto]>=2.8.0
python-multipart>=0.0.6
```

### 8.4 练习要求

**基础练习（必做）：**

1. 把前面章节的所有代码整合到一个项目中
2. 确保所有接口都能在 Swagger UI 中正常测试
3. 测试各种异常情况，验证错误处理是否正确
4. 用 curl 或前端代码测试 SSE 流式输出

**进阶练习（选做）：**

5. 给患者列表接口加上缓存（用内存字典模拟 Redis）
6. 实现简单的请求频率限制（每个 IP 每分钟最多 60 次）
7. 给 `/api/v1/chat/stream` 加上真实的 OpenAI API 调用（替换 mock_ai_response）
8. 编写 5 个单元测试，覆盖核心逻辑

---

## 验收标准清单

学完这份教程后，你应该能够：

### ✅ 基础能力（必须全部达标）

- [ ] 能独立创建 FastAPI 项目，5 分钟内跑通 `Hello World`
- [ ] 能用 Pydantic 定义请求/响应模型，包含校验规则
- [ ] 能写出完整的 CRUD 接口（POST/GET/PUT/PATCH/DELETE）
- [ ] 能实现分页查询 + 多条件筛选
- [ ] 能用 `Depends()` 实现依赖注入（认证/权限）
- [ ] 能写出 SSE 流式响应接口
- [ ] 能配置 CORS、日志中间件
- [ ] 能实现分层错误处理（业务异常/参数校验/全局兜底）

### ✅ 进阶能力（尽量达成）

- [ ] 能解释清楚中间件的执行顺序
- [ ] 能设计合理的 API 响应格式规范
- [ ] 能根据业务需求选择合适的 HTTP 状态码
- [ ] 能在 Swagger 文档中清晰描述接口用途

### ❓ 自测问题

如果你能回答下面这些问题，说明真的掌握了：

1. **`Depends()` 和直接在函数里写代码有什么区别？什么时候用哪个？**
   
2. **PUT 和 PATCH 有什么语义区别？在你的项目中怎么体现的？**
   
3. **如果一个请求同时触发了中间件、依赖注入、路由处理函数、异常处理器，它们的执行顺序是什么？**
   
4. **为什么 SSE 要设置 `X-Accel-Buffering: no` 和 `Cache-Control: no-cache`？**
   
5. **Pydantic 的 `Field(default=...)` 和 `Field(default_factory=...)` 有什么区别？**

---

## 常见坑点（新手容易犯的错误）

### 坑1：忘记安装依赖

```bash
# 错误：ImportError: No module named 'email_validator'
# 原因：用了 EmailStr 但没装 email-validator

# 解决：
pip install "pydantic[email]"
```

### 坑2：异步函数没加 async/await

```python
# 错误：阻塞事件循环
def slow_operation():
    time.sleep(10)  # 这会卡住整个服务器！

# 正确：
async def slow_operation():
    await asyncio.sleep(10)  # 不阻塞其他请求
```

### 坑3：SSE 被 Nginx 缓冲

```python
# 问题：前端收不到 SSE 数据，而是等到全部完成后一次性收到
# 原因：Nginx 默认会缓冲响应

# 解决：添加响应头
headers={
    "X-Accel-Buffering": "no",
    "Cache-Control": "no-cache",
}
```

### 坑4：CORS 配置错误

```python
# 错误：前端仍然报跨域错误
# 原因：allow_origins 不能写 "*" 当 allow_credentials=True 时

# 解决：
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 写具体的前端地址
    allow_credentials=True,
)
```

### 坑5：Pydantic v1 vs v2 语法混淆

```python
# Pydantic v1（旧）：
class User(BaseModel):
    name: str
    
    class Config:
        orm_mode = True

# Pydantic v2（新，你现在用的）：
class User(BaseModel):
    name: str
    
    model_config = ConfigDict(from_attributes=True)
    # 或者用 class Config: from_attributes = True
```

---

> **下一步**：学完 FastAPI 后，继续学习 [03-SQLAlchemy+PostgreSQL实战.md](./03-SQLAlchemy+PostgreSQL实战.md)，把数据持久化能力补齐。
