"""
聊天 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json
import time
import structlog

from app.database import get_db
from app.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    StreamChunk,
)
from app.auth import get_api_key_user
from app.models import User
from app.services.ai_router import get_ai_router, AIRouterService
from app.services.conversation_service import get_conversation_service, ConversationService
from app.providers.base import ChatMessage
from app.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["聊天"])


@router.post("/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    req: Request,
    current_user: User = Depends(get_api_key_user),
    db: AsyncSession = Depends(get_db),
    ai_router: AIRouterService = Depends(get_ai_router),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    聊天完成接口
    
    支持流式和非流式两种模式
    """
    start_time = time.time()
    
    # 获取或创建会话
    conversation_id = request.conversation_id
    if conversation_id:
        conversation = await conversation_service.get_conversation(
            db, conversation_id, str(current_user.id)
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
    else:
        # 创建新会话
        conversation = await conversation_service.create_conversation(
            db,
            str(current_user.id),
            model=request.model or "gpt-3.5-turbo"
        )
        conversation_id = str(conversation.id)
    
    # 保存用户消息
    user_message = request.messages[-1] if request.messages else None
    if user_message:
        await conversation_service.add_message(
            db,
            conversation_id,
            role=user_message.role,
            content=user_message.content
        )
    
    # 路由到最优模型
    model_config, provider = await ai_router.route_request(
        db,
        model_name=request.model,
        user_preferences={"user_id": str(current_user.id)}
    )
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="暂无可用模型服务"
        )
    
    # 构建上下文
    context_messages = [
        ChatMessage(role=msg.role, content=msg.content)
        for msg in request.messages
    ]
    
    try:
        if request.stream:
            # 流式响应
            return StreamingResponse(
                stream_generator(
                    provider,
                    context_messages,
                    model_config.model_name,
                    request.temperature,
                    request.max_tokens,
                    db,
                    conversation_id,
                    str(current_user.id)
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # 非流式响应
            response = await provider.chat_completion(
                messages=context_messages,
                model=model_config.model_name,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # 记录请求结果
            ai_router.record_request(
                provider.name,
                success=True,
                latency_ms=latency_ms
            )
            
            # 保存助手消息
            assistant_content = response.choices[0]["message"]["content"]
            await conversation_service.add_message(
                db,
                conversation_id,
                role="assistant",
                content=assistant_content,
                tokens=response.usage.get("total_tokens", 0),
                model=response.model,
                provider=response.provider,
                latency_ms=latency_ms
            )
            
            # 返回响应
            return ChatCompletionResponse(
                id=response.id,
                created=response.created,
                model=response.model,
                choices=response.choices,
                usage=response.usage
            )
    
    except Exception as e:
        logger.error("聊天请求失败", error=str(e))
        
        # 记录失败
        ai_router.record_request(
            provider.name,
            success=False,
            latency_ms=int((time.time() - start_time) * 1000)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"请求失败：{str(e)}"
        )


async def stream_generator(
    provider,
    messages,
    model: str,
    temperature: float,
    max_tokens: Optional[int],
    db: AsyncSession,
    conversation_id: str,
    user_id: str
):
    """SSE 流式生成器"""
    start_time = time.time()
    full_content = ""
    chunk_count = 0
    
    try:
        async for chunk in provider.chat_completion_stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            # 转换为 SSE 格式
            chunk_data = {
                "id": chunk.id,
                "object": "chat.completion.chunk",
                "created": chunk.created,
                "model": chunk.model,
                "choices": chunk.choices
            }
            
            yield f"data: {json.dumps(chunk_data)}\n\n"
            
            # 累积内容
            for choice in chunk.choices:
                if "delta" in choice and "content" in choice["delta"]:
                    full_content += choice["delta"]["content"]
            
            chunk_count += 1
        
        # 发送结束标记
        yield "data: [DONE]\n\n"
        
        # 计算延迟
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 估算 Token 数（简单估算）
        estimated_tokens = len(full_content) // 4
        
        # 异步保存消息（不阻塞流式响应）
        try:
            from app.services.conversation_service import ConversationService
            conversation_service = ConversationService()
            
            await conversation_service.add_message(
                db,
                conversation_id,
                role="assistant",
                content=full_content,
                tokens=estimated_tokens,
                model=model,
                provider=provider.name,
                latency_ms=latency_ms
            )
            
            # 记录成功
            from app.services.ai_router import get_ai_router
            ai_router = get_ai_router()
            ai_router.record_request(
                provider.name,
                success=True,
                latency_ms=latency_ms
            )
        except Exception as e:
            logger.error("保存消息失败", error=str(e))
    
    except Exception as e:
        logger.error("流式生成失败", error=str(e))
        
        # 发送错误
        error_data = {
            "error": {
                "message": str(e),
                "type": "server_error"
            }
        }
        yield f"data: {json.dumps(error_data)}\n\n"
        
        # 记录失败
        from app.services.ai_router import get_ai_router
        ai_router = get_ai_router()
        ai_router.record_request(
            provider.name,
            success=False,
            latency_ms=int((time.time() - start_time) * 1000)
        )
