# 服务连接测试
import requests
import time

services = {
    'config-manager': 'http://localhost:8000/health',
    'website-scanner': 'http://localhost:8001/health',
    'web-admin': 'http://localhost:3000'
}

print("等待5秒后开始测试...")
time.sleep(5)

for name, url in services.items():
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            print(f"✓ {name}: OK")
        else:
            print(f"✗ {name}: 状态码 {response.status_code}")
    except Exception as e:
        print(f"✗ {name}: 连接失败 - {str(e)[:50]}")
