from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.user_service import UserService
from ..schemas.user_schema import (
    UserCreate, UserUpdate, UserResponse, UserQuery, UserStats
)

router = APIRouter()

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

@router.get("/", response_model=List[UserResponse], summary="获取用户列表")
async def get_users(
    username: Optional[str] = Query(None, description="用户名"),
    email: Optional[str] = Query(None, description="邮箱地址"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    is_superuser: Optional[bool] = Query(None, description="是否超级用户"),
    limit: int = Query(100, description="返回数量限制", ge=1, le=1000),
    offset: int = Query(0, description="偏移量", ge=0),
    user_service: UserService = Depends(get_user_service)
):
    """获取用户列表，支持分页和过滤"""
    query = UserQuery(
        username=username,
        email=email,
        is_active=is_active,
        is_superuser=is_superuser,
        limit=limit,
        offset=offset
    )
    
    users = user_service.get_users(query)
    return users

@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """获取指定用户的详细信息"""
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return UserResponse.from_orm(user)

@router.post("/", response_model=UserResponse, summary="创建用户")
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """创建新用户"""
    try:
        user = user_service.create_user(user_data)
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户失败: {str(e)}"
        )

@router.put("/{user_id}", response_model=UserResponse, summary="更新用户")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """更新用户信息"""
    try:
        user = user_service.update_user(user_id, user_update)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户失败: {str(e)}"
        )

@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """删除用户"""
    success = user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return {"message": "用户删除成功"}

@router.get("/stats/overview", response_model=UserStats, summary="用户统计")
async def get_user_stats(
    user_service: UserService = Depends(get_user_service)
):
    """获取用户统计信息"""
    return user_service.get_user_stats()

@router.post("/{user_id}/activate", summary="激活用户")
async def activate_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """激活用户"""
    success = user_service.activate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return {"message": "用户激活成功"}

@router.post("/{user_id}/deactivate", summary="停用用户")
async def deactivate_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """停用用户"""
    success = user_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return {"message": "用户停用成功"}

@router.get("/{user_id}/activity", summary="获取用户活动日志")
async def get_user_activity(
    user_id: int,
    limit: int = Query(50, description="返回数量限制", ge=1, le=1000),
    user_service: UserService = Depends(get_user_service)
):
    """获取用户的活动日志"""
    # 检查用户是否存在
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    activity_logs = user_service.get_user_activity(user_id, limit)
    return {
        "user_id": user_id,
        "activity_count": len(activity_logs),
        "activities": activity_logs
    }

@router.get("/{user_id}/permissions", summary="获取用户权限")
async def get_user_permissions(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """获取用户的权限列表"""
    # 检查用户是否存在
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    permissions = user_service.get_user_permissions(user_id)
    return {
        "user_id": user_id,
        "permissions": permissions
    }

@router.post("/{user_id}/check-permission", summary="检查用户权限")
async def check_user_permission(
    user_id: int,
    resource: str,
    action: str,
    user_service: UserService = Depends(get_user_service)
):
    """检查用户是否有指定权限"""
    # 检查用户是否存在
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    has_permission = user_service.check_permission(user_id, resource, action)
    return {
        "user_id": user_id,
        "resource": resource,
        "action": action,
        "granted": has_permission
    }

@router.get("/search/", summary="搜索用户")
async def search_users(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(50, description="返回数量限制", ge=1, le=1000),
    user_service: UserService = Depends(get_user_service)
):
    """搜索用户"""
    # 这里应该实现用户搜索功能
    # 为了简化，这里只是返回空结果
    return {
        "query": q,
        "results": [],
        "total": 0
    }

@router.get("/by-username/{username}", response_model=UserResponse, summary="根据用户名获取用户")
async def get_user_by_username(
    username: str,
    user_service: UserService = Depends(get_user_service)
):
    """根据用户名获取用户信息"""
    user = user_service.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return UserResponse.from_orm(user)

@router.get("/by-email/{email}", response_model=UserResponse, summary="根据邮箱获取用户")
async def get_user_by_email(
    email: str,
    user_service: UserService = Depends(get_user_service)
):
    """根据邮箱获取用户信息"""
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return UserResponse.from_orm(user)
