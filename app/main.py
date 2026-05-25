"""
FastAPI 应用主入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app, Counter, Histogram
import structlog
import time

from app.config import settings
from app.logging import setup_logging, get_logger
from app.database import init_db, close_db
from app.redis import close_redis
from app.routers import auth, chat, conversations, models

# 设置日志
setup_logging()
logger = get_logger(__name__)

# Prometheus 指标
REQUEST_COUNT = Counter(
    "app_requests_total",
    "Total request count",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("应用启动中...")
    
    # 初始化数据库
    await init_db()
    logger.info("数据库初始化完成")
    
    # 注册 AI Provider
    from app.providers.openai import OpenAIProvider
    from app.providers.claude import ClaudeProvider
    from app.services.ai_router import get_ai_router
    
    ai_router = get_ai_router()
    
    if settings.OPENAI_API_KEY:
        openai_provider = OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        ai_router.register_provider("openai", openai_provider)
        logger.info("OpenAI Provider 注册成功")
    
    if settings.CLAUDE_API_KEY:
        claude_provider = ClaudeProvider(
            api_key=settings.CLAUDE_API_KEY,
            base_url=settings.CLAUDE_BASE_URL
        )
        ai_router.register_provider("claude", claude_provider)
        logger.info("Claude Provider 注册成功")
    
    yield
    
    # 关闭时执行
    logger.info("应用关闭中...")
    await close_db()
    await close_redis()
    logger.info("应用已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="统一的 AI 模型接入平台 - 支持 OpenAI、Claude 等多个 Provider",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    logger.info(
        "请求完成",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration * 1000
    )
    
    # 更新 Prometheus 指标
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(
        "未处理的异常",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"服务器内部错误：{str(exc)}"}
    )


# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")

# Prometheus 监控端点
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# 健康检查
@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": time.time()
    }


# 根路径
@app.get("/", tags=["根路径"])
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
