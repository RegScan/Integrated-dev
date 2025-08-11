# 开发环境启动脚本
Write-Host "正在启动web-admin开发环境..." -ForegroundColor Green

# 检查Node.js版本
$nodeVersion = node --version
Write-Host "Node.js版本: $nodeVersion" -ForegroundColor Yellow

# 检查npm版本
$npmVersion = npm --version
Write-Host "npm版本: $npmVersion" -ForegroundColor Yellow

# 清理缓存
Write-Host "清理缓存..." -ForegroundColor Blue
npm run clean

# 重新安装依赖
Write-Host "重新安装依赖..." -ForegroundColor Blue
npm install

# 启动开发服务器
Write-Host "启动开发服务器..." -ForegroundColor Green
npm run dev:simple
