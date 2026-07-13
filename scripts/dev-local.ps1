$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

Get-Content ".env.dev" | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
  $name, $value = $_ -split '=', 2
  if ($name) { Set-Item -Path "env:$name" -Value $value }
}

New-Item -ItemType Directory -Force -Path "$root\backend\data" | Out-Null

Write-Host "Starting API http://127.0.0.1:8000 ..."
$api = Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" -WorkingDirectory "$root\backend" -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 3

Write-Host "Starting web http://127.0.0.1:5173 ..."
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npm) { $npm = "npm.cmd" }
$web = Start-Process -FilePath $npm -ArgumentList "run","dev","--","--host","127.0.0.1" -WorkingDirectory "$root\frontend" -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 5

try {
  $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 5
  $ver = $health.api_version
  if (-not $ver) { $ver = "legacy" }
  Write-Host "API OK: $($health.status) version=$ver"
} catch {
  Write-Host "API not responding yet"
}

Write-Host ""
Write-Host "Local dev started:"
Write-Host "  Web:  http://127.0.0.1:5173"
Write-Host "  API:  http://127.0.0.1:8000/docs"
Write-Host ""
Write-Host "Stop: Stop-Process -Id $($api.Id),$($web.Id) -Force"
