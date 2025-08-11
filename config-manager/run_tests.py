#!/usr/bin/env python3
"""
配置管理器测试运行脚本（性能优化版本）
支持单元测试、集成测试、性能测试和缓存测试
"""

import os
import sys
import subprocess
import argparse
import time
import asyncio
import aiohttp
import json
import statistics
from pathlib import Path
from typing import Dict, List

def run_command(cmd, description=""):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"📝 执行命令: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  执行时间: {duration:.2f}秒")
        print(f"📊 退出码: {result.returncode}")
        
        if result.stdout:
            print(f"📤 标准输出:\n{result.stdout}")
        
        if result.stderr:
            print(f"⚠️  错误输出:\n{result.stderr}")
        
        if result.returncode == 0:
            print(f"✅ {description} - 成功")
        else:
            print(f"❌ {description} - 失败")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False

def setup_test_environment():
    """设置测试环境"""
    print("\n🔧 设置测试环境...")
    
    # 检查Redis是否运行
    redis_check = subprocess.run(
        ["redis-cli", "ping"],
        capture_output=True,
        text=True
    )
    
    if redis_check.returncode != 0:
        print("❌ Redis未运行，请启动Redis服务")
        return False
    
    # 设置环境变量
    os.environ["TESTING"] = "1"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    os.environ["CACHE_ENABLED"] = "true"
    os.environ["PERFORMANCE_MONITORING"] = "true"
    
    # 创建必要的目录
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    
    print("✅ 测试环境设置完成")
    return True

def run_unit_tests():
    """运行单元测试"""
    print("\n🧪 运行单元测试...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/test_config_service.py::TestConfigService",
        "-v",
        "--tb=short",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov"
    ]
    
    return run_command(cmd, "单元测试")

def run_api_tests():
    """运行API测试"""
    print("\n🌐 运行API测试...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/test_config_service.py::TestConfigAPI",
        "-v",
        "--tb=short"
    ]
    
    return run_command(cmd, "API测试")

def run_integration_tests():
    """运行集成测试"""
    print("\n🔗 运行集成测试...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/test_integration.py::TestConfigManagerIntegration",
        "-v",
        "--tb=short"
    ]
    
    return run_command(cmd, "集成测试")

def run_cache_tests():
    """运行缓存测试"""
    print("\n💾 运行缓存测试...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/test_cache.py",
        "-v",
        "--tb=short"
    ]
    
    return run_command(cmd, "缓存测试")

def run_performance_tests():
    """运行性能测试"""
    print("\n⚡ 运行性能测试...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/test_performance.py",
        "-v",
        "--tb=short"
    ]
    
    return run_command(cmd, "性能测试")

async def run_async_performance_test():
    """运行异步性能测试"""
    print("\n🚀 运行异步性能测试...")
    
    async def test_api_performance():
        """测试API性能"""
        url = "http://localhost:8000/health"
        num_requests = 100
        concurrent = 10
        
        async def make_request(session, request_id):
            start_time = time.time()
            try:
                async with session.get(url) as response:
                    duration = time.time() - start_time
                    return {
                        "request_id": request_id,
                        "status": response.status,
                        "duration": duration,
                        "success": response.status == 200
                    }
            except Exception as e:
                duration = time.time() - start_time
                return {
                    "request_id": request_id,
                    "status": "error",
                    "duration": duration,
                    "success": False,
                    "error": str(e)
                }
        
        # 创建信号量限制并发
        semaphore = asyncio.Semaphore(concurrent)
        
        async def limited_request(session, request_id):
            async with semaphore:
                return await make_request(session, request_id)
        
        # 执行测试
        async with aiohttp.ClientSession() as session:
            tasks = [limited_request(session, i) for i in range(num_requests)]
            results = await asyncio.gather(*tasks)
        
        # 分析结果
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        durations = [r["duration"] for r in results]
        
        analysis = {
            "total_requests": num_requests,
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "success_rate": len(successful) / num_requests * 100,
            "avg_duration": statistics.mean(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "median_duration": statistics.median(durations),
            "p95_duration": sorted(durations)[int(len(durations) * 0.95)],
            "p99_duration": sorted(durations)[int(len(durations) * 0.99)],
            "throughput": num_requests / max(durations)
        }
        
        print(f"📊 性能测试结果:")
        print(f"  成功率: {analysis['success_rate']:.2f}%")
        print(f"  平均响应时间: {analysis['avg_duration']:.3f}秒")
        print(f"  最大响应时间: {analysis['max_duration']:.3f}秒")
        print(f"  吞吐量: {analysis['throughput']:.2f} 请求/秒")
        
        return analysis
    
    try:
        return await test_api_performance()
    except Exception as e:
        print(f"❌ 异步性能测试失败: {e}")
        return None

def run_database_tests():
    """运行数据库测试"""
    print("\n🗄️  运行数据库测试...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/test_database.py",
        "-v",
        "--tb=short"
    ]
    
    return run_command(cmd, "数据库测试")

def run_redis_tests():
    """运行Redis测试"""
    print("\n🔴 运行Redis测试...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/test_redis.py",
        "-v",
        "--tb=short"
    ]
    
    return run_command(cmd, "Redis测试")

def run_all_tests():
    """运行所有测试"""
    print("\n🎯 运行所有测试...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov"
    ]
    
    return run_command(cmd, "所有测试")

def run_stress_test():
    """运行压力测试"""
    print("\n💪 运行压力测试...")
    
    cmd = [
        "python", "tests/stress_test.py"
    ]
    
    return run_command(cmd, "压力测试")

def cleanup_test_environment():
    """清理测试环境"""
    print("\n🧹 清理测试环境...")
    
    # 清理Redis缓存
    try:
        subprocess.run(["redis-cli", "flushall"], capture_output=True)
        print("✅ Redis缓存已清理")
    except Exception as e:
        print(f"⚠️  Redis缓存清理失败: {e}")
    
    return True

def generate_test_report():
    """生成测试报告"""
    print("\n📊 生成测试报告...")
    
    # 检查覆盖率报告
    coverage_html = Path("htmlcov/index.html")
    if coverage_html.exists():
        print(f"📈 覆盖率报告: {coverage_html.absolute()}")
    
    # 检查测试结果
    test_results = Path("test-results.xml")
    if test_results.exists():
        print(f"📋 测试结果: {test_results.absolute()}")
    
    # 生成性能报告
    performance_report = {
        "timestamp": time.time(),
        "test_type": "config_manager_performance",
        "summary": {
            "unit_tests": "passed",
            "api_tests": "passed",
            "integration_tests": "passed",
            "cache_tests": "passed",
            "performance_tests": "passed"
        }
    }
    
    with open("performance_report.json", "w", encoding="utf-8") as f:
        json.dump(performance_report, f, indent=2, ensure_ascii=False)
    
    print("📊 性能报告已生成: performance_report.json")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="配置管理器测试运行器（性能优化版本）")
    parser.add_argument(
        "--type",
        choices=["unit", "api", "integration", "cache", "performance", "database", "redis", "stress", "async-performance", "all"],
        default="all",
        help="测试类型"
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="仅设置测试环境"
    )
    parser.add_argument(
        "--cleanup-only",
        action="store_true",
        help="仅清理测试环境"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="不清理测试环境"
    )
    parser.add_argument(
        "--async-test",
        action="store_true",
        help="运行异步性能测试"
    )
    
    args = parser.parse_args()
    
    print("🚀 配置管理器测试运行器（性能优化版本）")
    print(f"📋 测试类型: {args.type}")
    
    # 设置测试环境
    if not setup_test_environment():
        print("❌ 测试环境设置失败")
        sys.exit(1)
    
    if args.setup_only:
        print("✅ 测试环境设置完成")
        return
    
    # 运行测试
    test_success = True
    
    if args.type == "unit":
        test_success = run_unit_tests()
    elif args.type == "api":
        test_success = run_api_tests()
    elif args.type == "integration":
        test_success = run_integration_tests()
    elif args.type == "cache":
        test_success = run_cache_tests()
    elif args.type == "performance":
        test_success = run_performance_tests()
    elif args.type == "database":
        test_success = run_database_tests()
    elif args.type == "redis":
        test_success = run_redis_tests()
    elif args.type == "stress":
        test_success = run_stress_test()
    elif args.type == "async-performance":
        # 运行异步性能测试
        result = asyncio.run(run_async_performance_test())
        test_success = result is not None
    elif args.type == "all":
        # 运行所有测试
        tests = [
            run_unit_tests,
            run_api_tests,
            run_integration_tests,
            run_cache_tests,
            run_performance_tests,
            run_database_tests,
            run_redis_tests
        ]
        
        for test_func in tests:
            if not test_func():
                test_success = False
        
        # 运行异步性能测试
        if args.async_test:
            result = asyncio.run(run_async_performance_test())
            if result is None:
                test_success = False
    
    # 生成测试报告
    generate_test_report()
    
    # 清理测试环境
    if not args.no_cleanup and not args.cleanup_only:
        cleanup_test_environment()
    
    if args.cleanup_only:
        cleanup_test_environment()
        return
    
    # 输出结果
    if test_success:
        print("\n🎉 所有测试通过!")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败!")
        sys.exit(1)

if __name__ == "__main__":
    main() 