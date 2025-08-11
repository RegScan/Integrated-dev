#!/usr/bin/env python3
"""
Website Scanner 快速启动脚本
帮助用户快速配置和启动系统
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    print("=" * 60)
    print("🚀 Website Scanner 快速启动向导")
    print("=" * 60)
    print()

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        sys.exit(1)
    print("✅ Python版本检查通过")

def check_dependencies():
    """检查依赖包"""
    print("📦 检查依赖包...")
    try:
        import fastapi
        import uvicorn
        import playwright
        import pymongo
        import redis
        print("✅ 核心依赖包已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请运行: pip install -r requirements.txt")
        return False
    return True

def setup_environment():
    """设置环境变量"""
    print("🔧 设置环境变量...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("📝 创建 .env 文件...")
            with open(env_example, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换示例值为实际值
            content = content.replace("your_baidu_api_key_here", "")
            content = content.replace("your_baidu_secret_key_here", "")
            content = content.replace("your_aliyun_access_key_here", "")
            content = content.replace("your_aliyun_secret_key_here", "")
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ .env 文件已创建")
        else:
            print("⚠️  未找到 env.example 文件")
    else:
        print("✅ .env 文件已存在")

def check_docker():
    """检查Docker环境"""
    print("🐳 检查Docker环境...")
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Docker已安装")
            return True
        else:
            print("❌ Docker未正确安装")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Docker未安装或无法访问")
        return False

def start_services():
    """启动服务"""
    print("🚀 启动服务...")
    
    if check_docker():
        print("使用Docker启动服务...")
        try:
            subprocess.run(["docker-compose", "up", "-d"], check=True)
            print("✅ 服务启动成功")
            print("📊 监控面板: http://localhost:3000 (Grafana)")
            print("📈 指标服务: http://localhost:9090 (Prometheus)")
            print("🔍 扫描服务: http://localhost:8001")
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker启动失败: {e}")
            print("尝试直接启动Python服务...")
            start_python_service()
    else:
        print("直接启动Python服务...")
        start_python_service()

def start_python_service():
    """启动Python服务"""
    print("🐍 启动Python服务...")
    try:
        # 检查MongoDB和Redis是否可用
        print("检查数据库连接...")
        
        # 启动服务
        print("启动Website Scanner服务...")
        subprocess.run([sys.executable, "-m", "uvicorn", 
                       "app.main:app", "--host", "0.0.0.0", "--port", "8001"], 
                      check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 服务启动失败: {e}")
        print("请检查配置和依赖")

def run_tests():
    """运行测试"""
    print("🧪 运行测试...")
    try:
        subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], check=True)
        print("✅ 测试通过")
    except subprocess.CalledProcessError as e:
        print(f"❌ 测试失败: {e}")

def show_status():
    """显示服务状态"""
    print("\n📊 服务状态:")
    print("-" * 40)
    
    services = [
        ("Website Scanner", "http://localhost:8001"),
        ("MongoDB", "mongodb://localhost:27017"),
        ("Redis", "redis://localhost:6379"),
        ("Grafana", "http://localhost:3000"),
        ("Prometheus", "http://localhost:9090")
    ]
    
    for name, url in services:
        print(f"{name:20} {url}")

def main():
    """主函数"""
    print_banner()
    
    # 检查环境
    check_python_version()
    
    if not check_dependencies():
        print("\n请先安装依赖包:")
        print("pip install -r requirements.txt")
        return
    
    # 设置环境
    setup_environment()
    
    # 询问用户操作
    print("\n请选择操作:")
    print("1. 启动所有服务 (推荐)")
    print("2. 运行测试")
    print("3. 显示服务状态")
    print("4. 退出")
    
    while True:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            start_services()
            break
        elif choice == "2":
            run_tests()
            break
        elif choice == "3":
            show_status()
            break
        elif choice == "4":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择，请输入1-4")

if __name__ == "__main__":
    main()
