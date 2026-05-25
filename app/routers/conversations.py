"""
对话管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from app.database import get_db
from app.schemas import ConversationResponse
from app.auth import get_api_key_user
from app.models import User, Conversation, Message
from app.services.conversation_service import ConversationService
from app.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/conversations", tags=["对话管理"])


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_api_key_user),
    db: AsyncSession = Depends(get_db)
):
    """列出当前用户的会话"""
    conversations = await ConversationService.list_conversations(
        db,
        str(current_user.id),
        limit=limit,
        offset=offset
    )
    
    return [
        ConversationResponse(
            id=str(conv.id),
            title=conv.title,
            model=conv.model,
            message_count=conv.message_count,
            total_tokens=conv.total_tokens,
            created_at=conv.created_at,
            updated_at=conv.updated_at
        )
        for conv in conversations
    ]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_api_key_user),
    db: AsyncSession = Depends(get_db)
):
    """获取会话详情"""
    conversation = await ConversationService.get_conversation(
        db,
        conversation_id,
        str(current_user.id)
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    return ConversationResponse(
        id=str(conversation.id),
        title=conversation.title,
        model=conversation.model,
        message_count=conversation.message_count,
        total_tokens=conversation.total_tokens,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_api_key_user),
    db: AsyncSession = Depends(get_db)
):
    """删除会话"""
    success = await ConversationService.delete_conversation(
        db,
        conversation_id,
        str(current_user.id)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_api_key_user),
    db: AsyncSession = Depends(get_db)
):
    """获取会话消息列表"""
    # 验证会话归属
    conversation = await ConversationService.get_conversation(
        db,
        conversation_id,
        str(current_user.id)
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    messages = await ConversationService.get_messages(
        db,
        conversation_id,
        limit=limit,
        offset=offset
    )
    
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "tokens": msg.tokens,
                "model": msg.model,
                "provider": msg.provider,
                "created_at": msg.created_at
            }
            for msg in messages
        ],
        "total": conversation.message_count,
        "limit": limit,
        "offset": offset
    }
