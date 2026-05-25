"""
对话管理服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from app.models import Conversation, Message, User
from app.providers.base import ChatMessage
from app.schemas import ChatMessage as ChatMessageSchema
from app.logging import get_logger

logger = get_logger(__name__)


class ConversationService:
    """对话管理服务"""
    
    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user_id: str,
        model: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """创建会话"""
        conversation = Conversation(
            user_id=user_id,
            title=title,
            model=model,
            status=1,
            message_count=0,
            total_tokens=0,
            metadata=metadata or {}
        )
        
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        logger.info(
            "会话创建成功",
            conversation_id=str(conversation.id),
            user_id=user_id,
            model=model
        )
        
        return conversation
    
    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Conversation]:
        """获取会话"""
        query = select(Conversation).where(Conversation.id == conversation_id)
        
        if user_id:
            query = query.where(Conversation.user_id == user_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Conversation]:
        """列出用户会话"""
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """删除会话"""
        conversation = await ConversationService.get_conversation(
            db, conversation_id, user_id
        )
        
        if not conversation:
            return False
        
        await db.delete(conversation)
        await db.commit()
        
        logger.info(
            "会话已删除",
            conversation_id=conversation_id
        )
        
        return True
    
    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: str,
        role: str,
        content: str,
        tokens: Optional[int] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        latency_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """添加消息"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens=tokens,
            model=model,
            provider=provider,
            latency_ms=latency_ms,
            metadata=metadata or {}
        )
        
        db.add(message)
        
        # 更新会话统计
        conversation = await ConversationService.get_conversation(db, conversation_id)
        if conversation:
            conversation.message_count += 1
            conversation.total_tokens += tokens or 0
            conversation.updated_at = datetime.utcnow()
            
            # 自动生成标题
            if not conversation.title and role == "user":
                conversation.title = content[:50] + ("..." if len(content) > 50 else "")
        
        await db.commit()
        await db.refresh(message)
        
        return message
    
    @staticmethod
    async def get_messages(
        db: AsyncSession,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """获取会话消息"""
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    @staticmethod
    async def build_context(
        db: AsyncSession,
        conversation_id: str,
        max_tokens: Optional[int] = None
    ) -> List[ChatMessage]:
        """构建对话上下文"""
        messages = await ConversationService.get_messages(db, conversation_id)
        
        context = []
        total_tokens = 0
        
        # 从后往前遍历，优先保留最近的消息
        for msg in reversed(messages):
            if max_tokens and total_tokens >= max_tokens:
                break
            
            chat_msg = ChatMessage(
                role=msg.role,
                content=msg.content
            )
            context.insert(0, chat_msg)
            total_tokens += msg.tokens or 0
        
        return context
    
    @staticmethod
    async def get_user_conversation_stats(
        db: AsyncSession,
        user_id: str
    ) -> Dict[str, Any]:
        """获取用户会话统计"""
        # 总会话数
        total_result = await db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.user_id == user_id)
        )
        total_conversations = total_result.scalar() or 0
        
        # 总消息数
        messages_result = await db.execute(
            select(func.sum(Conversation.message_count))
            .where(Conversation.user_id == user_id)
        )
        total_messages = messages_result.scalar() or 0
        
        # 总 Token 数
        tokens_result = await db.execute(
            select(func.sum(Conversation.total_tokens))
            .where(Conversation.user_id == user_id)
        )
        total_tokens = tokens_result.scalar() or 0
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_tokens": total_tokens
        }


# 全局对话服务实例
conversation_service = ConversationService()


def get_conversation_service() -> ConversationService:
    """获取对话服务实例"""
    return conversation_service
