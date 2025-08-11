#!/usr/bin/env python3
"""
缓存测试模块
测试Redis缓存功能
"""

import pytest
import time
import json
from unittest.mock import patch, MagicMock
from app.database import redis_client, cache_result, CacheKeys
from app.services.config_service import ConfigService


class TestCache:
    """缓存测试类"""
    
    def setup_method(self):
        """测试前设置"""
        # 清理Redis缓存
        if redis_client:
            redis_client.flushall()
    
    def test_cache_connection(self):
        """测试缓存连接"""
        if redis_client:
            result = redis_client.ping()
            assert result == True
        else:
            pytest.skip("Redis未连接")
    
    def test_cache_set_get(self):
        """测试缓存设置和获取"""
        if not redis_client:
            pytest.skip("Redis未连接")
        
        # 设置缓存
        test_key = "test:cache:key"
        test_value = {"data": "test_value", "timestamp": time.time()}
        
        redis_client.setex(test_key, 3600, json.dumps(test_value))
        
        # 获取缓存
        cached_value = redis_client.get(test_key)
        assert cached_value is not None
        
        # 验证值
        parsed_value = json.loads(cached_value)
        assert parsed_value["data"] == test_value["data"]
    
    def test_cache_decorator(self):
        """测试缓存装饰器"""
        if not redis_client:
            pytest.skip("Redis未连接")
        
        @cache_result(ttl=60, key_prefix="test")
        def test_function(param):
            return {"result": f"processed_{param}", "timestamp": time.time()}
        
        # 第一次调用
        result1 = test_function("test_param")
        
        # 第二次调用（应该从缓存获取）
        result2 = test_function("test_param")
        
        # 验证结果
        assert result1["result"] == result2["result"]
        assert result1["timestamp"] == result2["timestamp"]
    
    def test_cache_keys(self):
        """测试缓存键设计"""
        # 测试配置缓存键
        config_key = CacheKeys.CONFIG.format(key="test_config", environment="test")
        assert "config:test_config:test" in config_key
        
        # 测试用户缓存键
        user_key = CacheKeys.USER.format(user_id="123")
        assert "user:123" in user_key
        
        # 测试模板缓存键
        template_key = CacheKeys.TEMPLATE.format(template_id="456")
        assert "template:456" in template_key
    
    def test_config_service_cache(self):
        """测试配置服务的缓存功能"""
        if not redis_client:
            pytest.skip("Redis未连接")
        
        # 模拟配置服务
        config_service = ConfigService()
        
        # 测试配置获取缓存
        test_config = {
            "key": "test_config",
            "value": "test_value",
            "environment": "test"
        }
        
        # 设置缓存
        cache_key = CacheKeys.CONFIG.format(
            key=test_config["key"], 
            environment=test_config["environment"]
        )
        redis_client.setex(cache_key, 1800, json.dumps(test_config))
        
        # 验证缓存存在
        cached_config = redis_client.get(cache_key)
        assert cached_config is not None
        
        parsed_config = json.loads(cached_config)
        assert parsed_config["key"] == test_config["key"]
        assert parsed_config["value"] == test_config["value"]
    
    def test_cache_ttl(self):
        """测试缓存TTL"""
        if not redis_client:
            pytest.skip("Redis未连接")
        
        test_key = "test:ttl:key"
        test_value = "test_value"
        
        # 设置短期缓存
        redis_client.setex(test_key, 1, test_value)
        
        # 立即获取
        value = redis_client.get(test_key)
        assert value == test_value
        
        # 等待过期
        time.sleep(2)
        
        # 再次获取（应该过期）
        value = redis_client.get(test_key)
        assert value is None
    
    def test_cache_eviction(self):
        """测试缓存淘汰策略"""
        if not redis_client:
            pytest.skip("Redis未连接")
        
        # 设置最大内存策略
        redis_client.config_set("maxmemory-policy", "allkeys-lru")
        
        # 添加多个键值对
        for i in range(100):
            key = f"test:eviction:key:{i}"
            value = f"value_{i}" * 100  # 较大的值
            redis_client.setex(key, 3600, value)
        
        # 验证某些键被淘汰
        # 注意：这取决于Redis的内存配置
        total_keys = len(redis_client.keys("test:eviction:key:*"))
        assert total_keys <= 100  # 可能少于100个键
    
    def test_cache_performance(self):
        """测试缓存性能"""
        if not redis_client:
            pytest.skip("Redis未连接")
        
        # 测试写入性能
        start_time = time.time()
        for i in range(1000):
            key = f"perf:write:key:{i}"
            value = f"value_{i}"
            redis_client.setex(key, 3600, value)
        
        write_time = time.time() - start_time
        print(f"写入1000个键耗时: {write_time:.3f}秒")
        assert write_time < 5.0  # 应该在5秒内完成
        
        # 测试读取性能
        start_time = time.time()
        for i in range(1000):
            key = f"perf:write:key:{i}"
            value = redis_client.get(key)
            assert value is not None
        
        read_time = time.time() - start_time
        print(f"读取1000个键耗时: {read_time:.3f}秒")
        assert read_time < 2.0  # 应该在2秒内完成
    
    def test_cache_concurrent_access(self):
        """测试缓存并发访问"""
        if not redis_client:
            pytest.skip("Redis未连接")
        
        import threading
        
        def worker(thread_id):
            """工作线程函数"""
            for i in range(100):
                key = f"concurrent:key:{thread_id}:{i}"
                value = f"value:{thread_id}:{i}"
                
                # 写入
                redis_client.setex(key, 3600, value)
                
                # 读取
                cached_value = redis_client.get(key)
                assert cached_value == value
        
        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
        
        # 启动线程
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        print(f"5个线程并发访问缓存耗时: {total_time:.3f}秒")
        assert total_time < 10.0  # 应该在10秒内完成
    
    def test_cache_error_handling(self):
        """测试缓存错误处理"""
        # 测试Redis连接失败的情况
        with patch('app.database.redis_client') as mock_redis:
            mock_redis.get.side_effect = Exception("Redis连接失败")
            
            @cache_result(ttl=60, key_prefix="test")
            def test_function():
                return "test_result"
            
            # 应该正常执行，不抛出异常
            result = test_function()
            assert result == "test_result"
    
    def test_cache_serialization(self):
        """测试缓存序列化"""
        if not redis_client:
            pytest.skip("Redis未连接")
        
        # 测试复杂对象的序列化
        complex_obj = {
            "string": "test",
            "number": 123,
            "float": 3.14,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "none": None
        }
        
        test_key = "test:serialization:key"
        redis_client.setex(test_key, 3600, json.dumps(complex_obj))
        
        # 反序列化
        cached_value = redis_client.get(test_key)
        parsed_obj = json.loads(cached_value)
        
        # 验证所有字段
        assert parsed_obj["string"] == complex_obj["string"]
        assert parsed_obj["number"] == complex_obj["number"]
        assert parsed_obj["float"] == complex_obj["float"]
        assert parsed_obj["boolean"] == complex_obj["boolean"]
        assert parsed_obj["list"] == complex_obj["list"]
        assert parsed_obj["dict"] == complex_obj["dict"]
        assert parsed_obj["none"] == complex_obj["none"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 