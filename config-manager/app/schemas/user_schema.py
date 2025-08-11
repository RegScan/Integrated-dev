from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """用户角色"""
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"

class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

# 基础用户模型
class UserBase(BaseModel):
    username: str = Field(..., description="用户名", min_length=3, max_length=50)
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, description="全名", max_length=100)
    is_active: bool = Field(True, description="是否激活")
    is_superuser: bool = Field(False, description="是否超级用户")

# 创建用户模型
class UserCreate(UserBase):
    password: str = Field(..., description="密码", min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v

# 更新用户模型
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    full_name: Optional[str] = Field(None, description="全名", max_length=100)
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_superuser: Optional[bool] = Field(None, description="是否超级用户")
    password: Optional[str] = Field(None, description="新密码", min_length=8)

# 用户响应模型
class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# 用户登录模型
class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

# 用户认证响应模型
class UserAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

# 密码重置模型
class PasswordReset(BaseModel):
    email: EmailStr = Field(..., description="邮箱地址")

class PasswordResetConfirm(BaseModel):
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., description="新密码", min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v

# 用户权限模型
class UserPermission(BaseModel):
    user_id: int
    resource: str = Field(..., description="资源名称")
    action: str = Field(..., description="操作类型")
    granted: bool = Field(True, description="是否授权")

class UserPermissionCreate(UserPermission):
    pass

class UserPermissionResponse(UserPermission):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 用户组模型
class UserGroupBase(BaseModel):
    name: str = Field(..., description="组名称", max_length=100)
    description: Optional[str] = Field(None, description="组描述")
    is_active: bool = Field(True, description="是否激活")

class UserGroupCreate(UserGroupBase):
    pass

class UserGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, description="组名称", max_length=100)
    description: Optional[str] = Field(None, description="组描述")
    is_active: Optional[bool] = Field(None, description="是否激活")

class UserGroupResponse(UserGroupBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    user_count: int = Field(0, description="用户数量")
    
    class Config:
        from_attributes = True

# 用户查询模型
class UserQuery(BaseModel):
    username: Optional[str] = Field(None, description="用户名")
    email: Optional[str] = Field(None, description="邮箱地址")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_superuser: Optional[bool] = Field(None, description="是否超级用户")
    limit: int = Field(100, description="返回数量限制", ge=1, le=1000)
    offset: int = Field(0, description="偏移量", ge=0)

# 用户统计模型
class UserStats(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    superusers: int
    recent_registrations: List[UserResponse]
    users_by_status: dict

# 用户会话模型
class UserSession(BaseModel):
    user_id: int
    session_id: str
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    created_at: datetime
    expires_at: datetime
    is_active: bool = Field(True, description="是否活跃")

class UserSessionCreate(BaseModel):
    user_id: int
    session_id: str
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    expires_at: datetime

class UserSessionResponse(UserSession):
    id: int
    
    class Config:
        from_attributes = True
