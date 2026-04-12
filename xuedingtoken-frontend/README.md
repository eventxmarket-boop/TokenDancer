# TokenDancer Frontend

TokenDancer 的 Vue 3 + TypeScript + Vite 前端，包含商城、用户控制台与管理员后台。

## 环境要求

- Node.js 18+
- npm 或 pnpm

## 快速启动

```bash
cd xuedingtoken-frontend

# 1. 安装依赖
npm install

# 2. 配置环境变量（开发环境已有默认值，可跳过）
cp .env.example .env.local

# 3. 启动开发服务器
npm run dev
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|------|
| `VITE_API_BASE_URL` | 后端 API 地址 | `/api`（开发走 Vite 代理，生产填绝对地址） |
| `VITE_APP_ENV` | 环境 | `dev` / `prod` |

**开发模式：** API 请求走 Vite 代理（`/api` → `http://127.0.0.1:8011`），无需手动配置后端地址。开发服务器默认从 `localhost:5181` 启动。

**生产构建：**
```bash
npm run build
# 产物在 dist/ 目录
```

## 主要页面

| 路径 | 说明 | 权限 |
|------|------|------|
| `/` | 商城首页 | 公开 |
| `/products` | 商品列表 | 公开 |
| `/products/:id` | 商品详情 | 公开 |
| `/cart` | 购物车 | 登录 |
| `/auth/login` | 登录 | 公开 |
| `/auth/register` | 注册 | 公开 |
| `/main/dashboard` | 主站 Dashboard | 登录 |
| `/main/keys` | API Key 管理 | 登录 |
| `/main/usage` | 用量记录 | 登录 |
| `/main/redeem` | 兑换码 | 登录 |
| `/main/profile` | 个人资料 | 登录 |
| `/main/client-install` | 客户端部署 | 登录 |

## 技术栈

- Vue 3 (Composition API + `<script setup>`)
- TypeScript
- Pinia（状态管理）
- Vue Router
- Vite
- Axios / Fetch（API client）

## Setup

```bash
cd xuedingtoken-frontend
npm install
cp .env.example .env   # then edit VITE_API_BASE_URL if needed
npm run dev
```

App runs at http://localhost:5173

## Environment

Create `.env` (copy from `.env.example`):

```
VITE_API_BASE_URL=http://127.0.0.1:8011
```

## Tech Stack

- Vue 3 (Composition API + `<script setup>`)
- Pinia (state management)
- Vue Router 4
- Chart.js for dashboard charts
- Vite build tool
