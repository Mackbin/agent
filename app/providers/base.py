"""
Provider 基类定义
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional
from dataclasses import dataclass
import time


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str
    content: str
    name: Optional[str] = None


@dataclass
class ChatCompletion:
    """聊天完成响应"""
    id: str
    model: str
    created: int
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]
    provider: str


@dataclass
class ChatChunk:
    """聊天流式块"""
    id: str
    model: str
    created: int
    choices: List[Dict[str, Any]]
    provider: str


class BaseProvider(ABC):
    """AI Provider 基类"""
    
    name: str = "base"
    
    def __init__(self, api_key: str, base_url: str, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletion:
        """非流式聊天完成"""
        pass
    
    @abstractmethod
    async def chat_completion_stream(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[ChatChunk, None]:
        """流式聊天完成"""
        pass
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 简单测试连接
            await self.chat_completion(
                messages=[ChatMessage(role="user", content="Hi")],
                model=model,
                max_tokens=1
            )
            return True
        except Exception:
            return False
    
    def _get_current_timestamp(self) -> int:
        """获取当前时间戳"""
        return int(time.time())
    
    def _generate_id(self, prefix: str = "chatcmpl") -> str:
        """生成唯一 ID"""
        import uuid
        return f"{prefix}-{uuid.uuid4().hex[:8]}"
