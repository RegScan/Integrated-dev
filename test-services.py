#!/usr/bin/env python3
"""
服务连接测试脚本
用于测试所有微服务的连接状态和基本功能
"""

import requests
import json
import time
import sys
from typing import Dict, List, Tuple

class ServiceTester:
    def __init__(self):
        self.base_urls = {
            'api-gateway': 'http://localhost:8080',
            'config-manager': 'http://localhost:8000',
            'website-scanner': 'http://localhost:8001',
            'alert-handler': 'http://localhost:8002',
            'task-scheduler': 'http://localhost:8003',
            'web-admin': 'http://localhost:3000',
            'prometheus': 'http://localhost:9090',
            'grafana': 'http://localhost:3001'
        }
        
        self.test_results: List[Dict] = []
    
    def log(self, message: str, level: str = "INFO"):
        """打印日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def test_health_endpoint(self, service_name: str, url: str) -> Tuple[bool, str]:
        """测试健康检查端点"""
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                return True, f"健康 (响应时间: {response.elapsed.total_seconds():.2f}s)"
            else:
                return False, f"状态码: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "连接失败"
        except requests.exceptions.Timeout:
            return False, "请求超时"
        except Exception as e:
            return False, f"错误: {str(e)}"
    
    def test_api_gateway_routes(self) -> Tuple[bool, str]:
        """测试API网关路由"""
        try:
            # 测试网关健康检查
            response = requests.get(f"{self.base_urls['api-gateway']}/health", timeout=5)
            if response.status_code != 200:
                return False, f"网关健康检查失败: {response.status_code}"
            
            # 测试路由转发
            test_routes = [
                "/api/health/config",
                "/api/health/scanner", 
                "/api/health/alert",
                "/api/health/task"
            ]
            
            failed_routes = []
            for route in test_routes:
                try:
                    resp = requests.get(f"{self.base_urls['api-gateway']}{route}", timeout=5)
                    if resp.status_code not in [200, 404]:  # 404是可以接受的，说明路由能通
                        failed_routes.append(f"{route}({resp.status_code})")
                except Exception as e:
                    failed_routes.append(f"{route}(连接失败)")
            
            if failed_routes:
                return False, f"路由失败: {', '.join(failed_routes)}"
            else:
                return True, "所有路由正常"
                
        except Exception as e:
            return False, f"网关测试失败: {str(e)}"
    
    def test_user_login_flow(self) -> Tuple[bool, str]:
        """测试用户登录流程"""
        try:
            login_url = f"{self.base_urls['api-gateway']}/api/auth/login"
            
            # 测试登录端点是否可访问
            test_data = {
                "username": "test_user_not_exist",
                "password": "test_password"
            }
            
            response = requests.post(login_url, json=test_data, timeout=5)
            
            # 期望得到401未授权或400错误请求，说明端点工作正常
            if response.status_code in [400, 401, 422]:
                return True, f"登录端点响应正常 (状态码: {response.status_code})"
            elif response.status_code == 404:
                return False, "登录端点不存在或路由配置错误"
            else:
                return False, f"异常状态码: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "无法连接到登录服务"
        except Exception as e:
            return False, f"登录测试失败: {str(e)}"
    
    def test_database_connections(self) -> Tuple[bool, str]:
        """测试数据库连接状态"""
        try:
            # 通过各服务的健康检查间接测试数据库连接
            db_services = ['config-manager', 'website-scanner', 'alert-handler']
            failed_services = []
            
            for service in db_services:
                success, message = self.test_health_endpoint(service, self.base_urls[service])
                if not success:
                    failed_services.append(f"{service}({message})")
            
            if failed_services:
                return False, f"数据库连接失败: {', '.join(failed_services)}"
            else:
                return True, "所有数据库连接正常"
                
        except Exception as e:
            return False, f"数据库连接测试失败: {str(e)}"
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("开始服务连接测试", "INFO")
        self.log("=" * 60, "INFO")
        
        # 1. 基础服务健康检查
        self.log("1. 测试基础服务健康状态", "INFO")
        for service_name, url in self.base_urls.items():
            success, message = self.test_health_endpoint(service_name, url)
            status = "✓" if success else "✗"
            level = "INFO" if success else "ERROR"
            self.log(f"  {status} {service_name}: {message}", level)
            
            self.test_results.append({
                'test': f'{service_name}_health',
                'success': success,
                'message': message
            })
        
        self.log("", "INFO")
        
        # 2. API网关路由测试
        self.log("2. 测试API网关路由", "INFO")
        success, message = self.test_api_gateway_routes()
        status = "✓" if success else "✗"
        level = "INFO" if success else "ERROR"
        self.log(f"  {status} API网关路由: {message}", level)
        
        self.test_results.append({
            'test': 'api_gateway_routes',
            'success': success,
            'message': message
        })
        
        self.log("", "INFO")
        
        # 3. 用户登录流程测试
        self.log("3. 测试用户登录流程", "INFO")
        success, message = self.test_user_login_flow()
        status = "✓" if success else "✗"
        level = "INFO" if success else "ERROR"
        self.log(f"  {status} 用户登录: {message}", level)
        
        self.test_results.append({
            'test': 'user_login_flow',
            'success': success,
            'message': message
        })
        
        self.log("", "INFO")
        
        # 4. 数据库连接测试
        self.log("4. 测试数据库连接", "INFO")
        success, message = self.test_database_connections()
        status = "✓" if success else "✗"
        level = "INFO" if success else "ERROR"
        self.log(f"  {status} 数据库连接: {message}", level)
        
        self.test_results.append({
            'test': 'database_connections',
            'success': success,
            'message': message
        })
        
        self.log("", "INFO")
        
        # 测试总结
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        self.log("=" * 60, "INFO")
        self.log("测试总结", "INFO")
        self.log(f"总测试数: {total_tests}", "INFO")
        self.log(f"通过: {passed_tests}", "INFO" if failed_tests == 0 else "WARN")
        self.log(f"失败: {failed_tests}", "INFO" if failed_tests == 0 else "ERROR")
        
        if failed_tests > 0:
            self.log("", "ERROR")
            self.log("失败的测试:", "ERROR")
            for result in self.test_results:
                if not result['success']:
                    self.log(f"  ✗ {result['test']}: {result['message']}", "ERROR")
        
        self.log("=" * 60, "INFO")
        
        if failed_tests == 0:
            self.log("🎉 所有测试通过！系统运行正常。", "INFO")
            return True
        else:
            self.log("⚠️  部分测试失败，请检查相关服务。", "ERROR")
            return False

def main():
    """主函数"""
    print("内容合规检测系统 - 服务连接测试")
    print("请确保所有Docker容器已启动")
    print()
    
    # 等待用户确认
    try:
        input("按回车键开始测试...")
    except KeyboardInterrupt:
        print("\n测试已取消")
        return
    
    print()
    
    # 运行测试
    tester = ServiceTester()
    success = tester.run_all_tests()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()