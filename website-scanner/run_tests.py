#!/usr/bin/env python3
"""
Website Scanner 测试运行脚本（性能优化版本）

支持以下测试模式：
- unit: 单元测试
- integration: 集成测试
- performance: 性能测试
- cache: 缓存测试
- async: 异步测试
- crawler: 爬虫测试
- scanner: 扫描测试
- all: 所有测试
- coverage: 覆盖率测试
- docker: Docker环境测试
- violation: 违规检测测试
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


def run_command(command, description=""):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🔄 执行: {description}")
    print(f"📝 命令: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"⏱️  执行时间: {end_time - start_time:.2f}秒")
    print(f"📊 返回码: {result.returncode}")
    
    if result.stdout:
        print("📤 标准输出:")
        print(result.stdout)
    
    if result.stderr:
        print("⚠️  错误输出:")
        print(result.stderr)
    
    success = result.returncode == 0
    if success:
        print(f"✅ {description} - 成功")
    else:
        print(f"❌ {description} - 失败")
    
    return success


def setup_test_environment():
    """设置测试环境"""
    print("🔧 设置测试环境...")
    
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
    os.environ["MONGODB_URL"] = "mongodb://localhost:27017/test_scanner"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    os.environ["DEBUG"] = "true"
    os.environ["CACHE_ENABLED"] = "true"
    os.environ["PERFORMANCE_MONITORING"] = "true"
    os.environ["ASYNC_TASK_ENABLED"] = "true"
    
    # 创建必要的目录
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    
    print("✅ 测试环境设置完成")
    return True


def run_unit_tests():
    """运行单元测试"""
    print("\n🧪 运行单元测试...")
    
    cmd = "python -m pytest tests/test_unit.py -v --tb=short"
    return run_command(cmd, "单元测试")


def run_integration_tests():
    """运行集成测试"""
    print("\n🔗 运行集成测试...")
    
    cmd = "python -m pytest tests/test_integration.py -v -m integration"
    return run_command(cmd, "集成测试")


def run_performance_tests():
    """运行性能测试"""
    print("\n⚡ 运行性能测试...")
    
    cmd = "python -m pytest tests/test_performance.py -v --tb=short"
    return run_command(cmd, "性能测试")


def run_cache_tests():
    """运行缓存测试"""
    print("\n💾 运行缓存测试...")
    
    cmd = "python -m pytest tests/test_cache.py -v --tb=short"
    return run_command(cmd, "缓存测试")


def run_async_tests():
    """运行异步测试"""
    print("\n🚀 运行异步测试...")
    
    cmd = "python -m pytest tests/test_async.py -v --tb=short"
    return run_command(cmd, "异步测试")


def run_crawler_tests():
    """运行爬虫测试"""
    print("\n🕷️  运行爬虫测试...")
    
    cmd = "python -m pytest tests/test_real_crawler.py -m real_website -v --tb=short"
    return run_command(cmd, "爬虫测试")


def run_scanner_tests():
    """运行扫描测试"""
    print("\n🔍 运行扫描测试...")
    
    cmd = "python -m pytest tests/test_real_scanner.py -m real_website -v --tb=short"
    return run_command(cmd, "扫描测试")


def run_real_website_tests():
    """运行真实网站测试"""
    print("\n🌐 运行真实网站测试...")
    
    cmd = "python -m pytest tests/test_real_websites.py -m real_website -v --tb=short"
    return run_command(cmd, "真实网站测试")


def run_violation_tests():
    """运行违规检测测试"""
    print("\n🚨 运行违规检测测试...")
    
    cmd = "python -m pytest tests/test_violation_detection_fix.py -v --tb=short"
    return run_command(cmd, "违规检测测试")


async def run_async_performance_test():
    """运行异步性能测试"""
    print("\n🚀 运行异步性能测试...")
    
    async def test_scanner_performance():
        """测试扫描器性能"""
        url = "http://localhost:8001/api/v1/scan"
        test_domains = ["example.com", "httpbin.org", "jsonplaceholder.typicode.com"]
        num_requests = 30
        concurrent = 5
        
        async def scan_domain(session, domain, request_id):
            start_time = time.time()
            try:
                async with session.post(
                    url,
                    json={"domain": domain, "scan_type": "basic"},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    duration = time.time() - start_time
                    return {
                        "request_id": request_id,
                        "domain": domain,
                        "status": response.status,
                        "duration": duration,
                        "success": response.status == 200
                    }
            except Exception as e:
                duration = time.time() - start_time
                return {
                    "request_id": request_id,
                    "domain": domain,
                    "status": "error",
                    "duration": duration,
                    "success": False,
                    "error": str(e)
                }
        
        # 创建信号量限制并发
        semaphore = asyncio.Semaphore(concurrent)
        
        async def limited_scan(session, domain, request_id):
            async with semaphore:
                return await scan_domain(session, domain, request_id)
        
        # 执行测试
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(num_requests):
                domain = test_domains[i % len(test_domains)]
                task = limited_scan(session, domain, i)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
        
        # 分析结果
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        durations = [r["duration"] for r in results]
        
        analysis = {
            "total_scans": num_requests,
            "successful_scans": len(successful),
            "failed_scans": len(failed),
            "success_rate": len(successful) / num_requests * 100,
            "avg_duration": statistics.mean(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "median_duration": statistics.median(durations),
            "p95_duration": sorted(durations)[int(len(durations) * 0.95)],
            "p99_duration": sorted(durations)[int(len(durations) * 0.99)],
            "throughput": num_requests / max(durations) if durations else 0
        }
        
        print(f"📊 异步性能测试结果:")
        print(f"  成功率: {analysis['success_rate']:.2f}%")
        print(f"  平均扫描时间: {analysis['avg_duration']:.3f}秒")
        print(f"  最大扫描时间: {analysis['max_duration']:.3f}秒")
        print(f"  吞吐量: {analysis['throughput']:.2f} 扫描/秒")
        
        return analysis
    
    try:
        return await test_scanner_performance()
    except Exception as e:
        print(f"❌ 异步性能测试失败: {e}")
        return None


def run_coverage_tests():
    """运行覆盖率测试"""
    print("\n📊 运行覆盖率测试...")
    
    # 安装覆盖率工具
    run_command("pip install pytest-cov", "安装覆盖率工具")
    
    # 运行覆盖率测试
    coverage_cmd = (
        "python -m pytest tests/ -v --cov=app --cov-report=html "
        "--cov-report=term-missing --cov-fail-under=80"
    )
    
    success = run_command(coverage_cmd, "覆盖率测试")
    
    if success:
        print("\n📈 覆盖率报告已生成在 htmlcov/ 目录中")
    
    return success


def run_docker_tests():
    """运行Docker环境测试"""
    print("\n🐳 运行Docker环境测试...")
    
    # 构建测试镜像
    if not run_command("docker build -t website-scanner-test .", "构建测试镜像"):
        return False
    
    # 启动测试环境
    if not run_command("docker-compose -f docker-compose.test.yml up -d", "启动测试环境"):
        return False
    
    # 等待服务启动
    print("⏳ 等待测试服务启动...")
    time.sleep(30)
    
    # 运行测试
    test_cmd = (
        "docker-compose -f docker-compose.test.yml run --rm website-scanner-test "
        "python -m pytest tests/ -v"
    )
    
    success = run_command(test_cmd, "Docker环境测试")
    
    # 清理测试环境
    run_command("docker-compose -f docker-compose.test.yml down", "清理测试环境")
    
    return success


def run_stress_test():
    """运行压力测试"""
    print("\n💪 运行压力测试...")
    
    cmd = "python tests/stress_test.py"
    return run_command(cmd, "压力测试")


def run_all_tests():
    """运行所有测试"""
    print("\n🎯 运行所有测试...")
    
    tests = [
        run_unit_tests,
        run_integration_tests,
        run_performance_tests,
        run_cache_tests,
        run_async_tests,
        run_crawler_tests,
        run_scanner_tests,
        run_real_website_tests
    ]
    
    success = True
    for test_func in tests:
        if not test_func():
            success = False
    
    return success


def run_specific_test(test_file):
    """运行特定的测试文件"""
    print(f"\n🎯 运行特定测试: {test_file}")
    
    if not os.path.exists(test_file):
        print(f"❌ 错误: 测试文件不存在: {test_file}")
        return False
    
    return run_command(f"python -m pytest {test_file} -v", f"特定测试: {test_file}")


def generate_test_report():
    """生成测试报告"""
    print("\n📊 生成测试报告...")
    
    report_cmd = (
        "python -m pytest tests/ -v --junitxml=test-results.xml "
        "--html=test-report.html --self-contained-html"
    )
    
    success = run_command(report_cmd, "生成测试报告")
    
    if success:
        # 生成性能报告
        performance_report = {
            "timestamp": time.time(),
            "test_type": "website_scanner_performance",
            "summary": {
                "unit_tests": "passed",
                "integration_tests": "passed",
                "performance_tests": "passed",
                "cache_tests": "passed",
                "async_tests": "passed",
                "crawler_tests": "passed",
                "scanner_tests": "passed",
                "real_website_tests": "passed"
            }
        }
        
        with open("performance_report.json", "w", encoding="utf-8") as f:
            json.dump(performance_report, f, indent=2, ensure_ascii=False)
        
        print("📊 性能报告已生成: performance_report.json")
    
    return success


def cleanup_test_environment():
    """清理测试环境"""
    print("\n🧹 清理测试环境...")
    
    # 清理Redis缓存
    try:
        subprocess.run(["redis-cli", "-n", "1", "flushall"], capture_output=True)
        print("✅ Redis缓存已清理")
    except Exception as e:
        print(f"⚠️  Redis缓存清理失败: {e}")
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Website Scanner 测试运行器（性能优化版本）")
    parser.add_argument(
        "mode",
        choices=["unit", "integration", "performance", "cache", "async", "crawler", "scanner", "real_website", "violation", "all", "coverage", "docker", "report", "stress", "async-performance"],
        help="测试模式"
    )
    parser.add_argument(
        "--test-file",
        help="运行特定的测试文件"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    parser.add_argument(
        "--no-setup",
        action="store_true",
        help="跳过环境设置"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="清理测试环境"
    )
    
    args = parser.parse_args()
    
    # 设置测试环境
    if not args.no_setup:
        if not setup_test_environment():
            print("❌ 测试环境设置失败")
            sys.exit(1)
    
    # 根据模式运行测试
    success = False
    
    if args.test_file:
        success = run_specific_test(args.test_file)
    elif args.mode == "unit":
        success = run_unit_tests()
    elif args.mode == "integration":
        success = run_integration_tests()
    elif args.mode == "performance":
        success = run_performance_tests()
    elif args.mode == "cache":
        success = run_cache_tests()
    elif args.mode == "async":
        success = run_async_tests()
    elif args.mode == "crawler":
        success = run_crawler_tests()
    elif args.mode == "scanner":
        success = run_scanner_tests()
    elif args.mode == "real_website":
        success = run_real_website_tests()
    elif args.mode == "violation":
        success = run_violation_tests()
    elif args.mode == "all":
        success = run_all_tests()
    elif args.mode == "coverage":
        success = run_coverage_tests()
    elif args.mode == "docker":
        success = run_docker_tests()
    elif args.mode == "report":
        success = generate_test_report()
    elif args.mode == "stress":
        success = run_stress_test()
    elif args.mode == "async-performance":
        # 运行异步性能测试
        result = asyncio.run(run_async_performance_test())
        success = result is not None
    
    # 清理测试环境
    if args.cleanup:
        cleanup_test_environment()
    
    # 输出结果
    print(f"\n{'='*60}")
    if success:
        print("🎉 所有测试通过!")
    else:
        print("❌ 测试失败!")
    print(f"{'='*60}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 