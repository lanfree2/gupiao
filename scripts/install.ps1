$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path .env)) { Copy-Item .env.example .env; Write-Host "已创建 .env，请编辑后重新运行"; exit 0 }
docker compose up -d --build
Write-Host "嘉岭佰已启动: http://localhost"
Write-Host "演示用户 13888888888 / demo123456"
