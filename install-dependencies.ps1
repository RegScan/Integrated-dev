# 重新安装所有服务的依赖
# 用于修复依赖缺失问题

Write-Host "=== 重新安装所有Python依赖 ===" -ForegroundColor Green

$services = @("config-manager", "website-scanner", "alert-handler", "task-scheduler")

foreach ($service in $services) {
    Write-Host "`n=== 处理 $service ===" -ForegroundColor Cyan
    
    if (!(Test-Path $service)) {
        Write-Host "跳过: $service 目录不存在" -ForegroundColor Yellow
        continue
    }
    
    Set-Location $service
    
    # 删除旧的虚拟环境
    if (Test-Path "venv") {
        Write-Host "删除旧的虚拟环境..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force "venv"
    }
    
    # 创建新的虚拟环境
    Write-Host "创建虚拟环境..." -ForegroundColor Yellow
    python -m venv venv
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "创建虚拟环境失败: $service" -ForegroundColor Red
        Set-Location ..
        continue
    }
    
    # 激活虚拟环境
    Write-Host "激活虚拟环境..." -ForegroundColor Yellow
    & "venv\Scripts\activate.ps1"
    
    # 升级pip
    Write-Host "升级pip..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    
    # 安装依赖
    if (Test-Path "requirements.txt") {
        Write-Host "安装依赖: $service" -ForegroundColor Yellow
        pip install -r requirements.txt
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ $service 依赖安装成功" -ForegroundColor Green
        } else {
            Write-Host "✗ $service 依赖安装失败" -ForegroundColor Red
        }
    } else {
        Write-Host "警告: $service 没有 requirements.txt" -ForegroundColor Yellow
    }
    
    Set-Location ..
}

Write-Host "`n=== 安装Web-Admin依赖 ===" -ForegroundColor Cyan

if (Test-Path "web-admin") {
    Set-Location web-admin
    
    # 删除旧的node_modules
    if (Test-Path "node_modules") {
        Write-Host "删除旧的node_modules..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force "node_modules"
    }
    
    if (Test-Path "package.json") {
        Write-Host "安装前端依赖..." -ForegroundColor Yellow
        npm install
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Web-Admin 依赖安装成功" -ForegroundColor Green
        } else {
            Write-Host "✗ Web-Admin 依赖安装失败" -ForegroundColor Red
        }
    }
    
    Set-Location ..
}

Write-Host "`n=== 依赖安装完成 ===" -ForegroundColor Green
Write-Host "现在可以使用以下命令启动服务：" -ForegroundColor Yellow
Write-Host "  .\start-config-manager.ps1" -ForegroundColor Gray
Write-Host "  .\start-website-scanner.ps1" -ForegroundColor Gray
Write-Host "  .\start-web-admin.ps1" -ForegroundColor Gray
