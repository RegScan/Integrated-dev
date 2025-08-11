from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.user_service import UserService
from ..schemas.user_schema import (
    UserCreate, UserResponse, UserLogin, UserAuthResponse,
    PasswordReset, PasswordResetConfirm
)

router = APIRouter()
security = HTTPBearer()

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service)
) -> Optional[UserResponse]:
    """获取当前用户"""
    token = credentials.credentials
    user = user_service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UserResponse.from_orm(user)

@router.post("/login", response_model=UserAuthResponse, summary="用户登录")
async def login(
    user_login: UserLogin,
    user_service: UserService = Depends(get_user_service)
):
    """用户登录接口"""
    auth_response = user_service.login_user(user_login)
    if not auth_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_response

@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """用户注册接口"""
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
            detail=f"注册失败: {str(e)}"
        )

@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    """获取当前登录用户的信息"""
    return current_user

@router.post("/logout", summary="用户登出")
async def logout():
    """用户登出接口"""
    # 在实际实现中，这里应该将令牌加入黑名单
    return {"message": "登出成功"}

@router.post("/refresh", response_model=UserAuthResponse, summary="刷新令牌")
async def refresh_token(
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """刷新访问令牌"""
    # 这里应该实现令牌刷新逻辑
    # 为了简化，这里只是返回成功
    return {
        "access_token": "new_token_here",
        "token_type": "bearer",
        "expires_in": 1800,
        "user": current_user
    }

@router.post("/password/reset", summary="请求密码重置")
async def request_password_reset(
    password_reset: PasswordReset,
    user_service: UserService = Depends(get_user_service)
):
    """请求密码重置"""
    success = user_service.reset_password_request(password_reset)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮箱地址不存在"
        )
    return {"message": "密码重置邮件已发送"}

@router.post("/password/reset/confirm", summary="确认密码重置")
async def confirm_password_reset(
    password_reset_confirm: PasswordResetConfirm,
    user_service: UserService = Depends(get_user_service)
):
    """确认密码重置"""
    success = user_service.reset_password_confirm(password_reset_confirm)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的重置令牌"
        )
    return {"message": "密码重置成功"}

@router.post("/password/change", summary="修改密码")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """修改密码"""
    success = user_service.change_password(current_user.id, old_password, new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    return {"message": "密码修改成功"}

@router.get("/verify", summary="验证令牌")
async def verify_token(
    current_user: UserResponse = Depends(get_current_user)
):
    """验证访问令牌的有效性"""
    return {
        "valid": True,
        "user": current_user
    }

@router.get("/permissions", summary="获取用户权限")
async def get_user_permissions(
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """获取当前用户的权限列表"""
    permissions = user_service.get_user_permissions(current_user.id)
    return {"permissions": permissions}

@router.post("/check-permission", summary="检查权限")
async def check_permission(
    resource: str,
    action: str,
    current_user: UserResponse = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """检查用户是否有指定权限"""
    has_permission = user_service.check_permission(current_user.id, resource, action)
    return {
        "resource": resource,
        "action": action,
        "granted": has_permission
    }
