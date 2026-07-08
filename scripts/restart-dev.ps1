$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent

function Stop-Port($port) {
  Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

Write-Host "停止旧进程 (8000 / 5173)..."
Stop-Port 8000
Stop-Port 5173
Start-Sleep -Seconds 1

& "$PSScriptRoot\dev-local.ps1"
