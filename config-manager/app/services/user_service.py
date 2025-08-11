from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import hashlib
import secrets
import logging
from passlib.context import CryptContext
from jose import JWTError, jwt

from ..database import User, ConfigAccessLog
from ..schemas.user_schema import (
    UserCreate, UserUpdate, UserResponse, UserLogin, UserAuthResponse,
    PasswordReset, PasswordResetConfirm, UserQuery, UserStats
)
from ..config import settings

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def _hash_password(self, password: str) -> str:
        """哈希密码"""
        return pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def _create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def _verify_token(self, token: str) -> Optional[dict]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    def create_user(self, user_data: UserCreate) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        existing_user = self.db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise ValueError("用户名已存在")
        
        # 检查邮箱是否已存在
        existing_email = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise ValueError("邮箱已存在")
        
        # 创建用户
        hashed_password = self._hash_password(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=user_data.is_active,
            is_superuser=user_data.is_superuser
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        logger.info(f"创建用户: {user_data.username}")
        return db_user
    
    def get_user(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """更新用户"""
        db_user = self.get_user(user_id)
        if not db_user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        
        # 如果更新密码，需要哈希
        if "password" in update_data:
            update_data["hashed_password"] = self._hash_password(update_data.pop("password"))
        
        # 检查邮箱唯一性
        if "email" in update_data:
            existing_email = self.db.query(User).filter(
                and_(User.email == update_data["email"], User.id != user_id)
            ).first()
            if existing_email:
                raise ValueError("邮箱已存在")
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db_user.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(db_user)
        
        logger.info(f"更新用户: {db_user.username}")
        return db_user
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        db_user = self.get_user(user_id)
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        
        logger.info(f"删除用户: {db_user.username}")
        return True
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        if not self._verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    def login_user(self, user_login: UserLogin) -> Optional[UserAuthResponse]:
        """用户登录"""
        user = self.authenticate_user(user_login.username, user_login.password)
        if not user:
            return None
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self._create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        )
        
        return UserAuthResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
    
    def get_current_user(self, token: str) -> Optional[User]:
        """获取当前用户"""
        payload = self._verify_token(token)
        if payload is None:
            return None
        
        username: str = payload.get("sub")
        if username is None:
            return None
        
        user = self.get_user_by_username(username)
        if user is None:
            return None
        
        return user
    
    def get_users(self, query: UserQuery) -> List[User]:
        """查询用户列表"""
        filters = []
        
        if query.username:
            filters.append(User.username.like(f"%{query.username}%"))
        if query.email:
            filters.append(User.email.like(f"%{query.email}%"))
        if query.is_active is not None:
            filters.append(User.is_active == query.is_active)
        if query.is_superuser is not None:
            filters.append(User.is_superuser == query.is_superuser)
        
        query_obj = self.db.query(User)
        if filters:
            query_obj = query_obj.filter(and_(*filters))
        
        return query_obj.offset(query.offset).limit(query.limit).all()
    
    def get_user_stats(self) -> UserStats:
        """获取用户统计信息"""
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        inactive_users = self.db.query(User).filter(User.is_active == False).count()
        superusers = self.db.query(User).filter(User.is_superuser == True).count()
        
        # 最近注册的用户
        recent_registrations = self.db.query(User).order_by(User.created_at.desc()).limit(10).all()
        
        # 按状态统计
        users_by_status = {
            "active": active_users,
            "inactive": inactive_users,
            "superuser": superusers
        }
        
        return UserStats(
            total_users=total_users,
            active_users=active_users,
            inactive_users=inactive_users,
            superusers=superusers,
            recent_registrations=recent_registrations,
            users_by_status=users_by_status
        )
    
    def reset_password_request(self, password_reset: PasswordReset) -> bool:
        """请求密码重置"""
        user = self.get_user_by_email(password_reset.email)
        if not user:
            return False
        
        # 生成重置令牌
        reset_token = secrets.token_urlsafe(32)
        # 这里应该将令牌存储到数据库或缓存中，并设置过期时间
        # 为了简化，这里只是返回成功
        
        logger.info(f"密码重置请求: {user.email}")
        return True
    
    def reset_password_confirm(self, password_reset_confirm: PasswordResetConfirm) -> bool:
        """确认密码重置"""
        # 这里应该验证令牌的有效性
        # 为了简化，这里假设令牌有效
        
        # 查找用户（这里需要根据令牌找到用户）
        # 实际实现中，应该从令牌中解析用户信息或从缓存中获取
        
        logger.info("密码重置确认")
        return True
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        # 验证旧密码
        if not self._verify_password(old_password, user.hashed_password):
            return False
        
        # 更新密码
        user.hashed_password = self._hash_password(new_password)
        user.updated_at = datetime.now()
        self.db.commit()
        
        logger.info(f"用户修改密码: {user.username}")
        return True
    
    def get_user_permissions(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户权限"""
        # 这里应该实现权限系统
        # 为了简化，返回基本权限
        user = self.get_user(user_id)
        if not user:
            return []
        
        permissions = []
        
        # 超级用户拥有所有权限
        if user.is_superuser:
            permissions = [
                {"resource": "*", "action": "*", "granted": True}
            ]
        else:
            # 普通用户权限
            permissions = [
                {"resource": "config", "action": "read", "granted": True},
                {"resource": "config", "action": "write", "granted": user.is_active},
                {"resource": "user", "action": "read", "granted": True},
                {"resource": "user", "action": "write", "granted": False}
            ]
        
        return permissions
    
    def check_permission(self, user_id: int, resource: str, action: str) -> bool:
        """检查用户权限"""
        permissions = self.get_user_permissions(user_id)
        
        for permission in permissions:
            if (permission["resource"] == "*" and permission["action"] == "*") or \
               (permission["resource"] == resource and permission["action"] == action):
                return permission["granted"]
        
        return False
    
    def get_user_activity(self, user_id: int, limit: int = 50) -> List[ConfigAccessLog]:
        """获取用户活动日志"""
        return self.db.query(ConfigAccessLog).filter(
            ConfigAccessLog.user_id == user_id
        ).order_by(ConfigAccessLog.created_at.desc()).limit(limit).all()
    
    def activate_user(self, user_id: int) -> bool:
        """激活用户"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        user.is_active = True
        user.updated_at = datetime.now()
        self.db.commit()
        
        logger.info(f"激活用户: {user.username}")
        return True
    
    def deactivate_user(self, user_id: int) -> bool:
        """停用用户"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        user.is_active = False
        user.updated_at = datetime.now()
        self.db.commit()
        
        logger.info(f"停用用户: {user.username}")
        return True
