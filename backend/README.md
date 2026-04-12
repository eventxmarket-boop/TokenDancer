# Demo Platform Backend

FastAPI 后端服务，提供商城、主站 API 及管理接口。

## 快速启动

```bash
cd backend

# 1. 创建虚拟环境
python3 -m venv .venv && source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，修改 SECRET_KEY（必须！）

# 4. 初始化数据库（开发环境）
python3 -c "from app.main import app; from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
# 或使用 Alembic 迁移（推荐）:
alembic upgrade head

# 5. 初始化演示数据
python3 scripts/seed_demo_data.py

# 6. 启动服务
uvicorn app.main:app --reload --port 8011
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `SECRET_KEY` | ✅ 必改 | JWT 签名密钥 |
| `DATABASE_URL` | ✅ | SQLite 开发；PostgreSQL 生产 |
| `APP_ENV` | — | `dev` / `prod` |
| `PAYMENT_PROVIDER` | — | `stripe` 或 `mock` |
| `STRIPE_SECRET_KEY` | — | Stripe 密钥（生产） |
| `SMTP_HOST` | — | 邮件发送（生产） |
| `RATE_LIMIT_ENABLED` | — | `true` 开启限流 |
| `EXTRA_CORS_ORIGINS` | — | 额外 CORS 域名（逗号分隔） |

## API 文档

- 开发环境: http://localhost:8011/docs
- ReDoc: http://localhost:8011/redoc

## 测试账号

| 角色 | 邮箱 | 密码 |
|------|------|------|
| Admin | admin@example.com | Admin@123 |
| User | user@example.com | User@123 |

## 安全配置

### SECRET_KEY（必读）
生产环境（`APP_ENV=prod`）启动时，系统会检查 `SECRET_KEY`：
- 长度 < 32 → 拒绝启动
- 为默认值 `change_this...` / `secret` / `password` 等 → 拒绝启动

开发环境仅有 warning 日志，不会阻止启动。

生成强密钥：
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 限流
启用方式：`.env` 中设置 `RATE_LIMIT_ENABLED=true`

| 接口 | 限制 |
|------|------|
| `POST /auth/login` | 10次/分钟（per email） |
| `POST /auth/register` | 5次/分钟（per email） |
| `POST /auth/password` | 5次/分钟（per user） |
| `POST /redeem` | 20次/分钟（per user） |
| `POST /payments/webhook` | 60次/分钟（per IP） |

### 登录失败冷却
连续输错密码 5 次（可配置）后，账户被锁定 5 分钟（可配置），期间无法登录。

### Webhook 安全
- Stripe 模式：使用 Stripe 官方签名验证（`stripe.Webhook.construct_event`）
- Mock/其他：校验 `X-Webhook-Secret` header 必须匹配 `PAYMENT_WEBHOOK_SECRET`
- 已支付订单的重复回调不触发重复发放

### 密码强度
- 最少 8 位
- 必须包含：大写字母 + 小写字母 + 数字
- 常见弱密码（如 `password123`、`12345678`）被拒绝

## 目录结构

```
app/
├── core/           # 配置、数据库、安全、日志
├── models/         # SQLAlchemy 模型
├── schemas/        # Pydantic 请求/响应 schema
├── services/      # 业务逻辑层
├── routers/       # API 路由
│   ├── auth.py        # 登录/注册/个人资料/密码修改
│   ├── products.py    # 商品列表/详情/精选
│   ├── cart.py        # 购物车 CRUD
│   ├── orders.py     # 订单创建/列表/详情
│   ├── redeem.py     # 兑换码兑换/历史
│   ├── keys.py        # API Key 管理
│   ├── usage.py       # 用量查询/写入
│   ├── dashboard.py   # Dashboard 指标
│   ├── admin.py       # 管理接口（需 admin 角色）
│   ├── payments.py    # 支付创建/状态/回调
│   └── profile.py     # 个人资料管理
alembic/             # 数据库迁移
scripts/seed_demo_data.py  # 演示数据初始化
```

## 主要 API 路由

### 公开
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/login` | 用户登录 |
| GET | `/products` | 商品列表 |
| GET | `/products/featured` | 精选商品 |
| GET | `/products/{id}` | 商品详情 |

### 需登录
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dashboard` | Dashboard 指标 |
| GET/POST | `/keys` | Key 管理 |
| DELETE/PATCH | `/keys/{id}` | Key 启停/删除 |
| GET | `/usage` | 用量记录 |
| POST | `/redeem` | 兑换码兑换 |
| GET | `/redeem/history` | 兑换历史 |
| GET/POST | `/cart` | 购物车 |
| POST | `/orders` | 创建订单 |
| GET | `/orders` | 订单列表 |
| POST | `/payments/create` | 创建支付会话 |
| GET | `/payments/{order_id}/status` | 支付状态 |
| GET/PUT | `/auth/profile` | 个人资料 |
| PUT | `/auth/password` | 修改密码 |

### 管理接口（需 admin 角色）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/users` | 用户列表 |
| PATCH | `/admin/users/{id}` | 修改用户状态/角色/余额 |
| GET | `/admin/orders` | 订单列表 |
| PATCH | `/admin/orders/{id}` | 修改订单状态 |
| GET/POST | `/admin/redeem-codes` | 兑换码管理 |

### Webhook
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/payments/webhook` | 支付回调（Stripe 等） |

## 支付接入

1. 在 `.env` 中设置 `PAYMENT_PROVIDER=stripe`
2. 配置 `STRIPE_SECRET_KEY` 和 `STRIPE_WEBHOOK_SECRET`
3. 在 Stripe Dashboard 配置 webhook 指向 `https://your-domain/payments/webhook`
4. 支付成功 → Stripe 回调 → `fulfill_order()` → 权益发放

**开发阶段**：`PAYMENT_PROVIDER=mock`（默认），支付为模拟，不触发真实扣费。

## Alembic 迁移

```bash
# 生成新迁移
alembic revision --autogenerate -m "add new field"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

## 数据库

- 开发: SQLite（`demo_platform.db`）
- 生产: PostgreSQL（修改 `DATABASE_URL`）

迁移后所有表：`users`, `products`, `carts`, `cart_items`, `orders`, `order_items`, `redeem_codes`, `redeem_logs`, `api_keys`, `usage_records`, `balance_ledger`

## 部署

### 开发环境

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入必要配置（SECRET_KEY 必须修改）
alembic upgrade head
uvicorn app.main:app --reload --port 8011
```

### 生产环境（Docker）

```bash
# 1. 克隆项目后，在 docker-compose.yml 所在目录：
cp .env.example .env
# 编辑 .env：填入 SECRET_KEY / DATABASE_URL / PAYMENT_WEBHOOK_SECRET

# 2. 启动：
docker-compose up --build -d

# 3. 初始化数据库（首次或更新后）：
docker-compose exec backend alembic upgrade head

# 4. 健康检查：
docker-compose exec backend python scripts/run_health_checks.py
```

### 健康检查脚本

```bash
# 全部 provider：
python scripts/run_health_checks.py

# 单个 provider：
python scripts/run_health_checks.py --provider-id 1
```

### 日志查看

```bash
# 后端实时日志：
docker-compose logs -f backend

# PostgreSQL 日志（需进入容器）：
docker-compose exec db psql -U demoplat -d demoplat
```

### 定时任务建议

```cron
# 每小时健康检查
0 * * * * /app/scripts/run_health_checks.py >> /var/log/health_checks.log 2>&1
```

### 部署验收 Checklist

- [ ] .env 已配置（SECRET_KEY / DATABASE_URL）
- [ ] PostgreSQL 已可连通
- [ ] `alembic upgrade head` 成功
- [ ] backend 启动成功（`/docs` 可访问）
- [ ] frontend 启动成功
- [ ] admin 登录正常
- [ ] proxy `/chat/completions` 路由存在
- [ ] `POST /payments/webhook` 可访问
