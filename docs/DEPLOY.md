# 嘉岭佰 · 部署文档

本文说明如何在 Linux 服务器上使用 Docker Compose 一键部署。

---

## 1. 服务器要求

| 项 | 建议 |
|----|------|
| 系统 | Ubuntu 22.04+ / Debian 12+ |
| 配置 | 2 核 CPU · 4GB 内存 · 20GB 磁盘 |
| 软件 | Docker 24+ · Docker Compose v2 |

安装 Docker（Ubuntu）：

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# 重新登录后生效
```

---

## 2. 获取代码

```bash
git clone https://github.com/<你的用户名>/<仓库名>.git
cd <仓库名>
```

---

## 3. 配置环境变量

```bash
cp .env.example .env
nano .env
```

**生产环境务必修改：**

```env
SECRET_KEY=随机长字符串至少32位
POSTGRES_PASSWORD=强密码
ADMIN_PASSWORD=强密码
ADMIN_PHONE=你的管理员手机号

ENV=production
CORS_ORIGINS=https://你的域名.com
```

### 短信开关

| 变量 | 说明 |
|------|------|
| `SMS_ENABLED=false` | **演示模式**（默认）。接口正常，验证码固定为 `SMS_MOCK_CODE`（默认 123456） |
| `SMS_ENABLED=true` | 真实短信。需配置 `SMS_PROVIDER=aliyun` 及阿里云密钥 |

演示模式下前端会显示提示：「演示模式：验证码固定为 123456」。

接入阿里云后填写：

```env
SMS_ENABLED=true
SMS_PROVIDER=aliyun
ALIYUN_ACCESS_KEY_ID=...
ALIYUN_ACCESS_SECRET=...
ALIYUN_SMS_SIGN_NAME=...
ALIYUN_SMS_TEMPLATE_REGISTER=SMS_xxx
ALIYUN_SMS_TEMPLATE_RESET_PASSWORD=SMS_xxx
```

> 阿里云 SDK 接入点在 `backend/app/services/sms.py`，开启后需按注释补全 `_send_aliyun` 实现。

---

## 4. 启动服务

```bash
docker compose up -d --build
```

服务组成：

| 容器 | 端口 | 说明 |
|------|------|------|
| `web` | 80 | Nginx 托管前端 + 反代 `/api` |
| `api` | 8000 | FastAPI 后端 |
| `worker` | - | 定时抓取到期节点 |
| `db` | 5432（内部） | PostgreSQL |
| `redis` | 6379（内部） | Redis |

查看状态：

```bash
docker compose ps
docker compose logs -f api
```

---

## 5. 验证部署

1. 打开 `http://服务器IP/`
2. 用户登录：`13888888888` / `demo123456`（seed 演示账号，生产可删）
3. 管理后台：`http://服务器IP/admin/login`，使用 `.env` 中 `ADMIN_PHONE` / `ADMIN_PASSWORD`
4. 健康检查：`curl http://localhost:8000/api/health`

---

## 6. HTTPS（可选）

推荐使用 Caddy 或 Nginx 反向代理 + Let's Encrypt：

```bash
# 示例：Caddy 自动 HTTPS
your.domain.com {
    reverse_proxy localhost:80
}
```

同时将 `.env` 中 `CORS_ORIGINS` 改为 `https://your.domain.com`。

---

## 7. 常用运维命令

```bash
# 重启
docker compose restart

# 更新代码后重新构建
git pull
docker compose up -d --build

# 或启用 GitHub Actions 自动部署（见 docs/CICD.md）

# 查看 Worker 日志
docker compose logs -f worker

# 手动触发节点抓取（需管理员 Token）
curl -X POST http://localhost:8000/api/admin/worker/run \
  -H "Authorization: Bearer <admin_token>"

# 备份数据库
docker compose exec db pg_dump -U jianji jianji > backup_$(date +%F).sql

# 停止并删除容器（保留数据卷）
docker compose down

# 停止并删除数据（慎用）
docker compose down -v
```

---

## 8. Worker 说明

- 默认每个**工作日 16:30** 扫描到期节点，调用 AKShare 获取收盘价
- 调整时间：`.env` 中 `TRACKING_CRON_HOUR` / `TRACKING_CRON_MINUTE`
- 容器首次启动会立即执行一次抓取
- AKShare 需容器能访问外网

---

## 9. 密码相关接口

| 接口 | 说明 |
|------|------|
| `POST /api/auth/password/change` | 登录后修改密码（旧密码 + 新密码） |
| `POST /api/auth/password/reset/sms` | 忘记密码，短信验证码重置 |
| `GET /api/auth/sms/config` | 前端读取短信开关状态 |
| `POST /api/auth/sms/send` | 发送验证码（register / reset_password） |

---

## 10. 故障排查

| 现象 | 处理 |
|------|------|
| 502 / 无法访问 | `docker compose logs api web` |
| 数据库连接失败 | 确认 `db` 健康，`DATABASE_URL` 正确 |
| 节点一直待到期 | 检查 worker 日志；手动触发 admin worker |
| AKShare 失败 | 网络问题或股票停牌；见 `tracking_nodes.error_message` |
| 验证码收不到 | 确认 `SMS_ENABLED`；演示模式用固定码 |

---

## 11. 开发模式（非 Docker）

见项目根目录 [README.md](../README.md)。
