from fastapi import APIRouter
from .alerts import router as alerts_router
from .actions import router as actions_router

# 创建主路由器
api_router = APIRouter(prefix="/api/v1")

# 注册子路由
api_router.include_router(alerts_router)
api_router.include_router(actions_router)

__all__ = ["api_router"]