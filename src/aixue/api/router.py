"""总路由聚合：汇集所有 API 端点。"""

from fastapi import APIRouter

from aixue.api.endpoints import auth, diagnosis, problems, solver, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(solver.router)
api_router.include_router(diagnosis.router)
api_router.include_router(problems.router)
