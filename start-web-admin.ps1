# Web管理界面快速启动
Write-Host "=== 启动Web管理界面 ===" -ForegroundColor Green

# 检查Node.js环境
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "错误: Node.js未安装或不在PATH中" -ForegroundColor Red
    Write-Host "请从 https://nodejs.org 下载安装Node.js" -ForegroundColor Yellow
    exit 1
}

if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "错误: npm未安装或不在PATH中" -ForegroundColor Red
    exit 1
}

# 进入服务目录
if (!(Test-Path "web-admin")) {
    Write-Host "错误: web-admin目录不存在" -ForegroundColor Red
    exit 1
}

Set-Location web-admin

Write-Host "当前目录: $(Get-Location)" -ForegroundColor Gray

# 检查package.json
if (!(Test-Path "package.json")) {
    Write-Host "错误: package.json不存在" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# 安装依赖
if (!(Test-Path "node_modules")) {
    Write-Host "安装Node.js依赖..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "依赖安装失败" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
} else {
    Write-Host "依赖已存在，跳过安装" -ForegroundColor Gray
}

# 检查开发环境配置
if (Test-Path "env.development") {
    Write-Host "使用开发环境配置: env.development" -ForegroundColor Gray
} else {
    Write-Host "警告: env.development不存在" -ForegroundColor Yellow
}

Write-Host "`n=== 启动Web管理界面 ===" -ForegroundColor Green
Write-Host "端口: 3000" -ForegroundColor Cyan
Write-Host "访问: http://localhost:3000" -ForegroundColor Cyan
Write-Host "API代理: http://localhost:8080/api" -ForegroundColor Cyan
Write-Host "`n按Ctrl+C停止服务" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Green

# 启动开发服务器
npm run dev