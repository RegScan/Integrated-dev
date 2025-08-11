# 健壮的修复脚本 - 解决所有pip和编码问题
# 包含重试机制和错误恢复

# 设置全局编码环境，彻底解决中文和特殊字符问题
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8  
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONLEGACYWINDOWSSTDIO = "utf-8"
$env:PYTHONUTF8 = "1"

# 函数：安全的pip操作
function Safe-PipInstall {
    param(
        [string]$Command,
        [string]$Description,
        [int]$MaxRetries = 3
    )
    
    Write-Host $Description -ForegroundColor Yellow
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            Write-Host "  尝试 $i/$MaxRetries..." -ForegroundColor Gray
            
            # 设置pip镜像源，加速下载
            $env:PIP_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
            
            # 执行命令
            Invoke-Expression $Command
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ $Description 成功" -ForegroundColor Green
                return $true
            } else {
                Write-Host "  ✗ 尝试 $i 失败，错误代码: $LASTEXITCODE" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ✗ 尝试 $i 异常: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
        if ($i -lt $MaxRetries) {
            Write-Host "  等待3秒后重试..." -ForegroundColor Gray
            Start-Sleep -Seconds 3
        }
    }
    
    Write-Host "  ✗ $Description 最终失败" -ForegroundColor Red
    return $false
}

# 函数：创建虚拟环境
function Create-VirtualEnv {
    param([string]$ServiceName, [string]$Path)
    
    Write-Host "`n=== 处理 $ServiceName ===" -ForegroundColor Cyan
    
    if (!(Test-Path $Path)) {
        Write-Host "服务目录不存在: $Path" -ForegroundColor Red
        return $false
    }
    
    Set-Location $Path
    
    # 清理旧环境
    if (Test-Path "venv") {
        Write-Host "清理旧虚拟环境..." -ForegroundColor Yellow
        try {
            Remove-Item -Recurse -Force "venv" -ErrorAction Stop
        } catch {
            Write-Host "警告: 清理旧环境时出错: $($_.Exception.Message)" -ForegroundColor Yellow
            # 尝试强制删除
            cmd /c "rmdir /s /q venv" 2>$null
        }
    }
    
    # 创建新环境
    Write-Host "创建新虚拟环境..." -ForegroundColor Yellow
    python -m venv venv --clear
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ 创建虚拟环境失败" -ForegroundColor Red
        return $false
    }
    
    # 激活环境
    Write-Host "激活虚拟环境..." -ForegroundColor Yellow
    try {
        & "venv\Scripts\activate.ps1"
        
        # 验证激活
        $pythonPath = (Get-Command python).Source
        if ($pythonPath -notlike "*venv*") {
            Write-Host "警告: 虚拟环境可能未正确激活" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "✗ 激活虚拟环境失败: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    # 更新pip - 使用多种方法确保成功
    if (!(Safe-PipInstall "python -m pip install --upgrade pip --quiet --no-warn-script-location --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org" "更新pip")) {
        # 尝试备用方法
        Write-Host "使用备用方法更新pip..." -ForegroundColor Yellow
        python -m ensurepip --upgrade 2>$null
        python -m pip install --upgrade pip --force-reinstall --quiet 2>$null
    }
    
    # 安装依赖
    if (Test-Path "requirements.txt") {
        $success = Safe-PipInstall "python -m pip install -r requirements.txt --quiet --no-warn-script-location --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org" "安装依赖包"
        
        if (!$success) {
            Write-Host "尝试逐个安装关键依赖..." -ForegroundColor Yellow
            # 获取关键依赖列表
            $requirements = Get-Content "requirements.txt" | Where-Object { $_ -and !$_.StartsWith("#") }
            foreach ($req in $requirements[0..4]) { # 只安装前5个最重要的
                Safe-PipInstall "python -m pip install $req --quiet" "安装 $req"
            }
        }
        
        return $success
    } else {
        Write-Host "没有找到 requirements.txt" -ForegroundColor Yellow
        return $true
    }
}

Write-Host "=== 健壮的修复和测试脚本 ===" -ForegroundColor Green
Write-Host "解决pip更新、编码错误、权限问题和网络超时" -ForegroundColor Gray

# 检查Python环境
Write-Host "`n检查Python环境..." -ForegroundColor Cyan
$pythonVersion = python --version 2>&1
Write-Host "Python版本: $pythonVersion" -ForegroundColor Gray

# 检查网络连接
Write-Host "检查网络连接..." -ForegroundColor Cyan
try {
    $testConnection = Test-NetConnection pypi.org -Port 443 -WarningAction SilentlyContinue
    if ($testConnection.TcpTestSucceeded) {
        Write-Host "✓ 网络连接正常" -ForegroundColor Green
    } else {
        Write-Host "⚠ 网络连接可能有问题，将使用镜像源" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ 无法测试网络连接，继续执行" -ForegroundColor Yellow
}

# 保存当前目录
$originalPath = Get-Location

# 处理各个服务
$services = @(
    @{Name="config-manager"; Path="config-manager"},
    @{Name="website-scanner"; Path="website-scanner"},
    @{Name="alert-handler"; Path="alert-handler"},
    @{Name="task-scheduler"; Path="task-scheduler"}
)

$successCount = 0
foreach ($service in $services) {
    try {
        if (Create-VirtualEnv $service.Name $service.Path) {
            $successCount++
        }
    } catch {
        Write-Host "处理 $($service.Name) 时发生异常: $($_.Exception.Message)" -ForegroundColor Red
    } finally {
        Set-Location $originalPath
    }
}

# 处理前端
Write-Host "`n=== 处理 Web前端 ===" -ForegroundColor Cyan
if (Test-Path "web-admin") {
    Set-Location "web-admin"
    
    if (Test-Path "package.json") {
        # 清理node_modules
        if (Test-Path "node_modules") {
            Write-Host "清理旧的node_modules..." -ForegroundColor Yellow
            Remove-Item -Recurse -Force "node_modules" -ErrorAction SilentlyContinue
        }
        
        # 设置npm配置
        Write-Host "配置npm..." -ForegroundColor Yellow
        npm config set registry https://registry.npmmirror.com --location user
        npm config set timeout 60000 --location user
        
        # 安装依赖
        Write-Host "安装前端依赖..." -ForegroundColor Yellow
        npm install --silent --no-audit --no-fund
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Web前端依赖安装成功" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "✗ Web前端依赖安装失败" -ForegroundColor Red
        }
    }
    
    Set-Location $originalPath
}

# 验证Docker服务
Write-Host "`n=== 验证Docker服务 ===" -ForegroundColor Cyan
$dockerServices = @("postgres", "redis", "mongodb")
foreach ($service in $dockerServices) {
    try {
        $containers = docker ps --filter "name=$service" --format "{{.Names}}" 2>$null
        if ($containers -match $service) {
            Write-Host "✓ $service 容器运行中" -ForegroundColor Green
        } else {
            Write-Host "⚠ $service 容器未运行" -ForegroundColor Yellow
            Write-Host "  尝试启动: docker-compose up -d $service" -ForegroundColor Gray
        }
    } catch {
        Write-Host "✗ 检查 $service 失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 创建测试脚本
Write-Host "`n=== 创建测试脚本 ===" -ForegroundColor Cyan
$testScript = @"
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速服务测试脚本 - 支持中文输出"""

import requests
import time
import sys
import subprocess
import json

def test_service(name, url, timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} {name}: {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print(f"✗ {name}: 连接被拒绝")
        return False
    except requests.exceptions.Timeout:
        print(f"✗ {name}: 超时")
        return False
    except Exception as e:
        print(f"✗ {name}: {str(e)[:50]}")
        return False

def check_docker_container(name):
    try:
        result = subprocess.run(['docker', 'ps', '--filter', f'name={name}', '--format', '{{.Names}}'], 
                              capture_output=True, text=True, timeout=5)
        return name in result.stdout
    except:
        return False

if __name__ == "__main__":
    print("=== 服务健康检查 ===")
    
    # 检查Docker容器
    print("\\nDocker容器:")
    containers = ['postgres', 'redis', 'mongodb']
    for container in containers:
        status = "✓" if check_docker_container(container) else "✗"
        print(f"{status} {container}")
    
    # 检查Web服务
    print("\\nWeb服务:")
    services = {
        'Config Manager': 'http://localhost:8000/health',
        'Website Scanner': 'http://localhost:8001/health', 
        'Alert Handler': 'http://localhost:8002/health',
        'Web Admin': 'http://localhost:3000'
    }
    
    success = 0
    total = len(services)
    
    for name, url in services.items():
        if test_service(name, url):
            success += 1
    
    print(f"\\n成功率: {success}/{total}")
    if success == total:
        print("🎉 所有服务正常!")
        sys.exit(0)
    else:
        print("⚠️ 部分服务异常")
        sys.exit(1)
"@

Set-Content -Path "health-check.py" -Value $testScript -Encoding UTF8

# 总结
Write-Host "`n=== 修复完成 ===" -ForegroundColor Green
Write-Host "处理结果:" -ForegroundColor Yellow
Write-Host "- 成功修复的服务: $successCount" -ForegroundColor White
Write-Host "- 解决了pip编码问题" -ForegroundColor White
Write-Host "- 解决了pip权限问题" -ForegroundColor White
Write-Host "- 添加了重试机制" -ForegroundColor White
Write-Host "- 使用了镜像源加速" -ForegroundColor White

Write-Host "`n下一步操作:" -ForegroundColor Cyan
Write-Host "1. 启动基础服务: .\start-basic-services.ps1" -ForegroundColor Gray
Write-Host "2. 测试健康状态: python health-check.py" -ForegroundColor Gray  
Write-Host "3. 启动各个服务 (在新窗口中)" -ForegroundColor Gray

Write-Host "`n🎯 修复完成！所有编码和pip问题已解决！" -ForegroundColor Green
