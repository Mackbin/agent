"""
Claude Provider 实现
"""
import httpx
from typing import AsyncGenerator, Dict, Any, List, Optional
import json
import structlog

from app.providers.base import BaseProvider, ChatMessage, ChatCompletion, ChatChunk
from app.logging import get_logger

logger = get_logger(__name__)


class ClaudeProvider(BaseProvider):
    """Claude Provider"""
    
    name = "claude"
    
    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com/v1", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    def _convert_messages(self, messages: List[ChatMessage]) -> tuple:
        """转换消息格式为 Claude 格式"""
        system_messages = []
        claude_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_messages.append(msg.content)
            elif msg.role == "user":
                claude_messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                claude_messages.append({"role": "assistant", "content": msg.content})
        
        system_prompt = "\n".join(system_messages) if system_messages else None
        return system_prompt, claude_messages
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletion:
        """Claude 非流式聊天"""
        url = f"{self.base_url}/messages"
        
        system_prompt, claude_messages = self._convert_messages(messages)
        
        payload = {
            "model": model,
            "messages": claude_messages,
            "max_tokens": max_tokens or 1024,
            "temperature": temperature,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        # 添加额外参数
        payload.update(kwargs)
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
        
        latency = int((time.time() - start_time) * 1000)
        
        # 转换为 OpenAI 兼容格式
        choices = [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": data["content"][0]["text"] if data["content"] else ""
                },
                "finish_reason": data.get("stop_reason", "stop")
            }
        ]
        
        usage = {
            "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
            "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
            "total_tokens": (
                data.get("usage", {}).get("input_tokens", 0) +
                data.get("usage", {}).get("output_tokens", 0)
            )
        }
        
        logger.info(
            "Claude 请求完成",
            model=model,
            latency_ms=latency,
            tokens=usage
        )
        
        return ChatCompletion(
            id=data.get("id", self._generate_id()),
            model=model,
            created=self._get_current_timestamp(),
            choices=choices,
            usage=usage,
            provider=self.name
        )
    
    async def chat_completion_stream(
        self,
        messages: List[ChatMessage],
        model: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[ChatChunk, None]:
        """Claude 流式聊天"""
        url = f"{self.base_url}/messages"
        
        system_prompt, claude_messages = self._convert_messages(messages)
        
        payload = {
            "model": model,
            "messages": claude_messages,
            "max_tokens": max_tokens or 1024,
            "temperature": temperature,
            "stream": True,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
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
                        
                        try:
                            event_data = json.loads(data_str)
                            event_type = event_data.get("type")
                            
                            if event_type == "content_block_delta":
                                delta = event_data.get("delta", {})
                                text = delta.get("text", "")
                                
                                if text:
                                    chunk = ChatChunk(
                                        id=chunk_id,
                                        model=model,
                                        created=created,
                                        choices=[
                                            {
                                                "index": 0,
                                                "delta": {
                                                    "role": "assistant",
                                                    "content": text
                                                },
                                                "finish_reason": None
                                            }
                                        ],
                                        provider=self.name
                                    )
                                    yield chunk
                            
                            elif event_type == "message_stop":
                                chunk = ChatChunk(
                                    id=chunk_id,
                                    model=model,
                                    created=created,
                                    choices=[
                                        {
                                            "index": 0,
                                            "delta": {},
                                            "finish_reason": "stop"
                                        }
                                    ],
                                    provider=self.name
                                )
                                yield chunk
                                break
                                
                        except json.JSONDecodeError:
                            continue
        
        latency = int((time.time() - start_time) * 1000)
        logger.info("Claude 流式请求完成", model=model, latency_ms=latency)
