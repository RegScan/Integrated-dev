from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class ConfigAction(str, Enum):
    """配置操作类型"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"

class ConfigCategory(str, Enum):
    """配置分类"""
    SYSTEM = "system"
    DATABASE = "database"
    API = "api"
    SECURITY = "security"
    NOTIFICATION = "notification"
    SCANNER = "scanner"
    SCHEDULER = "scheduler"
    MONITORING = "monitoring"
    LOGGING = "logging"
    CUSTOM = "custom"

class Environment(str, Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

# 基础配置模型
class ConfigBase(BaseModel):
    key: str = Field(..., description="配置键名", max_length=255)
    value: str = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    category: ConfigCategory = Field(ConfigCategory.CUSTOM, description="配置分类")
    environment: Environment = Field(Environment.DEVELOPMENT, description="环境")
    is_encrypted: bool = Field(False, description="是否加密")
    is_sensitive: bool = Field(False, description="是否敏感信息")

# 创建配置模型
class ConfigCreate(ConfigBase):
    pass

# 更新配置模型
class ConfigUpdate(BaseModel):
    value: Optional[str] = Field(None, description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    category: Optional[ConfigCategory] = Field(None, description="配置分类")
    environment: Optional[Environment] = Field(None, description="环境")
    is_encrypted: Optional[bool] = Field(None, description="是否加密")
    is_sensitive: Optional[bool] = Field(None, description="是否敏感信息")

# 配置响应模型
class ConfigResponse(ConfigBase):
    id: int
    owner_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# 配置版本模型
class ConfigVersionBase(BaseModel):
    version: int = Field(..., description="版本号")
    value: str = Field(..., description="配置值")
    change_reason: Optional[str] = Field(None, description="变更原因")

class ConfigVersionCreate(ConfigVersionBase):
    pass

class ConfigVersionResponse(ConfigVersionBase):
    id: int
    config_id: int
    user_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 配置模板模型
class ConfigTemplateBase(BaseModel):
    name: str = Field(..., description="模板名称", max_length=100)
    description: Optional[str] = Field(None, description="模板描述")
    template_data: Dict[str, Any] = Field(..., description="模板数据")
    category: ConfigCategory = Field(ConfigCategory.CUSTOM, description="模板分类")
    is_active: bool = Field(True, description="是否激活")

class ConfigTemplateCreate(ConfigTemplateBase):
    pass

class ConfigTemplateUpdate(BaseModel):
    description: Optional[str] = Field(None, description="模板描述")
    template_data: Optional[Dict[str, Any]] = Field(None, description="模板数据")
    category: Optional[ConfigCategory] = Field(None, description="模板分类")
    is_active: Optional[bool] = Field(None, description="是否激活")

class ConfigTemplateResponse(ConfigTemplateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# 配置组模型
class ConfigGroupBase(BaseModel):
    name: str = Field(..., description="组名称", max_length=100)
    description: Optional[str] = Field(None, description="组描述")
    parent_group_id: Optional[int] = Field(None, description="父组ID")

class ConfigGroupCreate(ConfigGroupBase):
    pass

class ConfigGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, description="组名称", max_length=100)
    description: Optional[str] = Field(None, description="组描述")
    parent_group_id: Optional[int] = Field(None, description="父组ID")

class ConfigGroupResponse(ConfigGroupBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# 配置访问日志模型
class ConfigAccessLogBase(BaseModel):
    config_id: int = Field(..., description="配置ID")
    action: ConfigAction = Field(..., description="操作类型")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")

class ConfigAccessLogCreate(ConfigAccessLogBase):
    pass

class ConfigAccessLogResponse(ConfigAccessLogBase):
    id: int
    user_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 批量操作模型
class BatchConfigUpdate(BaseModel):
    configs: List[Dict[str, Any]] = Field(..., description="批量配置更新列表")
    
    @validator('configs')
    def validate_configs(cls, v):
        for config in v:
            if 'key' not in config or 'value' not in config:
                raise ValueError("每个配置项必须包含key和value字段")
        return v

# 配置查询模型
class ConfigQuery(BaseModel):
    key: Optional[str] = Field(None, description="配置键名")
    category: Optional[ConfigCategory] = Field(None, description="配置分类")
    environment: Optional[Environment] = Field(None, description="环境")
    is_encrypted: Optional[bool] = Field(None, description="是否加密")
    is_sensitive: Optional[bool] = Field(None, description="是否敏感信息")
    limit: int = Field(100, description="返回数量限制", ge=1, le=1000)
    offset: int = Field(0, description="偏移量", ge=0)

# 配置统计模型
class ConfigStats(BaseModel):
    total_configs: int
    encrypted_configs: int
    sensitive_configs: int
    configs_by_category: Dict[str, int]
    configs_by_environment: Dict[str, int]
    recent_updates: List[ConfigResponse]

# 配置导入导出模型
class ConfigExport(BaseModel):
    configs: List[ConfigResponse]
    templates: List[ConfigTemplateResponse]
    groups: List[ConfigGroupResponse]
    export_time: datetime
    version: str = "1.0"

class ConfigImport(BaseModel):
    configs: List[ConfigCreate]
    templates: List[ConfigTemplateCreate]
    groups: List[ConfigGroupCreate]
    overwrite: bool = Field(False, description="是否覆盖现有配置")
