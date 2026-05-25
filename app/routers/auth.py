"""
用户认证 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from typing import List

from app.database import get_db
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    APIKeyCreate,
    APIKeyResponse,
    Token,
)
from app.services.user_service import UserService
from app.security import create_access_token
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    try:
        user = await UserService.create_user(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    user = await UserService.authenticate_user(
        db,
        login_data.username,
        login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 创建 Access Token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=1440)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user


@router.post("/api-key", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新的 API Key"""
    try:
        api_key = await UserService.create_api_key(
            db,
            str(current_user.id),
            api_key_data
        )
        
        response = APIKeyResponse(
            id=str(api_key.id),
            name=api_key.name,
            key_prefix=api_key.key_hash[:8] + "...",
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at
        )
        
        # 在响应头中返回完整的 API Key（只显示一次）
        response.headers["X-API-Key"] = getattr(api_key, "_raw_key", "")
        
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """列出所有 API Key"""
    api_keys = await UserService.list_api_keys(db, str(current_user.id))
    
    return [
        APIKeyResponse(
            id=str(api_key.id),
            name=api_key.name,
            key_prefix=api_key.key_hash[:8] + "...",
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at
        )
        for api_key in api_keys
    ]


@router.delete("/api-key/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """撤销 API Key"""
    success = await UserService.revoke_api_key(
        db,
        str(current_user.id),
        api_key_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key 不存在"
        )
