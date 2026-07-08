$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created .env from .env.example — edit SECRET_KEY and passwords before production."
}

docker compose up -d --build

Write-Host ""
Write-Host "嘉岭佰已启动: http://localhost"
Write-Host "API 文档:   http://localhost:8000/docs"
Write-Host "演示账号:   13888888888 / demo123456"
Write-Host "管理后台:   http://localhost/admin/login"
