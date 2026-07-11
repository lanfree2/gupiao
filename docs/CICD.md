# 嘉岭佰 · 自动部署（CI/CD）

适用于：**代码在 GitHub，应用已用 Docker Compose 部署在 Linux 服务器**。

流程：

```
push main → GitHub Actions 构建检查(CI) → 通过后 SSH 部署(CD) → 健康检查
```

---

## 1. 服务器一次性准备

以下在**已部署好的 Linux 服务器**上执行。

### 1.1 确认项目目录

假设项目在：

```bash
cd /opt/gupiao   # 换成你的实际路径
docker compose ps
```

### 1.2 创建部署专用 SSH 密钥

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N "" -C "github-actions-deploy"
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys ~/.ssh/github_deploy
```

查看私钥（整段复制，稍后填入 GitHub Secret）：

```bash
cat ~/.ssh/github_deploy
```

### 1.3 确认服务器能拉取 GitHub 代码

```bash
cd /opt/gupiao
git remote -v
git pull origin main
```

若仓库是私有的，服务器需配置 Git 凭据（HTTPS Token 或 SSH deploy key）。

**私有仓库推荐**：在服务器再生成一把只读 Deploy Key，添加到 GitHub 仓库 → Settings → Deploy keys。

---

## 2. 配置 GitHub Secrets

打开仓库：**Settings → Secrets and variables → Actions → New repository secret**

| Secret 名称 | 示例值 | 说明 |
|-------------|--------|------|
| `DEPLOY_HOST` | `123.45.67.89` | 服务器公网 IP 或域名 |
| `DEPLOY_USER` | `root` | SSH 登录用户名 |
| `DEPLOY_KEY` | `-----BEGIN OPENSSH PRIVATE KEY-----...` | 1.2 步生成的**私钥**全文 |
| `DEPLOY_PATH` | `/opt/gupiao` | 项目在服务器上的绝对路径 |

注意：

- `.env` 只留在服务器，**不要**提交到 GitHub，也不要放进 Secrets（除非你用密钥管理方案）
- 首次部署时已在服务器配好 `.env`，自动部署不会覆盖它

---

## 3. 工作流说明

| 文件 | 触发时机 | 作用 |
|------|----------|------|
| `.github/workflows/ci.yml` | push / PR 到 `main` | 前端 `npm run build`、后端 import 检查 |
| `.github/workflows/deploy.yml` | CI 成功后，或手动触发 | SSH 登录服务器 → `git pull` → `docker compose up -d --build` → `/api/health` |

### 手动部署

GitHub 仓库 → **Actions** → **Deploy** → **Run workflow**。

---

## 4. 首次启用步骤

1. 把本仓库的 `.github/workflows/` 推送到 GitHub：

   ```bash
   git add .github/workflows/ci.yml .github/workflows/deploy.yml docs/CICD.md scripts/deploy-server.sh
   git commit -m "ci: add GitHub Actions CI/CD"
   git push origin main
   ```

2. 在 GitHub 配好 4 个 Secrets（上一节）

3. 打开 **Actions** 页，确认 `CI` 跑绿

4. `Deploy` 会自动跟着跑；或手动点 **Run workflow**

5. 部署成功后访问你的域名 / IP 验证

---

## 5. 服务器上手動部署（备用）

与 Actions 逻辑一致：

```bash
cd /opt/gupiao
chmod +x scripts/deploy-server.sh
./scripts/deploy-server.sh
```

---

## 6. 常见问题

| 现象 | 处理 |
|------|------|
| Deploy 报 `Permission denied (publickey)` | 检查 `DEPLOY_KEY` 是否完整、`DEPLOY_USER` 是否正确 |
| `git pull` 失败 | 服务器配置 GitHub 凭据或 Deploy Key |
| 健康检查超时 | `docker compose logs api` 看启动错误；常见是 `.env` / 数据库问题 |
| 只改了前端但没更新 | `docker compose up -d --build` 会重建 `web` 镜像，确认 Deploy 日志无报错 |
| 想先测 CI 不自动上线 | 暂时不配 Secrets，`CI` 仍会跑；`Deploy` 会因缺 Secret 失败 |

---

## 7. 安全建议

- 部署密钥专用于 GitHub Actions，不要复用个人 SSH 密钥
- 生产环境 `SEED_DEMO_USER=false`，改掉默认管理员密码
- 安全组只开放 80/443，**不要**把 22 端口对全网开放；可限制为 GitHub Actions IP 段或固定跳板机
- 后续可加：部署前自动备份数据库、失败时钉钉/邮件通知

---

## 8. 后续可增强

- **GHCR 镜像**：CI 构建镜像推送到 GitHub Container Registry，服务器只 pull，部署更快
- **Staging**：`develop` 分支部署测试机，`main` 部署生产
- **回滚**：`git reset --hard <上一个commit>` 后重新 `docker compose up -d --build`
