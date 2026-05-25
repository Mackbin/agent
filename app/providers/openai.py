"""
OpenAI Provider 实现
"""
import httpx
from typing import AsyncGenerator, Dict, Any, List, Optional
import json
import structlog

from app.providers.base import BaseProvider, ChatMessage, ChatCompletion, ChatChunk
from app.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI Provider"""
    
    name = "openai"
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletion:
        """OpenAI 非流式聊天"""
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # 添加额外参数
        payload.update(kwargs)
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
        
        latency = int((time.time() - start_time) * 1000)
        
        logger.info(
            "OpenAI 请求完成",
            model=model,
            latency_ms=latency,
            tokens=data.get("usage", {})
        )
        
        return ChatCompletion(
            id=data["id"],
            model=data["model"],
            created=data["created"],
            choices=data["choices"],
            usage=data.get("usage", {}),
            provider=self.name
        )
    
    async def chat_completion_stream(
        self,
        messages: List[ChatMessage],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[ChatChunk, None]:
        """OpenAI 流式聊天"""
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
            "temperature": temperature,
            "stream": True,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        payload.update(kwargs)
        
        start_time = time.time()
        chunk_id = self._generate_id()
        created = self._get_current_timestamp()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=self.headers, json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            if data.get("choices") and len(data["choices"]) > 0:
                                chunk = ChatChunk(
                                    id=data.get("id", chunk_id),
                                    model=data.get("model", model),
                                    created=created,
                                    choices=data["choices"],
                                    provider=self.name
                                )
                                yield chunk
                        except json.JSONDecodeError:
                            continue
        
        latency = int((time.time() - start_time) * 1000)
        logger.info("OpenAI 流式请求完成", model=model, latency_ms=latency)
