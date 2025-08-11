# 配置管理服务快速启动
Write-Host "=== 启动配置管理服务 ===" -ForegroundColor Green

# 检查Python环境
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "错误: Python未安装或不在PATH中" -ForegroundColor Red
    exit 1
}

# 进入服务目录
if (!(Test-Path "config-manager")) {
    Write-Host "错误: config-manager目录不存在" -ForegroundColor Red
    exit 1
}

Set-Location config-manager

Write-Host "当前目录: $(Get-Location)" -ForegroundColor Gray

# 检查虚拟环境
if (!(Test-Path "venv")) {
    Write-Host "创建Python虚拟环境..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "创建虚拟环境失败" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
}

# 激活虚拟环境
Write-Host "激活虚拟环境..." -ForegroundColor Yellow
& "venv\Scripts\activate.ps1"

# 安装依赖
if (Test-Path "requirements.txt") {
    Write-Host "安装Python依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "依赖安装失败" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
} else {
    Write-Host "警告: requirements.txt不存在" -ForegroundColor Yellow
}

# 设置环境变量
Write-Host "设置环境变量..." -ForegroundColor Yellow
$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/config_manager"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:SECRET_KEY = "your-secret-key-here"
$env:ENVIRONMENT = "development"

Write-Host "环境变量已设置:" -ForegroundColor Gray
Write-Host "  DATABASE_URL: $env:DATABASE_URL" -ForegroundColor Gray
Write-Host "  REDIS_URL: $env:REDIS_URL" -ForegroundColor Gray

# 检查主模块
if (!(Test-Path "app\main.py")) {
    Write-Host "错误: app\main.py不存在" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "`n=== 启动配置管理服务 ===" -ForegroundColor Green
Write-Host "端口: 8000" -ForegroundColor Cyan
Write-Host "访问: http://localhost:8000" -ForegroundColor Cyan
Write-Host "健康检查: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "`n按Ctrl+C停止服务" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Green

# 启动服务
python -m app.main