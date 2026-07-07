$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

# 加载本地开发环境变量
Get-Content ".env.dev" | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
  $name, $value = $_ -split '=', 2
  if ($name) { Set-Item -Path "env:$name" -Value $value }
}

New-Item -ItemType Directory -Force -Path "$root\backend\data" | Out-Null

Write-Host "启动后端 http://127.0.0.1:8000 ..."
$api = Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" -WorkingDirectory "$root\backend" -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 3

Write-Host "启动前端 http://127.0.0.1:5173 ..."
$web = Start-Process -FilePath "npm" -ArgumentList "run","dev","--","--host","127.0.0.1" -WorkingDirectory "$root\frontend" -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 4

try {
  $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 5
  Write-Host "API 正常: $($health.status)"
} catch {
  Write-Host "API 未响应，请检查后端日志"
}

Write-Host ""
Write-Host "荐迹本地开发已启动:"
Write-Host "  前端: http://127.0.0.1:5173"
Write-Host "  API:  http://127.0.0.1:8000/docs"
Write-Host "  演示: 13888888888 / demo123456"
Write-Host ""
Write-Host "关闭方式: Stop-Process -Id $($api.Id),$($web.Id)"
