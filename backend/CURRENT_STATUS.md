# TokenDancer CURRENT_STATUS.md — 系统状态快照

> 更新时间：2026-04-11 v5.0.0
> 维护范围：Token API 中转（v1-v4）+ 支付链

---

## 一、支付链当前状态

### 阶段：可用（测试模式）

| 模块 | 状态 | 说明 |
|------|------|------|
| 支付配置（后台） | ✅ 可用 | GET/PUT 正常，格式统一 |
| 支付配置（前台） | ✅ 可用 | Public 接口正常返回数组 |
| 扫码支付页 | ✅ 可用 | AlipayQrPage 加载/展示/错误提示正常 |
| 支付宝人工确认 | ✅ 可用 | 待确认订单列表 + 确认到账 → fulfill |
| Webhook 回调 | ⚠️ 待接入 | 正式支付宝开放平台未接入 |
| Stripe 真实接入 | ❌ 未做 | 仅占位，无真实商户号 |
| 微信支付 | ❌ 未做 | 无商户号 |
| 退款/撤销 | ❌ 未做 | 无业务逻辑 |

### 已知限制
- 正式支付宝开放平台（沙箱/生产）未接入，当前为静态收款码模式
- `alipay_qr_note` 字段已加入 schema 和 service，但数据库表缺少此列（Alembic 未补）
- Webhook 验签：仅 header 级别，无加密签名验签

---

## 二、API 中转四阶段状态

### v1 阶段（最小可用）：✅ 完成
- MinimaxAdapter 成功/失败/usage 解析正确
- 单 Provider 单 Key，最小可跑通

### v2 阶段（单 Provider 多 Key）：✅ 完成
- `provider_key_service.is_key_available()` / `get_available_keys_for_model()` 正确
- 失败切下一把 key：`used_count_today` / `last_used_at` / `last_error` 均更新
- rpm_limit：**未实现**（代码为占位符）

### v3 阶段（多 Provider 分发）：✅ 骨架完成，weighted 静态近似
- `fixed` 策略：✅ 正确执行（provider exhausted → 直接失败，不切 fallback）
- `fallback` 策略：✅ 正确执行（provider exhausted → 切下一 provider）
- `weighted` 策略：⚠️ **名义支持，实为静态优先级近似**（无真实权重随机）
- `cost_first` 策略：**预留，未实现**
- provider health 过滤：✅ health_status = down/degraded 时跳过
- failure_chain_summary：✅ 同时记录 provider 级和 key 级失败

### v4 阶段（外部可见性）：✅ 基本可用
- `/admin/proxy-logs`：✅ 返回真实数据，含 policy_type/provider_id/Key-switch-count
- `/admin/proxy-runtime`：✅ 前端正确渲染日志列
- `/admin/routing-status`：✅ 路由列表 + 健康状态展示
- `/admin/system-overview`：✅ KPI 卡片 + 健康检查 + 失败日志

### 未实现功能（需后续迭代）
| 功能 | 状态 |
|------|------|
| Stream 流式响应 | ❌ 未实现 |
| 真实 weighted 权重随机 | ❌ 静态近似 |
| cost_first 动态成本路由 | ❌ 预留 |
| Redis 分布式限流 | ❌ 未实现 |
| 动态成本表 | ❌ 未实现 |
| RPM/TPM 真实限制 | ❌ 未实现 |
| Alembic 迁移补齐（alipay_qr_note 列） | ❌ 未做 |

---

## 三、关键文件清单

### 后端核心
- `app/services/proxy_gateway_service.py` — 路由分发 v3/v4 逻辑
- `app/services/provider_key_service.py` — Key 调度 v2 逻辑
- `app/services/providers/minimax_adapter.py` — Minimax v1 适配器
- `app/services/proxy_log_service.py` — 日志写入
- `app/core/proxy_errors.py` — 异常类型定义
- `app/routers/proxy.py` — 中转入口（统一错误语义）

### 前端核心
- `src/api/client.ts` — 网络层（支持 fetch 异常捕获、404/429/502/504 区分）
- `src/api/adminProxyLogs.ts` — 日志 API（空参数过滤）
- `src/views/admin/AdminProxyLogs.vue` — 日志页（分页修复）
- `src/views/admin/AdminPaymentConfig.vue` — 支付配置页（格式统一）
- `src/views/shop/AlipayQrPage.vue` — 扫码页（已支付状态提示）

### 数据库
- SQLite：`backend/app.db`
- `alembic/versions/001_initial.py` — 初始迁移（alipay_qr_note 列缺失）

---

## 四、运行要求

### 启动后端
```bash
cd /Users/chanzi/.qclaw/workspace/backend
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8011
```

### 启动前端
```bash
cd /Users/chanzi/.qclaw/workspace/xuedingtoken-frontend
npm run dev
```

### 健康检查
```bash
curl http://127.0.0.1:8011/health
```

### 管理员登录
- Email: `admin@example.com`
- Password: `Admin@123`

---

## 五、已修复 Bug 汇总（v5.0.0）

1. **支付配置回显**：GET 返回逗号分隔字符串，前端 load() 正确解析
2. **支付配置保存**：前端发 list[]，service 层规范化存储
3. **Pydantic schema**：所有字段设默认值，避免 422 错误
4. **网络错误处理**：client.ts 捕获 fetch 异常，区分 6 种错误类型
5. **Proxy 日志参数**：`provider_id=""` 空字符串不再发送
6. **Proxy 日志分页**：AdminProxyLogs.vue 分页逻辑修复
7. **Proxy 日志表头**：重复 `<thead>` 清理
8. **fixed 策略 key_rec**：provider exhausted 时 key_rec 未定义问题
9. **Proxy router 错误语义**：不裸返回 str(e)，区分 timeout/connection/500
10. **AlipayQrPage**：订单已支付时显示提示而非空白错误
