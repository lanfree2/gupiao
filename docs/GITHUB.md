# 发布到 GitHub

本文说明如何把「荐迹」项目上传到 GitHub，并在服务器上拉取部署。

---

## 一、本机准备

### 1. 安装 Git

Windows 下载安装：[https://git-scm.com/download/win](https://git-scm.com/download/win)

安装时勾选 **"Git from the command line and also from 3rd-party software"**，装完后**重新打开终端**。

验证：

```powershell
git --version
```

### 2. 配置 Git 身份（首次使用）

```powershell
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

### 3. 登录 GitHub

1. 打开 [https://github.com](https://github.com) 注册/登录
2. 建议配置 SSH 或 HTTPS 凭据：
   - **HTTPS**：推送时用 Personal Access Token（Settings → Developer settings → Personal access tokens）
   - **SSH**：生成密钥 `ssh-keygen -t ed25519`，把公钥加到 GitHub → Settings → SSH keys

---

## 二、在 GitHub 创建空仓库

1. 点击右上角 **+** → **New repository**
2. 仓库名建议：`jianji` 或 `stock-tracker`
3. 选 **Private**（私有）或 **Public**（公开）
4. **不要**勾选 "Add a README"（本地已有代码）
5. 创建后记下地址，例如：
   - HTTPS：`https://github.com/你的用户名/jianji.git`
   - SSH：`git@github.com:你的用户名/jianji.git`

---

## 三、本地初始化并推送

在项目根目录 `D:\股票后台展示系统` 执行：

```powershell
cd D:\股票后台展示系统

# 初始化仓库
git init

# 添加所有文件（.env、node_modules 等已被 .gitignore 排除）
git add .

# 首次提交
git commit -m "feat: 荐迹 MVP - FastAPI + Vue3 + Docker"

# 关联远程仓库（把 URL 换成你的）
git remote add origin https://github.com/你的用户名/jianji.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 推送时常见问题

| 问题 | 处理 |
|------|------|
| 要求输入用户名密码 | GitHub 已不支持账号密码，需用 **Personal Access Token** 当密码 |
| `git: command not found` | 安装 Git 并重启终端 |
| 文件太大被拒绝 | 确认 `node_modules/`、`frontend/dist/` 未被提交；若已提交用 `git rm -r --cached` 移除 |
| 不想提交 `.env` | 已在 `.gitignore` 中，只提交 `.env.example` |

### 检查哪些文件会被提交

```powershell
git status
git ls-files
```

**切勿提交**：`.env`（含密码）、`backend/data/*.db`（本地 SQLite 数据）

---

## 四、后续更新代码

```powershell
git add .
git commit -m "fix: 描述本次修改"
git push
```

---

## 五、从 GitHub 部署到线上服务器

代码上传后，在 **Linux 云服务器**（阿里云 / 腾讯云 / 华为云等）上：

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# 退出 SSH 重新登录

# 2. 克隆代码
git clone https://github.com/你的用户名/jianji.git
cd jianji

# 3. 配置环境变量
cp .env.example .env
nano .env   # 修改 SECRET_KEY、POSTGRES_PASSWORD、ADMIN_PASSWORD、CORS_ORIGINS

# 4. 启动
docker compose up -d --build

# 5. 开放防火墙端口
# 云控制台安全组：放行 TCP 80（和可选 443）
```

访问：`http://服务器公网IP/`

更完整的 HTTPS、备份、运维说明见 [DEPLOY.md](./DEPLOY.md)。

---

## 六、推荐的生产环境 `.env` 修改项

```env
ENV=production
SECRET_KEY=至少32位随机字符串
POSTGRES_PASSWORD=强密码
ADMIN_PASSWORD=强密码
ADMIN_PHONE=你的手机号
CORS_ORIGINS=https://你的域名.com
SEED_DEMO_USER=false          # 生产环境建议关闭演示账号
SMS_ENABLED=false             # 未接短信前保持演示模式
```

生成随机 SECRET_KEY（Linux）：

```bash
openssl rand -hex 32
```

---

## 七、没有服务器的替代方案

| 方案 | 说明 |
|------|------|
| **云服务器 + Docker** | 推荐，按 DEPLOY.md 操作，约 50–100 元/月 |
| **GitHub 仅作代码托管** | 只上传代码，不自动部署 |
| **Railway / Render** | 需改 compose 为多服务或单容器，适合进阶用户 |

当前项目按 **Docker Compose 单机部署** 设计，最简单路径是：**GitHub 存代码 + 一台 Linux 云服务器跑 `docker compose up`**。

---

## 八、一键脚本（Windows 本机推送前检查）

```powershell
.\scripts\pre-push-check.ps1
```

会检查 Git 是否安装、`.env` 是否误加入、前端能否构建等。
