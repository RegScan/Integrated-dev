# 网站扫描服务快速启动
Write-Host "=== 启动网站扫描服务 ===" -ForegroundColor Green

# 检查Python环境
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "错误: Python未安装或不在PATH中" -ForegroundColor Red
    exit 1
}

# 进入服务目录
if (!(Test-Path "website-scanner")) {
    Write-Host "错误: website-scanner目录不存在" -ForegroundColor Red
    exit 1
}

Set-Location website-scanner

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
$env:MONGODB_URL = "mongodb://localhost:27017/website_scanner"
$env:REDIS_URL = "redis://localhost:6379/1"
$env:ENVIRONMENT = "development"
$env:DEBUG = "true"

Write-Host "环境变量已设置:" -ForegroundColor Gray
Write-Host "  MONGODB_URL: $env:MONGODB_URL" -ForegroundColor Gray
Write-Host "  REDIS_URL: $env:REDIS_URL" -ForegroundColor Gray

# 检查主模块
if (!(Test-Path "app\main.py")) {
    Write-Host "错误: app\main.py不存在" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "`n=== 启动网站扫描服务 ===" -ForegroundColor Green
Write-Host "端口: 8001" -ForegroundColor Cyan
Write-Host "访问: http://localhost:8001" -ForegroundColor Cyan
Write-Host "健康检查: http://localhost:8001/health" -ForegroundColor Cyan
Write-Host "`n按Ctrl+C停止服务" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Green

# 启动服务
python -m app.main