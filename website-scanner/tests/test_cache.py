#!/usr/bin/env python3
"""
缓存测试模块
测试Website Scanner的Redis缓存功能
"""

import pytest
import time
import json
from unittest.mock import patch, MagicMock
from app.database import redis_client, cache_result, CacheKeys
from app.services.crawler import CrawlerService


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
        # 测试扫描结果缓存键
        scan_key = CacheKeys.SCAN_RESULT.format(domain="example.com")
        assert "scan:result:example.com" in scan_key
        
        # 测试备案信息缓存键
        beian_key = CacheKeys.BEIAN_INFO.format(domain="example.com")
        assert "beian:info:example.com" in beian_key
        
        # 测试网站信息缓存键
        website_key = CacheKeys.WEBSITE_INFO.format(domain="example.com")
        assert "website:info:example.com" in website_key
    
    def test_crawler_service_cache(self):
        """测试爬虫服务的缓存功能"""
        if not redis_client:
            pytest.skip("Redis未连接")
        
        # 模拟爬虫服务
        crawler_service = CrawlerService()
        
        # 测试扫描结果缓存
        test_scan_result = {
            "domain": "example.com",
            "text": "test content",
            "images": ["http://example.com/image1.jpg"],
            "url": "https://example.com",
            "title": "Test Page"
        }
        
        # 设置缓存
        cache_key = CacheKeys.SCAN_RESULT.format(domain="example.com")
        redis_client.setex(cache_key, 86400, json.dumps(test_scan_result))
        
        # 验证缓存存在
        cached_result = redis_client.get(cache_key)
        assert cached_result is not None
        
        parsed_result = json.loads(cached_result)
        assert parsed_result["domain"] == test_scan_result["domain"]
        assert parsed_result["text"] == test_scan_result["text"]
    
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
    
    def test_scan_result_cache(self):
        """测试扫描结果缓存"""
        if not redis_client:
            pytest.skip("Redis未连接")
        
        # 模拟扫描结果
        scan_result = {
            "domain": "example.com",
            "text": "This is a test page content",
            "images": [
                "http://example.com/image1.jpg",
                "http://example.com/image2.jpg"
            ],
            "url": "https://example.com",
            "title": "Example Domain",
            "crawl_time": time.time()
        }
        
        # 设置缓存
        cache_key = CacheKeys.SCAN_RESULT.format(domain="example.com")
        redis_client.setex(cache_key, 86400, json.dumps(scan_result))
        
        # 验证缓存
        cached_result = redis_client.get(cache_key)
        assert cached_result is not None
        
        parsed_result = json.loads(cached_result)
        assert parsed_result["domain"] == "example.com"
        assert len(parsed_result["images"]) == 2
        assert "crawl_time" in parsed_result
    
    def test_beian_info_cache(self):
        """测试备案信息缓存"""
        if not redis_client:
            pytest.skip("Redis未连接")
        
        # 模拟备案信息
        beian_info = {
            "domain": "example.com",
            "beian_number": "京ICP备12345678号",
            "company": "Example Company",
            "status": "active",
            "query_time": time.time()
        }
        
        # 设置缓存
        cache_key = CacheKeys.BEIAN_INFO.format(domain="example.com")
        redis_client.setex(cache_key, 604800, json.dumps(beian_info))
        
        # 验证缓存
        cached_info = redis_client.get(cache_key)
        assert cached_info is not None
        
        parsed_info = json.loads(cached_info)
        assert parsed_info["domain"] == "example.com"
        assert parsed_info["status"] == "active"
        assert "query_time" in parsed_info


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 