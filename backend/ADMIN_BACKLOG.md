# TokenDancer 管理后台 — 遗留问题清单
> **v5（最终版）** | 更新于 2026-04-11 00:40

---

## 一、已完成的模块

### 运营管理（4个页面）
| 页面 | 状态 | 说明 |
|------|------|------|
| AdminUsers | ✅ 完成 | 列表/筛选/详情抽屉/余额调整/角色修改/禁用解封 |
| AdminOrders | ✅ 完成 | 列表/用户列/详情/改状态二次确认 |
| AdminRedeemCodes | ✅ 完成 | 列表/创建/PATCH更新过期时间/DELETE删除 |
| AdminProducts | ✅ 完成 | 列表/创建/编辑/上下架 |

### API中转管理（5个页面）
| 页面 | 状态 | 说明 |
|------|------|------|
| AdminProviders | ✅ 完成 | CRUD/启停confirm/health_status显示 |
| AdminProviderKeys | ✅ 完成 | Key池/严格脱敏/编辑空不回显 |
| AdminModelRoutes | ✅ 完成 | 模型映射/CRUD/启停 |
| AdminRoutePolicies | ✅ 完成 | 四种策略/CRUD/启停 |
| AdminProxyLogs | ✅ 完成 | 统计栏/筛选/详情抽屉 |

### 安全与架构
| 项目 | 状态 | 说明 |
|------|------|------|
| ProviderKey脱敏 | ✅ 完成 | update时key_masked用明文生成（2026-04-11修复） |
| 登录失败冷却 | ✅ 完成 | T2: 5次/5分钟滑动窗口 |
| 密码强度校验 | ✅ 完成 | T1: 8位+大小写+弱口令黑名单 |
| 限流配置修复 | ✅ 完成 | T3: login用RATE_LIMIT_LOGIN |
| webhook签名校验 | ✅ 完成 | T5: X-Webhook-Secret |
| 生产SECRET_KEY强制 | ✅ 完成 | T6: APP_ENV=prod时校验 |
| Alembic迁移支持 | ✅ 完成 | PostgreSQL兼容 |

---

## 二、后端接口完整对照（最终版）

| 接口 | 方法 | 状态 |
|------|------|------|
| `/admin/users` | GET | ✅ |
| `/admin/users/{id}` | GET/PATCH | ✅ |
| `/admin/orders` | GET | ✅ 含user_email联查 |
| `/admin/orders/{id}` | GET/PATCH | ✅ |
| `/admin/products` | GET/POST | ✅ |
| `/admin/products/{id}` | GET/PATCH | ✅ |
| `/admin/redeem-codes` | GET/POST | ✅ |
| `/admin/redeem-codes/{id}` | PATCH/DELETE | ✅ 2026-04-11新增 |
| `/admin/providers` | GET/POST | ✅ |
| `/admin/providers/{id}` | GET/PATCH | ✅ |
| `/admin/provider-keys` | GET/POST | ✅ |
| `/admin/provider-keys/{id}` | GET/PATCH | ✅ |
| `/admin/model-routes` | GET/POST | ✅ |
| `/admin/model-routes/{id}` | PATCH | ✅ |
| `/admin/route-policies` | GET/POST | ✅ |
| `/admin/route-policies/{id}` | PATCH | ✅ |
| `/admin/proxy-logs` | GET | ✅ 支持多字段筛选 |
| `/admin/dashboard/stats` | GET | ❌ 路由不存在（前端Dashboard页为静态展示）|

---

## 三、剩余问题清单

### P1 — 功能性缺失（影响运营效率）

| # | 模块 | 问题 | 建议 |
|---|------|------|------|
| 1 | ProxyLogs | 无分页 | 后端加 `offset`/`limit` 参数 |
| 2 | Dashboard | 无统计API | 新增 `/admin/dashboard/stats` 接口 |
| 3 | Providers | 无连接测试 | 新增 `POST /admin/providers/{id}/test` |
| 4 | Providers | 无定时健康检查 | 后端定时任务更新 health_status |
| 5 | RoutePolicies | weighted类型无权重UI | 前端区分 policy_type=weighted 时显示权重配置 |

### P2 — 体验优化

| # | 问题 | 建议 |
|---|------|------|
| 6 | 表单弹窗重复代码多 | 抽取 AdminFormModal 组件 |
| 7 | 列表行无 hover 高亮 | 全局加 `.tr-body:hover` 样式 |
| 8 | CSS 分散重复 | 提取公共 admin-table/admin-form 样式 |
| 9 | ProxyLogs 无实时刷新 | WebSocket 或轮询机制 |

---

## 四、源 Key 脱敏最终确认

**策略：** 前端永远拿不到真实 API Key

| 场景 | 行为 |
|------|------|
| 列表页 | 只显示 `key_masked`（如 `sk-abc1****xyz9`） |
| 详情页 | 不展示明文 |
| 编辑时 | `api_key` 字段留空，不回显 |
| 更新时 | `key_masked = mask_api_key(明文)`，`key_encrypted = encrypt_api_key(明文)` |
| schema | `ProviderKeyRead` 不含 `key_encrypted` |

> ⚠️ 2026-04-11 修复确认：`update_provider_key` 中 `key_masked` 原来用密文生成，已改为用原始明文生成

---

## 五、后续开发建议

```
下一步优先（P1）:
  1. 补 /admin/dashboard/stats 接口（提供真实统计数据）
  2. ProxyLogs 加分页（offset/limit）
  3. POST /admin/providers/{id}/test（连接测试）

再下一步（P2）:
  4. AdminFormModal 组件抽取
  5. proxy_chat_completion 真实转发接入
  6. 操作审计日志表
```

---

## 六、当前阶段判定

**管理员后台当前阶段：✅ 完成**

- 9个管理页面全部可操作（非骨架）
- 4个运营模块 CRUD 完整
- 5个 API 中转模块 CRUD 完整
- ProviderKey 脱敏流程安全正确
- 无 P0 问题
- 可作为内部运营平台交付使用

---

## 管理员后台板块第 4 步完成（2026-04-11 06:30）

---

## 管理员后台板块补丁轮（2026-04-11 15:39）

### 问题根因
`client.ts` 的 `ApiClient.request<T>()` 已直接 `return res.json()`（无 axios 包装），API 文件也已直接 `api.get<...>(path, params)` 传参（无 `{ params }` 包装）。但各页面调用时仍用 `res.data.xxx`（axios 习惯），导致数据读取失败。

### 已修复

| # | 文件 | 问题 | 修复 |
|---|------|------|------|
| 1 | `AdminFinanceOverview.vue` | `res.data` ×3 | → `res` |
| 2 | `AdminLedger.vue` | `res.data?.records / total` | → `res?.records / total` |
| 3 | `AdminUsageRecords.vue` | `res.data?.records / total` | → `res?.records / total` |

### 已确认无需修改（本身正确）

| 文件 | 原因 |
|------|------|
| `AdminPaymentEvents.vue` | 已用 `res.records / total`（无 `.data`） |
| `AdminAuditLogs.vue` | 已用 `res.records / total`（无 `.data`） |
| `AdminProxyRuntime.vue` | 已用 `adminProxyLogsApi.list()` + `computeKpi()` 实时计算，无 `proxyOverview` 调用 |
| `adminFinance.ts` | 已直接传 `params`，无 `{ params }` 包装 |
| `adminAudit.ts` | 已直接传 `params`，无 `{ params }` 包装 |
| `adminSystem.ts` | `proxyOverview` 虽未实现但前端无调用，不影响 |

### 构建验证
```
✓ built in 1.51s
```
所有 admin 视图 chunk 均正确生成，无 TypeScript / Vite 报错。

### 剩余 P1/P2 未变（见上方表格）

### 已完成
- AdminDashboard 强化（KPI 卡片 + 中部区块 + 风险提示）
- AdminAuditLogs 新建（审计日志查看 + 筛选 + 分页）
- 状态标签颜色规范统一（healthy=绿 / degraded=黄 / unreachable=红 / unknown=灰）
- 按钮文案统一（新建/保存/启用/停用/删除/刷新）
- AdminLayout 新增"审计日志"菜单入口

### 仍待解决
| 优先级 | 问题 |
|--------|------|
| P1 | 批量导出 CSV 能力 |
| P1 | 深度分页（Users/Orders/Ledger/Usage/ProxyLogs/PaymentEvents） |
| P2 | 前后台联动跳转（Users→Ledger、Orders→PaymentEvents、Provider→Key详情） |
| P2 | 富文本编辑器接入（ContentPages 仍 textarea） |
| P2 | FAQ 结构化问答支持 |
| P2 | `/admin/proxy-runtime/overview` 独立概览接口未建（当前实时计算） |
| P3 | 多实例限流 Redis 共享 |
---

## 全项目全面收口轮（2026-04-11 15:50）

### 已完成
- adminSystem.ts 悬空 proxyOverview 定义已删除
- API 调用规范统一（无 res.data 残留）

### 当前阶段判定
✅ 管理员后台当前阶段完整完成

## 全项目全面收口轮完成（2026-04-11 16:16）

### 已完成
- 财务/系统页联调修复（res.data → res）
- AdminAuditLogs / AdminPaymentEvents / AdminProxyRuntime 联调通过
- API 调用规范统一（全局无 axios 残留）
- adminSystem.ts 悬空定义 proxyOverview 已删除
- 状态标签颜色规范统一

### 当前阶段判定
✅ 管理员后台当前阶段完整完成

## 全项目全面收口轮完成（2026-04-11 16:16）

### 已完成
- 财务/系统页联调修复（res.data → res）
- AdminAuditLogs / AdminPaymentEvents / AdminProxyRuntime 联调通过
- API 调用规范统一（全局无 axios 残留）
- 状态标签颜色规范统一

### 当前阶段判定
✅ 管理员后台当前阶段完整完成
