"""
认证依赖和中间件
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import structlog

from app.database import get_db
from app.models import User, APIKey
from app.security import decode_access_token, hash_api_key, verify_api_key_signature
from app.logging import get_logger

logger = get_logger(__name__)

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)

# API Key 认证（从 Header 获取）
api_key_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户（JWT 认证）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_access_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None or user.status != 1:
        raise credentials_exception
    
    return user


async def get_api_key_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取 API Key 用户"""
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 API Key"
        )
    
    # 哈希 API Key
    key_hash = hash_api_key(api_key)
    
    # 查询 API Key
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        )
    )
    api_key_obj = result.scalar_one_or_none()
    
    if api_key_obj is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 API Key"
        )
    
    # 检查是否过期
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key 已过期"
        )
    
    # 获取用户
    result = await db.execute(select(User).where(User.id == api_key_obj.user_id))
    user = result.scalar_one_or_none()
    
    if user is None or user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用"
        )
    
    # 更新最后使用时间
    api_key_obj.last_used_at = datetime.utcnow()
    await db.commit()
    
    return user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """可选的用户认证（有认证则返回用户，否则返回 None）"""
    try:
        # 尝试 JWT Token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_access_token(token)
            if payload:
                user_id = payload.get("sub")
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                if user and user.status == 1:
                    return user
        
        # 尝试 API Key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            key_hash = hash_api_key(api_key)
            result = await db.execute(
                select(APIKey).where(
                    APIKey.key_hash == key_hash,
                    APIKey.is_active == True
                )
            )
            api_key_obj = result.scalar_one_or_none()
            
            if api_key_obj and (not api_key_obj.expires_at or api_key_obj.expires_at >= datetime.utcnow()):
                result = await db.execute(select(User).where(User.id == api_key_obj.user_id))
                user = result.scalar_one_or_none()
                if user and user.status == 1:
                    return user
        
        return None
    except Exception:
        return None
