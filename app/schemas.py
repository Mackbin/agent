"""
Pydantic 模式定义
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import IntEnum


class UserStatus(IntEnum):
    ACTIVE = 1
    INACTIVE = 0


class UserCreate(BaseModel):
    """用户创建请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: str
    username: str
    email: str
    status: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class APIKeyCreate(BaseModel):
    """API Key 创建请求"""
    name: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    rate_limit: Optional[int] = None
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    """API Key 响应"""
    id: str
    name: Optional[str]
    key_prefix: str  # 只显示前缀
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT Token 响应"""
    access_token: str
    token_type: str = "bearer"


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str


class ChatCompletionRequest(BaseModel):
    """聊天完成请求"""
    model: Optional[str] = None
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = None
    stream: bool = False
    conversation_id: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    """聊天完成响应"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


class StreamChunk(BaseModel):
    """流式响应块"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]


class ConversationResponse(BaseModel):
    """会话响应"""
    id: str
    title: Optional[str]
    model: str
    message_count: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    name: str
    provider: str
    is_active: bool
    cost_per_1k_tokens: Optional[float]
    max_tokens: Optional[int]
    context_window: Optional[int]


class UsageStatistics(BaseModel):
    """使用统计"""
    total_requests: int
    total_tokens: int
    total_cost: float
    requests_by_model: Dict[str, int]
    tokens_by_model: Dict[str, int]


class HealthCheck(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    timestamp: datetime
