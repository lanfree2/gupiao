# 嘉岭佰 · 股票推荐追踪系统

个人股票推荐录入、多周期自动追踪、渠道业绩统计，含平台管理后台。

## 功能概览

- **用户端**：注册/登录、渠道管理、推荐录入、我的追踪、搜索、总览、修改密码、短信找回密码
- **管理后台**：全站股票/渠道/推荐、分周期业绩统计
- **Worker**：收盘后自动抓取节点涨跌幅（AKShare）
- **短信开关**：`SMS_ENABLED=false` 时为演示模式，验证码固定为 `SMS_MOCK_CODE`

## 快速开始

### 方式 A：本地开发（无需 Docker，推荐先试这个）

```powershell
cd D:\股票后台展示系统
.\scripts\dev-local.ps1
```

浏览器打开：**http://127.0.0.1:5173**（不是 localhost:80）

### 方式 B：Docker 一键部署

需先安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)。

```bash
cp .env.example .env
docker compose up -d --build
```

浏览器打开：**http://localhost**（端口 80）

> 若打开 `http://localhost` 显示 **Can't connect to server**，说明 Docker 未启动或未安装，请用方式 A 或先安装 Docker Desktop。

| 角色 | 账号 | 默认密码 |
|------|------|----------|
| 演示用户 | 13888888888 | demo123456 |
| 管理员 | 13800000000 | admin123（见 `.env` 中 `ADMIN_PASSWORD`）|

API 文档：http://localhost:8000/docs

## 本地开发

### 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp ..\.env.example ..\.env
# DATABASE_URL 改为 localhost:5432
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 手动跑 Worker

```bash
cd backend
python -m app.worker.run
```

## 文档

- [发布到 GitHub](docs/GITHUB.md)
- [线上部署（Docker）](docs/DEPLOY.md)
- [API 说明](docs/API.md)
- 交互原型：`index.html`

## 技术栈

FastAPI · PostgreSQL · Redis · Vue 3 · Vite · AKShare · Docker Compose

## 免责声明

本系统仅作个人信息记录与统计参考，不构成任何投资建议。
