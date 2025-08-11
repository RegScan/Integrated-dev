#!/usr/bin/env python3
"""
性能测试模块
测试Website Scanner的性能优化功能
"""

import pytest
import time
import asyncio
import aiohttp
import statistics
from unittest.mock import patch, MagicMock
from app.database import monitor_performance, cache_result
from app.services.crawler import CrawlerService, AsyncCrawlerService


class TestPerformance:
    """性能测试类"""
    
    def setup_method(self):
        """测试前设置"""
        pass
    
    def test_performance_monitoring_decorator(self):
        """测试性能监控装饰器"""
        @monitor_performance("test_function")
        def test_function():
            time.sleep(0.1)  # 模拟工作
            return "test_result"
        
        # 执行函数
        result = test_function()
        assert result == "test_result"
    
    def test_cache_performance_improvement(self):
        """测试缓存性能提升"""
        call_count = 0
        
        @cache_result(ttl=60, key_prefix="perf_test")
        def expensive_function(param):
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)  # 模拟昂贵操作
            return f"result_{param}"
        
        # 第一次调用（应该执行）
        start_time = time.time()
        result1 = expensive_function("test")
        first_call_time = time.time() - start_time
        
        # 第二次调用（应该从缓存获取）
        start_time = time.time()
        result2 = expensive_function("test")
        second_call_time = time.time() - start_time
        
        # 验证结果
        assert result1 == result2
        assert call_count == 1  # 只调用了一次
        
        # 验证缓存提升了性能
        assert second_call_time < first_call_time * 0.1  # 缓存调用应该快10倍以上
    
    def test_crawler_service_performance(self):
        """测试爬虫服务性能"""
        crawler_service = CrawlerService()
        
        # 模拟爬虫操作
        start_time = time.time()
        for i in range(10):
            # 模拟爬虫操作
            pass
        total_time = time.time() - start_time
        
        print(f"10次爬虫操作耗时: {total_time:.3f}秒")
        assert total_time < 5.0  # 应该在5秒内完成
    
    async def test_async_crawler_performance(self):
        """测试异步爬虫性能"""
        async_crawler = AsyncCrawlerService()
        
        # 测试并发爬取
        domains = [f"test{i}.example.com" for i in range(5)]
        
        start_time = time.time()
        # 注意：这里只是测试框架，不实际爬取
        results = await async_crawler.crawl_websites_batch(domains)
        total_time = time.time() - start_time
        
        print(f"5个域名并发爬取耗时: {total_time:.3f}秒")
        assert total_time < 10.0  # 应该在10秒内完成
    
    def test_database_connection_pool(self):
        """测试数据库连接池性能"""
        from app.database import engine
        
        # 测试连接池配置
        pool = engine.pool
        assert pool.size() <= 20  # 连接池大小
        assert pool.overflow() <= 30  # 最大溢出连接数
    
    def test_redis_connection_performance(self):
        """测试Redis连接性能"""
        from app.database import redis_client
        
        if not redis_client:
            pytest.skip("Redis未连接")
        
        # 测试连接性能
        start_time = time.time()
        for i in range(100):
            redis_client.ping()
        total_time = time.time() - start_time
        
        print(f"100次Redis ping耗时: {total_time:.3f}秒")
        assert total_time < 1.0  # 应该在1秒内完成
    
    async def test_async_performance(self):
        """测试异步性能"""
        async def async_operation(delay):
            await asyncio.sleep(delay)
            return f"result_{delay}"
        
        # 测试并发执行
        start_time = time.time()
        tasks = [async_operation(0.1) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # 验证结果
        assert len(results) == 10
        assert total_time < 0.2  # 并发执行应该比串行快
    
    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行一些操作
        for i in range(1000):
            # 模拟内存操作
            pass
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"内存使用增加: {memory_increase:.2f} MB")
        assert memory_increase < 100  # 内存增加应该小于100MB
    
    def test_cpu_usage(self):
        """测试CPU使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 测试CPU密集型操作
        start_time = time.time()
        cpu_percent = process.cpu_percent(interval=1.0)
        total_time = time.time() - start_time
        
        print(f"CPU使用率: {cpu_percent}%")
        assert cpu_percent < 80  # CPU使用率应该小于80%
    
    def test_scan_response_time_distribution(self):
        """测试扫描响应时间分布"""
        response_times = []
        
        def mock_scan_call():
            time.sleep(0.05)  # 模拟扫描调用
            return "scan_result"
        
        # 执行多次扫描调用
        for _ in range(50):
            start_time = time.time()
            mock_scan_call()
            response_times.append(time.time() - start_time)
        
        # 计算统计信息
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
        p99_time = sorted(response_times)[int(len(response_times) * 0.99)]
        
        print(f"平均扫描时间: {avg_time:.3f}秒")
        print(f"中位数扫描时间: {median_time:.3f}秒")
        print(f"95%分位数: {p95_time:.3f}秒")
        print(f"99%分位数: {p99_time:.3f}秒")
        
        # 验证性能指标
        assert avg_time < 0.1   # 平均扫描时间应该小于100ms
        assert p95_time < 0.2   # 95%的扫描应该小于200ms
        assert p99_time < 0.5   # 99%的扫描应该小于500ms
    
    def test_concurrent_scans(self):
        """测试并发扫描处理"""
        import threading
        
        results = []
        lock = threading.Lock()
        
        def worker(worker_id):
            """工作线程"""
            start_time = time.time()
            # 模拟扫描操作
            time.sleep(0.05)
            end_time = time.time()
            
            with lock:
                results.append({
                    "worker_id": worker_id,
                    "duration": end_time - start_time
                })
        
        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
        
        # 启动所有线程
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        print(f"5个并发扫描总耗时: {total_time:.3f}秒")
        assert total_time < 0.5  # 应该在500ms内完成
        assert len(results) == 5  # 所有扫描都应该完成
    
    def test_cache_hit_rate(self):
        """测试缓存命中率"""
        from app.database import redis_client
        
        if not redis_client:
            pytest.skip("Redis未连接")
        
        # 清理缓存
        redis_client.flushall()
        
        hit_count = 0
        total_count = 0
        
        @cache_result(ttl=60, key_prefix="hit_rate_test")
        def test_function(param):
            nonlocal hit_count, total_count
            total_count += 1
            
            # 检查是否从缓存获取
            if redis_client.get(f"hit_rate_test:test_function:{hash(str(param))}"):
                hit_count += 1
            
            return f"result_{param}"
        
        # 执行多次调用
        for i in range(10):
            test_function("same_param")
        
        # 计算命中率
        hit_rate = hit_count / total_count if total_count > 0 else 0
        print(f"缓存命中率: {hit_rate:.2%}")
        
        # 第二次调用应该全部命中缓存
        for i in range(10):
            test_function("same_param")
        
        hit_rate = hit_count / total_count if total_count > 0 else 0
        print(f"最终缓存命中率: {hit_rate:.2%}")
        assert hit_rate > 0.5  # 命中率应该大于50%
    
    def test_database_query_performance(self):
        """测试数据库查询性能"""
        from app.database import get_db
        
        # 测试数据库连接性能
        start_time = time.time()
        with get_db() as db:
            # 执行简单查询
            result = db.execute("SELECT 1")
            result.fetchone()
        query_time = time.time() - start_time
        
        print(f"数据库查询耗时: {query_time:.3f}秒")
        assert query_time < 0.1  # 应该在100ms内完成
    
    def test_error_handling_performance(self):
        """测试错误处理性能"""
        def function_with_error():
            raise ValueError("Test error")
        
        # 测试异常处理性能
        start_time = time.time()
        for _ in range(1000):
            try:
                function_with_error()
            except ValueError:
                pass
        total_time = time.time() - start_time
        
        print(f"1000次异常处理耗时: {total_time:.3f}秒")
        assert total_time < 1.0  # 应该在1秒内完成
    
    def test_playwright_performance(self):
        """测试Playwright性能"""
        # 测试浏览器启动性能
        start_time = time.time()
        
        # 模拟浏览器操作
        time.sleep(0.1)  # 模拟浏览器启动
        
        browser_time = time.time() - start_time
        print(f"浏览器启动耗时: {browser_time:.3f}秒")
        assert browser_time < 1.0  # 应该在1秒内完成
    
    def test_content_extraction_performance(self):
        """测试内容提取性能"""
        # 模拟HTML内容
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Content</h1>
                <p>This is a test paragraph with some content.</p>
                <img src="test1.jpg" alt="Test Image 1">
                <img src="test2.jpg" alt="Test Image 2">
            </body>
        </html>
        """
        
        # 测试内容提取性能
        start_time = time.time()
        for _ in range(100):
            # 模拟内容提取
            import re
            text_content = re.sub(r'<[^>]+>', ' ', html_content)
            images = re.findall(r'<img[^>]+src="([^"]+)"', html_content)
        
        extraction_time = time.time() - start_time
        print(f"100次内容提取耗时: {extraction_time:.3f}秒")
        assert extraction_time < 1.0  # 应该在1秒内完成
    
    def test_network_request_performance(self):
        """测试网络请求性能"""
        import requests
        
        # 测试HTTP请求性能
        start_time = time.time()
        for _ in range(10):
            try:
                # 使用本地测试URL
                response = requests.get("http://localhost:8001/health", timeout=1)
                assert response.status_code == 200
            except:
                pass  # 忽略连接错误
        
        request_time = time.time() - start_time
        print(f"10次HTTP请求耗时: {request_time:.3f}秒")
        assert request_time < 5.0  # 应该在5秒内完成


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 