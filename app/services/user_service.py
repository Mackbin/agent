"""
用户服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from typing import Optional, List
import structlog

from app.models import User, APIKey, Conversation
from app.security import get_password_hash, verify_password, generate_api_key, hash_api_key
from app.schemas import UserCreate, APIKeyCreate
from app.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """用户服务类"""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise ValueError("用户名已存在")
        
        # 检查邮箱是否已存在
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise ValueError("邮箱已被注册")
        
        # 创建用户
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            api_key=generate_api_key(),
            status=1
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info("用户创建成功", user_id=str(user.id), username=user.username)
        
        return user
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str
    ) -> Optional[User]:
        """认证用户"""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user or user.status != 1:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """通过 ID 获取用户"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_username(
        db: AsyncSession,
        username: str
    ) -> Optional[User]:
        """通过用户名获取用户"""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_api_key(
        db: AsyncSession,
        user_id: str,
        api_key_data: APIKeyCreate
    ) -> APIKey:
        """创建 API Key"""
        raw_api_key = generate_api_key()
        key_hash = hash_api_key(raw_api_key)
        
        expires_at = None
        if api_key_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_in_days)
        
        api_key = APIKey(
            user_id=user_id,
            key_hash=key_hash,
            name=api_key_data.name,
            permissions=api_key_data.permissions,
            rate_limit=api_key_data.rate_limit,
            expires_at=expires_at,
            is_active=True
        )
        
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        
        logger.info(
            "API Key 创建成功",
            user_id=user_id,
            api_key_id=str(api_key.id),
            name=api_key_data.name
        )
        
        # 返回时附带原始 API Key（只显示一次）
        api_key._raw_key = raw_api_key
        
        return api_key
    
    @staticmethod
    async def list_api_keys(
        db: AsyncSession,
        user_id: str
    ) -> List[APIKey]:
        """列出用户的所有 API Key"""
        result = await db.execute(
            select(APIKey)
            .where(APIKey.user_id == user_id)
            .order_by(APIKey.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def revoke_api_key(
        db: AsyncSession,
        user_id: str,
        api_key_id: str
    ) -> bool:
        """撤销 API Key"""
        result = await db.execute(
            select(APIKey).where(
                APIKey.id == api_key_id,
                APIKey.user_id == user_id
            )
        )
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            return False
        
        api_key.is_active = False
        await db.commit()
        
        logger.info(
            "API Key 已撤销",
            user_id=user_id,
            api_key_id=api_key_id
        )
        
        return True
    
    @staticmethod
    async def get_user_stats(
        db: AsyncSession,
        user_id: str
    ) -> dict:
        """获取用户统计信息"""
        # 获取会话数量
        conversation_result = await db.execute(
            select(Conversation).where(Conversation.user_id == user_id)
        )
        conversations = conversation_result.scalars().all()
        
        total_conversations = len(conversations)
        total_messages = sum(c.message_count for c in conversations)
        total_tokens = sum(c.total_tokens for c in conversations)
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_tokens": total_tokens
        }
