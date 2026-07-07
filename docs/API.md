# API 概览

Base URL: `/api`  
认证：`Authorization: Bearer <token>`

## 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/auth/sms/config` | 短信开关配置 |
| POST | `/auth/sms/send` | 发送验证码 `{ phone, purpose: register\|reset_password }` |
| POST | `/auth/register` | 注册 `{ phone, code, password, nickname? }` |
| POST | `/auth/login` | 登录 `{ phone, password }` |
| GET | `/auth/me` | 当前用户 |
| POST | `/auth/password/change` | 修改密码 `{ old_password, new_password }` 🔒 |
| POST | `/auth/password/reset/sms` | 忘记密码 `{ phone, code, new_password }` |

## 用户业务 🔒

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/PUT | `/periods` | 追踪周期 |
| GET/POST/PUT/DELETE | `/channels` | 渠道 |
| GET | `/recommendations/channels/{id}/detail` | 渠道详情统计 |
| GET/POST | `/recommendations` | 推荐列表/录入 |
| GET | `/recommendations/search` | 搜索 |
| GET | `/recommendations/{id}` | 详情 |
| GET | `/dashboard` | 总览 |
| GET | `/stocks/lookup?code=` | 查股票名称 |

## 管理后台 🔒 admin

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/dashboard` | 运营总览 |
| GET | `/admin/stocks` | 全部股票 |
| GET | `/admin/stocks/{code}` | 股票详情 |
| GET | `/admin/channels` | 全部渠道 |
| GET | `/admin/channels/{id}` | 渠道详情+分周期业绩 |
| GET | `/admin/records` | 全部推荐 |
| POST | `/admin/worker/run` | 手动触发节点抓取 |

完整交互式文档：启动后访问 `/docs`
