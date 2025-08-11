import pytest
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.schemas.config_schema import ConfigCategory, Environment

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

class TestSimpleAPI:
    """简化的API测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        # 创建数据库表
        Base.metadata.create_all(bind=engine)
        yield
        # 清理数据库
        Base.metadata.drop_all(bind=engine)
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查接口"""
        from app.main import app
        from app.database import get_db
        
        # 覆盖数据库依赖
        app.dependency_overrides[get_db] = override_get_db
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_create_config_api(self):
        """测试创建配置API"""
        from app.main import app
        from app.database import get_db
        
        # 覆盖数据库依赖
        app.dependency_overrides[get_db] = override_get_db
        
        config_data = {
            "key": "api.test.config",
            "value": "api_test_value",
            "description": "API测试配置",
            "category": ConfigCategory.CUSTOM,
            "environment": Environment.TESTING,
            "is_encrypted": False,
            "is_sensitive": False
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/config/", json=config_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["key"] == "api.test.config"
            assert data["value"] == "api_test_value"
    
    @pytest.mark.asyncio
    async def test_get_config_api(self):
        """测试获取配置API"""
        from app.main import app
        from app.database import get_db
        
        # 覆盖数据库依赖
        app.dependency_overrides[get_db] = override_get_db
        
        # 先创建配置
        config_data = {
            "key": "api.get.test",
            "value": "get_test_value",
            "description": "获取测试配置",
            "category": ConfigCategory.CUSTOM,
            "environment": Environment.TESTING
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # 创建配置
            create_response = await client.post("/api/v1/config/", json=config_data)
            assert create_response.status_code == 200
            
            # 获取配置
            response = await client.get("/api/v1/config/api.get.test")
            assert response.status_code == 200
            
            data = response.json()
            assert data["key"] == "api.get.test"
            assert data["value"] == "get_test_value"
    
    @pytest.mark.asyncio
    async def test_update_config_api(self):
        """测试更新配置API"""
        from app.main import app
        from app.database import get_db
        
        # 覆盖数据库依赖
        app.dependency_overrides[get_db] = override_get_db
        
        # 先创建配置
        config_data = {
            "key": "api.update.test",
            "value": "original_value",
            "description": "原始配置",
            "category": ConfigCategory.CUSTOM,
            "environment": Environment.TESTING
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # 创建配置
            create_response = await client.post("/api/v1/config/", json=config_data)
            assert create_response.status_code == 200
            config_id = create_response.json()["id"]
            
            # 更新配置
            update_data = {
                "value": "updated_value",
                "description": "更新的配置"
            }
            
            response = await client.put(f"/api/v1/config/{config_id}", json=update_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["value"] == "updated_value"
            assert data["description"] == "更新的配置"
    
    @pytest.mark.asyncio
    async def test_delete_config_api(self):
        """测试删除配置API"""
        from app.main import app
        from app.database import get_db
        
        # 覆盖数据库依赖
        app.dependency_overrides[get_db] = override_get_db
        
        # 先创建配置
        config_data = {
            "key": "api.delete.test",
            "value": "delete_test_value",
            "description": "删除测试配置",
            "category": ConfigCategory.CUSTOM,
            "environment": Environment.TESTING
        }
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # 创建配置
            create_response = await client.post("/api/v1/config/", json=config_data)
            assert create_response.status_code == 200
            config_id = create_response.json()["id"]
            
            # 删除配置
            response = await client.delete(f"/api/v1/config/{config_id}")
            assert response.status_code == 200
            
            # 验证配置已删除
            get_response = await client.get("/api/v1/config/api.delete.test")
            assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_configs_list_api(self):
        """测试获取配置列表API"""
        from app.main import app
        from app.database import get_db
        
        # 覆盖数据库依赖
        app.dependency_overrides[get_db] = override_get_db
        
        # 创建多个配置
        configs_data = [
            {"key": "list.test1", "value": "value1", "category": ConfigCategory.CUSTOM, "environment": Environment.TESTING},
            {"key": "list.test2", "value": "value2", "category": ConfigCategory.CUSTOM, "environment": Environment.TESTING},
            {"key": "list.test3", "value": "value3", "category": ConfigCategory.CUSTOM, "environment": Environment.TESTING}
        ]
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # 创建配置
            for config_data in configs_data:
                response = await client.post("/api/v1/config/", json=config_data)
                assert response.status_code == 200
            
            # 获取配置列表
            response = await client.get("/api/v1/config/")
            assert response.status_code == 200
            
            data = response.json()
            assert len(data) >= 3
    
    @pytest.mark.asyncio
    async def test_config_stats_api(self):
        """测试配置统计API"""
        from app.main import app
        from app.database import get_db
        
        # 覆盖数据库依赖
        app.dependency_overrides[get_db] = override_get_db
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/config/stats/overview")
            assert response.status_code == 200
            
            data = response.json()
            assert "total_configs" in data
            assert "encrypted_configs" in data
            assert "sensitive_configs" in data
            assert "configs_by_category" in data 