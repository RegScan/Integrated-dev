from typing import Dict, Any, List, Optional
import yaml
import json
import hashlib
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging
from cryptography.fernet import Fernet
import base64

from ..database import Config, ConfigVersion, ConfigTemplate, ConfigGroup, ConfigAccessLog, User
from ..schemas.config_schema import (
    ConfigCreate, ConfigUpdate, ConfigQuery, ConfigStats,
    ConfigTemplateCreate, ConfigGroupCreate, BatchConfigUpdate
)
from ..config import settings

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, db: Session, config_path: str = "configs/default.yaml"):
        self.db = db
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._encryption_key = self._get_encryption_key()
        self._fernet = Fernet(self._encryption_key) if self._encryption_key else None
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            logger.warning(f"配置文件不存在: {self.config_path}")
            return {}
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def _get_encryption_key(self) -> Optional[bytes]:
        """获取加密密钥"""
        key = settings.SECRET_KEY
        if not key or key == "your-secret-key-here":
            logger.warning("未设置加密密钥，敏感配置将不加密")
            return None
        
        # 生成32字节的密钥
        key_bytes = hashlib.sha256(key.encode()).digest()
        return base64.urlsafe_b64encode(key_bytes)
    
    def _encrypt_value(self, value: str) -> str:
        """加密配置值"""
        if not self._fernet:
            return value
        try:
            encrypted = self._fernet.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"加密失败: {e}")
            return value
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """解密配置值"""
        if not self._fernet:
            return encrypted_value
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"解密失败: {e}")
            return encrypted_value
    
    def get_config(self, key: str, default: Any = None, user_id: Optional[int] = None) -> Any:
        """获取配置项（优先从数据库获取）"""
        # 先从数据库查询
        db_config = self.db.query(Config).filter(Config.key == key).first()
        if db_config:
            # 记录访问日志
            self._log_access(db_config.id, "read", user_id)
            
            # 如果是加密配置，需要解密
            if db_config.is_encrypted:
                return self._decrypt_value(db_config.value)
            return db_config.value
        
        # 从文件配置获取
        keys = key.split('.')
        value = self._config
        for k in keys:
            if not isinstance(value, dict):
                return default
            value = value.get(k)
            if value is None:
                return default
        return value
    
    def set_config(self, config_data: ConfigCreate, user_id: Optional[int] = None) -> Config:
        """设置配置项"""
        # 检查是否已存在
        existing_config = self.db.query(Config).filter(Config.key == config_data.key).first()
        
        if existing_config:
            # 更新现有配置
            return self.update_config(existing_config.id, ConfigUpdate(**config_data.dict()), user_id)
        
        # 创建新配置
        config_value = config_data.value
        if config_data.is_encrypted:
            config_value = self._encrypt_value(config_data.value)
        
        db_config = Config(
            key=config_data.key,
            value=config_value,
            description=config_data.description,
            category=config_data.category.value,
            environment=config_data.environment.value,
            is_encrypted=config_data.is_encrypted,
            is_sensitive=config_data.is_sensitive,
            owner_id=user_id
        )
        
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        
        # 记录访问日志
        self._log_access(db_config.id, "write", user_id)
        
        logger.info(f"创建配置: {config_data.key}")
        return db_config
    
    def update_config(self, config_id: int, config_update: ConfigUpdate, user_id: Optional[int] = None) -> Config:
        """更新配置项"""
        db_config = self.db.query(Config).filter(Config.id == config_id).first()
        if not db_config:
            raise ValueError(f"配置不存在: {config_id}")
        
        # 保存当前版本
        self._create_version(db_config, user_id)
        
        # 更新配置
        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "value" and db_config.is_encrypted:
                value = self._encrypt_value(value)
            setattr(db_config, field, value)
        
        db_config.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(db_config)
        
        # 记录访问日志
        self._log_access(db_config.id, "write", user_id)
        
        logger.info(f"更新配置: {db_config.key}")
        return db_config
    
    def delete_config(self, config_id: int, user_id: Optional[int] = None) -> bool:
        """删除配置项"""
        db_config = self.db.query(Config).filter(Config.id == config_id).first()
        if not db_config:
            return False
        
        # 记录访问日志
        self._log_access(db_config.id, "delete", user_id)
        
        self.db.delete(db_config)
        self.db.commit()
        
        logger.info(f"删除配置: {db_config.key}")
        return True
    
    def get_configs(self, query: ConfigQuery) -> List[Config]:
        """查询配置列表"""
        filters = []
        
        if query.key:
            filters.append(Config.key.like(f"%{query.key}%"))
        if query.category:
            filters.append(Config.category == query.category.value)
        if query.environment:
            filters.append(Config.environment == query.environment.value)
        if query.is_encrypted is not None:
            filters.append(Config.is_encrypted == query.is_encrypted)
        if query.is_sensitive is not None:
            filters.append(Config.is_sensitive == query.is_sensitive)
        
        query_obj = self.db.query(Config)
        if filters:
            query_obj = query_obj.filter(and_(*filters))
        
        return query_obj.offset(query.offset).limit(query.limit).all()
    
    def get_config_stats(self) -> ConfigStats:
        """获取配置统计信息"""
        total_configs = self.db.query(Config).count()
        encrypted_configs = self.db.query(Config).filter(Config.is_encrypted == True).count()
        sensitive_configs = self.db.query(Config).filter(Config.is_sensitive == True).count()
        
        # 按分类统计
        configs_by_category = {}
        categories = self.db.query(Config.category).distinct().all()
        for category in categories:
            count = self.db.query(Config).filter(Config.category == category[0]).count()
            configs_by_category[category[0]] = count
        
        # 按环境统计
        configs_by_environment = {}
        environments = self.db.query(Config.environment).distinct().all()
        for env in environments:
            count = self.db.query(Config).filter(Config.environment == env[0]).count()
            configs_by_environment[env[0]] = count
        
        # 最近更新
        recent_updates = self.db.query(Config).order_by(Config.updated_at.desc()).limit(10).all()
        
        return ConfigStats(
            total_configs=total_configs,
            encrypted_configs=encrypted_configs,
            sensitive_configs=sensitive_configs,
            configs_by_category=configs_by_category,
            configs_by_environment=configs_by_environment,
            recent_updates=recent_updates
        )
    
    def batch_update_configs(self, batch_data: BatchConfigUpdate, user_id: Optional[int] = None) -> List[Config]:
        """批量更新配置"""
        updated_configs = []
        
        for config_item in batch_data.configs:
            key = config_item.get('key')
            value = config_item.get('value')
            
            if not key or value is None:
                continue
            
            # 查找现有配置
            existing_config = self.db.query(Config).filter(Config.key == key).first()
            
            if existing_config:
                # 更新现有配置
                config_update = ConfigUpdate(value=str(value))
                updated_config = self.update_config(existing_config.id, config_update, user_id)
            else:
                # 创建新配置
                config_create = ConfigCreate(
                    key=key,
                    value=str(value),
                    category="custom",
                    environment="development"
                )
                updated_config = self.set_config(config_create, user_id)
            
            updated_configs.append(updated_config)
        
        return updated_configs
    
    def create_template(self, template_data: ConfigTemplateCreate) -> ConfigTemplate:
        """创建配置模板"""
        db_template = ConfigTemplate(
            name=template_data.name,
            description=template_data.description,
            template_data=json.dumps(template_data.template_data),
            category=template_data.category.value,
            is_active=template_data.is_active
        )
        
        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)
        
        logger.info(f"创建配置模板: {template_data.name}")
        return db_template
    
    def create_group(self, group_data: ConfigGroupCreate) -> ConfigGroup:
        """创建配置组"""
        db_group = ConfigGroup(
            name=group_data.name,
            description=group_data.description,
            parent_group_id=group_data.parent_group_id
        )
        
        self.db.add(db_group)
        self.db.commit()
        self.db.refresh(db_group)
        
        logger.info(f"创建配置组: {group_data.name}")
        return db_group
    
    def _create_version(self, config: Config, user_id: Optional[int] = None):
        """创建配置版本"""
        # 获取最新版本号
        latest_version = self.db.query(ConfigVersion).filter(
            ConfigVersion.config_id == config.id
        ).order_by(ConfigVersion.version.desc()).first()
        
        version_number = (latest_version.version + 1) if latest_version else 1
        
        # 创建版本记录
        version = ConfigVersion(
            config_id=config.id,
            version=version_number,
            value=config.value,
            user_id=user_id
        )
        
        self.db.add(version)
        self.db.commit()
    
    def _log_access(self, config_id: int, action: str, user_id: Optional[int] = None):
        """记录配置访问日志"""
        log = ConfigAccessLog(
            config_id=config_id,
            action=action,
            user_id=user_id
        )
        
        self.db.add(log)
        self.db.commit()
    
    def export_configs(self, category: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """导出配置"""
        query = self.db.query(Config)
        
        if category:
            query = query.filter(Config.category == category)
        if environment:
            query = query.filter(Config.environment == environment)
        
        configs = query.all()
        
        export_data = {
            "configs": [],
            "templates": [],
            "groups": [],
            "export_time": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        for config in configs:
            config_dict = {
                "key": config.key,
                "value": config.value if not config.is_encrypted else "[ENCRYPTED]",
                "description": config.description,
                "category": config.category,
                "environment": config.environment,
                "is_encrypted": config.is_encrypted,
                "is_sensitive": config.is_sensitive
            }
            export_data["configs"].append(config_dict)
        
        return export_data
    
    def import_configs(self, import_data: Dict[str, Any], overwrite: bool = False) -> int:
        """导入配置"""
        imported_count = 0
        
        for config_data in import_data.get("configs", []):
            key = config_data.get("key")
            if not key:
                continue
            
            # 检查是否已存在
            existing_config = self.db.query(Config).filter(Config.key == key).first()
            
            if existing_config and not overwrite:
                continue
            
            if existing_config:
                # 更新现有配置
                config_update = ConfigUpdate(
                    value=config_data.get("value", ""),
                    description=config_data.get("description"),
                    category=config_data.get("category", "custom"),
                    environment=config_data.get("environment", "development"),
                    is_encrypted=config_data.get("is_encrypted", False),
                    is_sensitive=config_data.get("is_sensitive", False)
                )
                self.update_config(existing_config.id, config_update)
            else:
                # 创建新配置
                config_create = ConfigCreate(
                    key=key,
                    value=config_data.get("value", ""),
                    description=config_data.get("description"),
                    category=config_data.get("category", "custom"),
                    environment=config_data.get("environment", "development"),
                    is_encrypted=config_data.get("is_encrypted", False),
                    is_sensitive=config_data.get("is_sensitive", False)
                )
                self.set_config(config_create)
            
            imported_count += 1
        
        logger.info(f"导入配置完成，共导入 {imported_count} 个配置项")
        return imported_count
