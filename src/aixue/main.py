"""FastAPI 应用入口。"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from aixue.api.router import api_router
from aixue.config import Settings
from aixue.db.base import Base
from aixue.db.engine import engine

# 确保所有模型注册到 Base.metadata
import aixue.models  # noqa: F401

# 日志配置集中在入口执行一次
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时自动建表。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表已就绪")
    yield
    await engine.dispose()


app = FastAPI(
    title="AIXue API",
    description="AIXue - AI 辅助学生学习的教育平台",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP 阶段允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理：确保所有未处理异常返回 JSON 格式，便于前端解析。"""
    logger.exception("未处理异常: %s %s", request.method, request.url.path)
    detail = str(exc) if str(exc) else "服务器内部错误，请稍后重试"
    return JSONResponse(status_code=500, content={"detail": detail})


@app.get("/health")
async def health_check() -> dict[str, str]:
    """健康检查端点。"""
    return {"status": "ok"}
