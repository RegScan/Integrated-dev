import pytest
import asyncio
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.services.config_service import ConfigService
from app.schemas.config_schema import (
    ConfigCreate, ConfigUpdate, ConfigQuery, 
    ConfigCategory, Environment
)
from app.models.config import Config

# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """测试数据库会话"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

class TestConfigService:
    """配置服务测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        # 创建数据库表
        Base.metadata.create_all(bind=engine)
        yield
        # 清理数据库
        Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture
    def db_session(self):
        """数据库会话"""
        return next(override_get_db())
    
    @pytest.fixture
    def config_service(self, db_session):
        """配置服务实例"""
        return ConfigService(db_session, "configs/test.yaml")
    
    def test_create_config(self, config_service):
        """测试创建配置"""
        config_data = ConfigCreate(
            key="test.database.host",
            value="localhost",
            description="测试数据库主机",
            category=ConfigCategory.DATABASE,
            environment=Environment.TESTING,
            is_encrypted=False,
            is_sensitive=False
        )
        
        config = config_service.set_config(config_data)
        
        assert config.key == "test.database.host"
        assert config.value == "localhost"
        assert config.category == ConfigCategory.DATABASE
        assert config.environment == Environment.TESTING
        assert not config.is_encrypted
        assert not config.is_sensitive
    
    def test_create_encrypted_config(self, config_service):
        """测试创建加密配置"""
        config_data = ConfigCreate(
            key="test.api.key",
            value="secret-api-key",
            description="测试API密钥",
            category=ConfigCategory.API,
            environment=Environment.TESTING,
            is_encrypted=True,
            is_sensitive=True
        )
        
        config = config_service.set_config(config_data)
        
        assert config.key == "test.api.key"
        assert config.is_encrypted
        assert config.is_sensitive
        # 由于没有设置加密密钥，值不会被加密
        # 验证能正确获取
        decrypted_value = config_service.get_config("test.api.key")
        assert decrypted_value == "secret-api-key"
    
    def test_get_config(self, config_service):
        """测试获取配置"""
        # 先创建配置
        config_data = ConfigCreate(
            key="test.service.timeout",
            value="30",
            description="测试服务超时",
            category=ConfigCategory.SYSTEM,
            environment=Environment.TESTING
        )
        config_service.set_config(config_data)
        
        # 获取配置
        value = config_service.get_config("test.service.timeout")
        assert value == "30"
        
        # 获取不存在的配置
        value = config_service.get_config("nonexistent.key", default="default")
        assert value == "default"
    
    def test_update_config(self, config_service):
        """测试更新配置"""
        # 先创建配置
        config_data = ConfigCreate(
            key="test.database.port",
            value="5432",
            description="数据库端口",
            category=ConfigCategory.DATABASE,
            environment=Environment.TESTING
        )
        config = config_service.set_config(config_data)
        
        # 更新配置
        update_data = ConfigUpdate(
            value="5433",
            description="更新的数据库端口"
        )
        updated_config = config_service.update_config(config.id, update_data)
        
        assert updated_config.value == "5433"
        assert updated_config.description == "更新的数据库端口"
        
        # 验证值已更新
        value = config_service.get_config("test.database.port")
        assert value == "5433"
    
    def test_delete_config(self, config_service):
        """测试删除配置"""
        # 先创建配置
        config_data = ConfigCreate(
            key="test.temp.config",
            value="temp_value",
            description="临时配置",
            category=ConfigCategory.CUSTOM,
            environment=Environment.TESTING
        )
        config = config_service.set_config(config_data)
        
        # 删除配置
        success = config_service.delete_config(config.id)
        assert success
        
        # 验证配置已删除
        value = config_service.get_config("test.temp.config")
        assert value is None
    
    def test_get_configs_with_filter(self, config_service):
        """测试带过滤条件的配置查询"""
        # 创建多个配置
        configs_data = [
            ConfigCreate(key="test.db.host", value="localhost", category=ConfigCategory.DATABASE, environment=Environment.TESTING),
            ConfigCreate(key="test.db.port", value="5432", category=ConfigCategory.DATABASE, environment=Environment.TESTING),
            ConfigCreate(key="test.api.key", value="api-key", category=ConfigCategory.API, environment=Environment.TESTING),
            ConfigCreate(key="prod.db.host", value="prod-host", category=ConfigCategory.DATABASE, environment=Environment.PRODUCTION)
        ]
        
        for config_data in configs_data:
            config_service.set_config(config_data)
        
        # 测试按分类过滤
        query = ConfigQuery(category=ConfigCategory.DATABASE, limit=10, offset=0)
        configs = config_service.get_configs(query)
        assert len(configs) == 3  # 2个test + 1个prod
        
        # 测试按环境过滤
        query = ConfigQuery(environment=Environment.TESTING, limit=10, offset=0)
        configs = config_service.get_configs(query)
        assert len(configs) == 3  # 3个test环境配置
        
        # 测试分页
        query = ConfigQuery(limit=2, offset=0)
        configs = config_service.get_configs(query)
        assert len(configs) == 2
    
    def test_config_stats(self, config_service):
        """测试配置统计"""
        # 创建测试配置
        configs_data = [
            ConfigCreate(key="test.db.host", value="localhost", category=ConfigCategory.DATABASE, environment=Environment.TESTING),
            ConfigCreate(key="test.api.key", value="api-key", category=ConfigCategory.API, environment=Environment.TESTING, is_encrypted=True),
            ConfigCreate(key="test.service.timeout", value="30", category=ConfigCategory.SYSTEM, environment=Environment.TESTING)
        ]
        
        for config_data in configs_data:
            config_service.set_config(config_data)
        
        # 获取统计信息
        stats = config_service.get_config_stats()
        
        assert stats.total_configs == 3
        assert stats.encrypted_configs == 1
        assert stats.sensitive_configs == 0  # 由于没有加密密钥，敏感配置不会被标记为敏感
        assert "database" in stats.configs_by_category
        assert "api" in stats.configs_by_category
        assert "system" in stats.configs_by_category
    
    def test_batch_update_configs(self, config_service):
        """测试批量更新配置"""
        # 先创建一些配置
        configs_data = [
            ConfigCreate(key="batch.test1", value="value1", category=ConfigCategory.CUSTOM, environment=Environment.TESTING),
            ConfigCreate(key="batch.test2", value="value2", category=ConfigCategory.CUSTOM, environment=Environment.TESTING),
            ConfigCreate(key="batch.test3", value="value3", category=ConfigCategory.CUSTOM, environment=Environment.TESTING)
        ]
        
        for config_data in configs_data:
            config_service.set_config(config_data)
        
        # 批量更新
        from app.schemas.config_schema import BatchConfigUpdate
        batch_data = BatchConfigUpdate(
            configs=[
                {"key": "batch.test1", "value": "updated_value1"},
                {"key": "batch.test2", "value": "updated_value2"}
            ]
        )
        
        updated_configs = config_service.batch_update_configs(batch_data)
        assert len(updated_configs) == 2
        
        # 验证更新结果
        value1 = config_service.get_config("batch.test1")
        value2 = config_service.get_config("batch.test2")
        value3 = config_service.get_config("batch.test3")
        
        assert value1 == "updated_value1"
        assert value2 == "updated_value2"
        assert value3 == "value3"  # 未更新的保持不变

 