from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import hashlib

Base = declarative_base()


class User(Base):
    """
    用户模型
    """
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    password_hash = Column(String(128), nullable=False, comment="密码哈希")
    
    # 用户信息
    full_name = Column(String(100), comment="真实姓名")
    phone = Column(String(20), comment="手机号")
    department = Column(String(100), comment="部门")
    position = Column(String(100), comment="职位")
    
    # 权限和状态
    role = Column(String(20), default="viewer", comment="角色：admin, operator, viewer")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_verified = Column(Boolean, default=False, comment="是否已验证")
    
    # 权限配置
    permissions = Column(JSON, comment="用户权限配置")
    
    # 登录信息
    last_login_at = Column(DateTime, comment="最后登录时间")
    last_login_ip = Column(String(45), comment="最后登录IP")
    login_count = Column(Integer, default=0, comment="登录次数")
    
    # 密码相关
    password_changed_at = Column(DateTime, comment="密码修改时间")
    password_reset_token = Column(String(100), comment="密码重置令牌")
    password_reset_expires = Column(DateTime, comment="密码重置过期时间")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 其他信息
    avatar_url = Column(String(500), comment="头像URL")
    bio = Column(Text, comment="个人简介")
    settings = Column(JSON, comment="用户设置")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
    
    def set_password(self, password: str):
        """设置密码"""
        self.password_hash = self._hash_password(password)
        self.password_changed_at = datetime.utcnow()
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        return self.password_hash == self._hash_password(password)
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def has_permission(self, permission: str) -> bool:
        """检查权限"""
        if self.role == "admin":
            return True
        
        if not self.permissions:
            return False
        
        return permission in self.permissions.get("allowed", [])
    
    def is_admin(self) -> bool:
        """是否管理员"""
        return self.role == "admin"
    
    def is_operator(self) -> bool:
        """是否操作员"""
        return self.role in ["admin", "operator"]
    
    def can_scan(self) -> bool:
        """是否可以执行扫描"""
        return self.is_operator() or self.has_permission("scan:execute")
    
    def can_view_results(self) -> bool:
        """是否可以查看结果"""
        return self.is_active and (self.is_operator() or self.has_permission("results:view"))
    
    def can_manage_users(self) -> bool:
        """是否可以管理用户"""
        return self.is_admin() or self.has_permission("users:manage")
    
    def update_login_info(self, ip_address: str):
        """更新登录信息"""
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip_address
        self.login_count += 1
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "department": self.department,
            "position": self.position,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "avatar_url": self.avatar_url,
            "bio": self.bio
        }
        
        if include_sensitive:
            data.update({
                "permissions": self.permissions,
                "settings": self.settings,
                "login_count": self.login_count,
                "last_login_ip": self.last_login_ip
            })
        
        return data


class UserSession(Base):
    """
    用户会话模型
    """
    __tablename__ = "user_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, comment="用户ID")
    session_token = Column(String(128), unique=True, nullable=False, comment="会话令牌")
    
    # 会话信息
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(Text, comment="用户代理")
    device_info = Column(JSON, comment="设备信息")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    last_accessed_at = Column(DateTime, default=datetime.utcnow, comment="最后访问时间")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
    
    def is_expired(self) -> bool:
        """是否过期"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """是否有效"""
        return self.is_active and not self.is_expired()
    
    def update_access_time(self):
        """更新访问时间"""
        self.last_accessed_at = datetime.utcnow()


class UserLoginLog(Base):
    """
    用户登录日志模型
    """
    __tablename__ = "user_login_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), comment="用户ID")
    username = Column(String(50), comment="用户名")
    
    # 登录信息
    login_type = Column(String(20), comment="登录类型：password, token, sso")
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(Text, comment="用户代理")
    
    # 结果信息
    success = Column(Boolean, nullable=False, comment="是否成功")
    failure_reason = Column(String(200), comment="失败原因")
    
    # 时间信息
    login_time = Column(DateTime, default=datetime.utcnow, comment="登录时间")
    logout_time = Column(DateTime, comment="登出时间")
    
    # 地理位置（可选）
    location_info = Column(JSON, comment="地理位置信息")
    
    def __repr__(self):
        return f"<UserLoginLog(id={self.id}, username={self.username}, success={self.success})>"
    
    def get_session_duration(self):
        """获取会话时长"""
        if self.logout_time and self.login_time:
            return (self.logout_time - self.login_time).total_seconds()
        return None