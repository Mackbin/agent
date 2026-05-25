"""
模型管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.schemas import ModelInfo
from app.models import ModelConfig, User
from app.auth import get_current_user
from app.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/models", tags=["模型管理"])


@router.get("", response_model=List[ModelInfo])
async def list_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取可用模型列表"""
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.is_active == True)
    )
    models = result.scalars().all()
    
    return [
        ModelInfo(
            id=f"{model.provider}/{model.model_name}",
            name=model.model_name,
            provider=model.provider,
            is_active=model.is_active,
            cost_per_1k_tokens=float(model.cost_per_1k_tokens) if model.cost_per_1k_tokens else None,
            max_tokens=model.config.get("max_tokens") if model.config else None,
            context_window=model.config.get("context_window") if model.config else None
        )
        for model in models
    ]


@router.get("/{model_id}", response_model=ModelInfo)
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模型详情"""
    # 解析 model_id (格式：provider/model_name)
    if "/" not in model_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的模型 ID 格式，应为 provider/model_name"
        )
    
    provider, model_name = model_id.split("/", 1)
    
    result = await db.execute(
        select(ModelConfig).where(
            ModelConfig.provider == provider,
            ModelConfig.model_name == model_name
        )
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    return ModelInfo(
        id=model_id,
        name=model.model_name,
        provider=model.provider,
        is_active=model.is_active,
        cost_per_1k_tokens=float(model.cost_per_1k_tokens) if model.cost_per_1k_tokens else None,
        max_tokens=model.config.get("max_tokens") if model.config else None,
        context_window=model.config.get("context_window") if model.config else None
    )
