# 本地开发模式启动脚本
# 启动基础服务（数据库），然后手动启动Python服务

Write-Host "=== 本地开发模式启动 ===" -ForegroundColor Green

# 1. 启动基础服务
Write-Host "1. 启动基础服务..." -ForegroundColor Yellow
& .\start-basic-services.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "基础服务启动失败" -ForegroundColor Red
    exit 1
}

Write-Host "`n2. 本地开发环境设置..." -ForegroundColor Yellow

# 检查Python环境
$services = @(
    @{name="config-manager"; dir="config-manager"; port=8000},
    @{name="website-scanner"; dir="website-scanner"; port=8001},
    @{name="alert-handler"; dir="alert-handler"; port=8002}
)

Write-Host "`n=== Python服务启动指南 ===" -ForegroundColor Green

foreach ($service in $services) {
    Write-Host "`n【$($service.name)】" -ForegroundColor Cyan
    Write-Host "目录: $($service.dir)" -ForegroundColor Gray
    Write-Host "端口: $($service.port)" -ForegroundColor Gray
    
    # 检查requirements.txt
    $reqFile = Join-Path $service.dir "requirements.txt"
    if (Test-Path $reqFile) {
        Write-Host "✓ 依赖文件存在" -ForegroundColor Green
    } else {
        Write-Host "✗ 依赖文件缺失" -ForegroundColor Red
    }
    
    # 检查主模块
    $mainFile = Join-Path $service.dir "app\main.py"
    if (Test-Path $mainFile) {
        Write-Host "✓ 主模块存在" -ForegroundColor Green
    } else {
        Write-Host "✗ 主模块缺失" -ForegroundColor Red
    }
    
    Write-Host "启动命令:" -ForegroundColor Yellow
    Write-Host "  cd $($service.dir)" -ForegroundColor White
    Write-Host "  python -m venv venv" -ForegroundColor White
    Write-Host "  venv\Scripts\activate" -ForegroundColor White
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    Write-Host "  python -m app.main" -ForegroundColor White
}

# 3. 前端开发指南
Write-Host "`n【web-admin 前端】" -ForegroundColor Cyan
Write-Host "目录: web-admin" -ForegroundColor Gray
Write-Host "端口: 3000" -ForegroundColor Gray

if (Test-Path "web-admin\package.json") {
    Write-Host "✓ package.json存在" -ForegroundColor Green
} else {
    Write-Host "✗ package.json缺失" -ForegroundColor Red
}

Write-Host "启动命令:" -ForegroundColor Yellow
Write-Host "  cd web-admin" -ForegroundColor White
Write-Host "  npm install" -ForegroundColor White
Write-Host "  npm run dev" -ForegroundColor White

# 4. 环境变量提醒
Write-Host "`n=== 环境变量配置 ===" -ForegroundColor Green
Write-Host "确保各服务的环境变量正确设置：" -ForegroundColor Yellow

$envVars = @{
    "DATABASE_URL" = "postgresql://postgres:password@localhost:5432/config_manager"
    "MONGODB_URL" = "mongodb://localhost:27017/website_scanner"
    "REDIS_URL" = "redis://localhost:6379/0"
}

foreach ($var in $envVars.GetEnumerator()) {
    Write-Host "  $($var.Key)=$($var.Value)" -ForegroundColor Gray
}

Write-Host "`n=== 快速启动脚本 ===" -ForegroundColor Green
Write-Host "创建快速启动脚本..." -ForegroundColor Yellow

# 创建各服务的快速启动脚本
$quickStartScripts = @{
    "start-config-manager.ps1" = @"
# 配置管理服务快速启动
cd config-manager
if (!(Test-Path "venv")) {
    python -m venv venv
}
venv\Scripts\activate
pip install -r requirements.txt
`$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/config_manager"
`$env:REDIS_URL = "redis://localhost:6379/0"
python -m app.main
"@

    "start-website-scanner.ps1" = @"
# 网站扫描服务快速启动  
cd website-scanner
if (!(Test-Path "venv")) {
    python -m venv venv
}
venv\Scripts\activate
pip install -r requirements.txt
`$env:MONGODB_URL = "mongodb://localhost:27017/website_scanner"
`$env:REDIS_URL = "redis://localhost:6379/1"
python -m app.main
"@

    "start-web-admin.ps1" = @"
# Web管理界面快速启动
cd web-admin
if (!(Test-Path "node_modules")) {
    npm install
}
npm run dev
"@
}

foreach ($script in $quickStartScripts.GetEnumerator()) {
    Set-Content -Path $script.Key -Value $script.Value -Encoding UTF8
    Write-Host "创建: $($script.Key)" -ForegroundColor Green
}

Write-Host "`n=== 启动顺序建议 ===" -ForegroundColor Green
Write-Host "1. 基础服务已启动 ✓" -ForegroundColor Green
Write-Host "2. 启动配置管理服务: .\start-config-manager.ps1" -ForegroundColor Yellow
Write-Host "3. 启动网站扫描服务: .\start-website-scanner.ps1" -ForegroundColor Yellow  
Write-Host "4. 启动前端界面: .\start-web-admin.ps1" -ForegroundColor Yellow
Write-Host "5. 手动配置API网关（可选）" -ForegroundColor Yellow

Write-Host "`n开发环境启动完成！" -ForegroundColor Green
