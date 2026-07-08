$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

Write-Host "=== 嘉岭佰 · 推送前检查 ===" -ForegroundColor Cyan

# Git
try {
  $gitVer = git --version
  Write-Host "[OK] $gitVer"
} catch {
  Write-Host "[FAIL] 未安装 Git，请从 https://git-scm.com/download/win 安装" -ForegroundColor Red
  exit 1
}

# 敏感文件
$bad = @()
if (Test-Path ".env") {
  $tracked = git ls-files ".env" 2>$null
  if ($tracked) { $bad += ".env 已被 git 跟踪，请执行: git rm --cached .env" }
}
if (Test-Path "backend\data\jianji.db") {
  $tracked = git ls-files "backend/data/jianji.db" 2>$null
  if ($tracked) { $bad += "本地数据库文件被跟踪，请加入 .gitignore 并 git rm --cached" }
}
if ($bad.Count) {
  foreach ($b in $bad) { Write-Host "[FAIL] $b" -ForegroundColor Red }
  exit 1
}
Write-Host "[OK] 未发现敏感文件被跟踪"

# 应有文件
@(".env.example", "docker-compose.yml", "README.md") | ForEach-Object {
  if (-not (Test-Path $_)) { Write-Host "[FAIL] 缺少 $_" -ForegroundColor Red; exit 1 }
}
Write-Host "[OK] 核心文件齐全"

# 前端构建（可选，较慢）
if (Test-Path "frontend\package.json") {
  Write-Host "[..] 验证前端构建..."
  Push-Location frontend
  npm run build --silent 2>$null
  if ($LASTEXITCODE -ne 0) { Write-Host "[WARN] 前端构建失败，推送前建议修复" -ForegroundColor Yellow }
  else { Write-Host "[OK] 前端构建通过" }
  Pop-Location
}

Write-Host ""
Write-Host "检查完成。可执行:" -ForegroundColor Green
Write-Host "  git init"
Write-Host "  git add ."
Write-Host "  git commit -m `"feat: 嘉岭佰 MVP`""
Write-Host "  git remote add origin https://github.com/你的用户名/仓库名.git"
Write-Host "  git push -u origin main"
Write-Host ""
Write-Host "详细说明: docs\GITHUB.md"
