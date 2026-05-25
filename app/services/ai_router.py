"""
AI 路由服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import time
import structlog
from enum import Enum

from app.models import ModelConfig
from app.providers.base import BaseProvider, ChatMessage
from app.providers.openai import OpenAIProvider
from app.providers.claude import ClaudeProvider
from app.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ModelScore:
    """模型评分"""
    config: ModelConfig
    score: float
    latency: float = 0
    success_rate: float = 1.0
    cost: float = 0


class RoutingStrategy(Enum):
    """路由策略"""
    LATENCY = "latency"  # 延迟优先
    COST = "cost"  # 成本优先
    RELIABILITY = "reliability"  # 可靠性优先
    WEIGHTED = "weighted"  # 权重路由
    ROUND_ROBIN = "round_robin"  # 轮询


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"  # 正常
    OPEN = "open"  # 熔断
    HALF_OPEN = "half_open"  # 半开


class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self.half_open_calls = 0
    
    def record_success(self):
        """记录成功"""
        self.failure_count = 0
        self.success_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                self.half_open_calls = 0
    
    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.half_open_calls = 0
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def can_execute(self) -> bool:
        """检查是否可以执行请求"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        
        # HALF_OPEN 状态
        return self.half_open_calls < self.half_open_max_calls


class AIRouterService:
    """AI 路由服务"""
    
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.model_stats: Dict[str, Dict[str, Any]] = {}
        self.round_robin_index = 0
    
    def register_provider(self, name: str, provider: BaseProvider):
        """注册 Provider"""
        self.providers[name] = provider
        self.circuit_breakers[name] = CircuitBreaker()
        self.model_stats[name] = {
            "total_requests": 0,
            "failed_requests": 0,
            "total_latency": 0,
            "last_request_time": None
        }
    
    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """获取 Provider"""
        return self.providers.get(name)
    
    async def get_available_models(
        self,
        db: AsyncSession,
        model_name: Optional[str] = None
    ) -> List[ModelConfig]:
        """获取可用模型列表"""
        query = select(ModelConfig).where(ModelConfig.is_active == True)
        
        if model_name:
            query = query.where(ModelConfig.model_name == model_name)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    def calculate_score(
        self,
        config: ModelConfig,
        strategy: RoutingStrategy = RoutingStrategy.WEIGHTED,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ModelScore:
        """计算模型评分"""
        provider_name = config.provider
        stats = self.model_stats.get(provider_name, {})
        
        # 基础数据
        total_requests = stats.get("total_requests", 0) or 1
        failed_requests = stats.get("failed_requests", 0)
        total_latency = stats.get("total_latency", 0)
        
        avg_latency = total_latency / total_requests if total_requests > 0 else 0
        success_rate = 1 - (failed_requests / total_requests) if total_requests > 0 else 1.0
        cost = float(config.cost_per_1k_tokens or 0)
        
        # 根据策略计算评分
        if strategy == RoutingStrategy.LATENCY:
            # 延迟优先：延迟越低分越高
            score = (1 / (1 + avg_latency / 1000)) * config.weight
        elif strategy == RoutingStrategy.COST:
            # 成本优先：成本越低分越高
            score = (1 / (1 + cost)) * config.weight
        elif strategy == RoutingStrategy.RELIABILITY:
            # 可靠性优先：成功率越高越好
            score = success_rate * config.weight
        else:
            # 权重路由：综合考虑
            latency_score = 1 / (1 + avg_latency / 1000)
            cost_score = 1 / (1 + cost)
            reliability_score = success_rate
            
            # 默认权重：可靠性 40%, 延迟 30%, 成本 30%
            score = (
                reliability_score * 0.4 +
                latency_score * 0.3 +
                cost_score * 0.3
            ) * config.weight
        
        # 用户偏好调整
        if user_preferences:
            if user_preferences.get("preferred_provider") == config.provider:
                score *= 1.2
            if user_preferences.get("max_cost") and cost > user_preferences["max_cost"]:
                score *= 0.5
        
        return ModelScore(
            config=config,
            score=score,
            latency=avg_latency,
            success_rate=success_rate,
            cost=cost
        )
    
    async def route_request(
        self,
        db: AsyncSession,
        model_name: Optional[str] = None,
        strategy: RoutingStrategy = RoutingStrategy.WEIGHTED,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[tuple[ModelConfig, BaseProvider]]:
        """路由请求到最优模型"""
        # 获取可用模型
        models = await self.get_available_models(db, model_name)
        
        if not models:
            logger.warning("没有可用模型")
            return None
        
        # 过滤熔断的模型
        available_models = []
        for model in models:
            breaker = self.circuit_breakers.get(model.provider)
            if breaker and breaker.can_execute():
                available_models.append(model)
            else:
                logger.warning(
                    "模型被熔断",
                    provider=model.provider,
                    model=model.model_name
                )
        
        if not available_models:
            logger.error("所有模型都被熔断")
            return None
        
        # 计算评分
        scored_models = [
            self.calculate_score(model, strategy, user_preferences)
            for model in available_models
        ]
        
        # 排序
        scored_models.sort(key=lambda x: x.score, reverse=True)
        
        # 选择最优模型
        best = scored_models[0]
        provider = self.get_provider(best.config.provider)
        
        if provider:
            logger.info(
                "路由选择",
                provider=best.config.provider,
                model=best.config.model_name,
                score=best.score
            )
            return best.config, provider
        
        return None
    
    def record_request(
        self,
        provider_name: str,
        success: bool,
        latency_ms: int
    ):
        """记录请求结果"""
        if provider_name not in self.model_stats:
            self.model_stats[provider_name] = {
                "total_requests": 0,
                "failed_requests": 0,
                "total_latency": 0
            }
        
        stats = self.model_stats[provider_name]
        stats["total_requests"] += 1
        stats["total_latency"] += latency_ms
        stats["last_request_time"] = time.time()
        
        if not success:
            stats["failed_requests"] += 1
        
        # 更新熔断器
        breaker = self.circuit_breakers.get(provider_name)
        if breaker:
            if success:
                breaker.record_success()
            else:
                breaker.record_failure()
    
    def get_fallback_model(
        self,
        scored_models: List[ModelScore]
    ) -> Optional[ModelConfig]:
        """获取降级模型"""
        if len(scored_models) < 2:
            return None
        
        # 返回评分第二的模型
        return scored_models[1].config


# 全局路由服务实例
ai_router = AIRouterService()


def get_ai_router() -> AIRouterService:
    """获取 AI 路由服务实例"""
    return ai_router
