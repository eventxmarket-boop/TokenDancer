<template>
  <div class="admin-dashboard">
    <div class="page-title-row">
      <h1 class="page-title">管理后台总览</h1>
      <button class="btn-outline-sm" @click="loadAll">🔄 刷新</button>
    </div>

    <!-- ========== 顶部 KPI 统计卡 ========== -->
    <div class="stat-grid">
      <AdminStatCard label="总用户数" :value="stats.totalUsers" icon="👥" />
      <AdminStatCard label="活跃订单数" :value="stats.activeOrders" icon="🧾" />
      <AdminStatCard label="Active Providers" :value="stats.activeProviders" icon="🌐" />
      <AdminStatCard label="Active Keys" :value="stats.activeKeys" icon="🔑" />
      <AdminStatCard label="最近 Usage 记录" :value="stats.recentUsageCount" icon="📊" />
      <AdminStatCard label="最近账本变动" :value="stats.recentLedgerCount" icon="📒" />
    </div>

    <AdminSectionCard title="API 中转状态摘要">
      <template #actions>
        <router-link to="/admin/api-proxy/monitor" class="link-more">进入监控页 →</router-link>
      </template>
      <div class="proxy-summary-grid">
        <div class="proxy-summary-item">
          <span class="proxy-summary-label">健康 Provider</span>
          <strong class="proxy-summary-value">{{ proxyOverview.healthy_provider_count }}</strong>
        </div>
        <div class="proxy-summary-item">
          <span class="proxy-summary-label">24h 成功率</span>
          <strong class="proxy-summary-value">{{ proxyOverview.success_rate_24h }}%</strong>
        </div>
        <div class="proxy-summary-item">
          <span class="proxy-summary-label">24h 失败数</span>
          <strong class="proxy-summary-value">{{ proxyOverview.failed_requests_24h }}</strong>
        </div>
        <div class="proxy-summary-item">
          <span class="proxy-summary-label">24h 平均延迟</span>
          <strong class="proxy-summary-value">{{ proxyOverview.avg_latency_ms_24h ? proxyOverview.avg_latency_ms_24h + 'ms' : '—' }}</strong>
        </div>
      </div>
    </AdminSectionCard>

    <!-- ========== 中部四区块 ========== -->
    <div class="mid-grid">
      <!-- 最近 5 条订单 -->
      <AdminSectionCard title="最近订单">
        <template #actions>
          <router-link to="/admin/orders" class="link-more">查看全部 →</router-link>
        </template>
        <table class="admin-table">
          <thead><tr>
            <th>订单号</th><th>用户</th><th>金额</th><th>状态</th><th>时间</th>
          </tr></thead>
          <tbody>
            <tr v-if="recentOrders.length === 0"><td colspan="5" class="td-empty">暂无订单</td></tr>
            <tr v-for="o in recentOrders" :key="o.id">
              <td><code>{{ o.order_no }}</code></td>
              <td>{{ o.user_email || '—' }}</td>
              <td>¥{{ typeof o.total_amount === 'number' ? o.total_amount.toFixed(2) : o.total_amount }}</td>
              <td><AdminStatusBadge :value="o.status" /></td>
              <td class="td-time">{{ fmtDate(o.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </AdminSectionCard>

      <!-- 最近 5 条账本变动 -->
      <AdminSectionCard title="最近账本变动">
        <template #actions>
          <router-link to="/admin/finance/ledger" class="link-more">查看全部 →</router-link>
        </template>
        <table class="admin-table">
          <thead><tr>
            <th>用户</th><th>操作</th><th>金额</th><th>余额变化</th><th>时间</th>
          </tr></thead>
          <tbody>
            <tr v-if="recentLedger.length === 0"><td colspan="5" class="td-empty">暂无记录</td></tr>
            <tr v-for="l in recentLedger" :key="l.id">
              <td>{{ l.user_email || l.user_id }}</td>
              <td><span class="op-tag">{{ l.operation }}</span></td>
              <td :class="l.amount >= 0 ? 'td-plus' : 'td-minus'">
                {{ l.amount >= 0 ? '+' : '' }}{{ l.amount }}
              </td>
              <td class="td-small">{{ l.balance_before }} → {{ l.balance_after }}</td>
              <td class="td-time">{{ fmtDate(l.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </AdminSectionCard>

      <!-- 最近 5 条 Proxy 异常 -->
      <AdminSectionCard title="最近 Proxy 异常">
        <template #actions>
          <router-link to="/admin/api-proxy/proxy-logs" class="link-more">查看全部 →</router-link>
        </template>
        <table class="admin-table">
          <thead><tr>
            <th>时间</th><th>模型</th><th>Provider</th><th>状态</th><th>错误</th>
          </tr></thead>
          <tbody>
            <tr v-if="recentProxyAnomalies.length === 0"><td colspan="5" class="td-empty">暂无异常</td></tr>
            <tr v-for="p in recentProxyAnomalies" :key="p.id">
              <td class="td-time">{{ fmtDate(p.requested_at) }}</td>
              <td><code>{{ p.public_model_name }}</code></td>
              <td>{{ providerMap[p.provider_id] || p.provider_id || '—' }}</td>
              <td><AdminStatusBadge :value="p.request_status" /></td>
              <td class="td-error">{{ p.error_message ? p.error_message.slice(0, 40) : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </AdminSectionCard>

      <!-- 最近 5 条支付事件 -->
      <AdminSectionCard title="最近支付事件">
        <template #actions>
          <router-link to="/admin/system/payment-events" class="link-more">查看全部 →</router-link>
        </template>
        <table class="admin-table">
          <thead><tr>
            <th>时间</th><th>渠道</th><th>处理结果</th><th>验签结果</th>
          </tr></thead>
          <tbody>
            <tr v-if="recentPaymentEvents.length === 0"><td colspan="4" class="td-empty">暂无事件</td></tr>
            <tr v-for="e in recentPaymentEvents" :key="e.id">
              <td class="td-time">{{ fmtDate(e.received_at) }}</td>
              <td>{{ e.provider }}</td>
              <td><AdminStatusBadge :value="e.processed_result" /></td>
              <td>
                <AdminStatusBadge
                  :value="e.verify_result === 'passed' ? 'success' : e.verify_result === 'failed' ? 'failed' : 'default'"
                  :label="e.verify_result"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </AdminSectionCard>
    </div>

    <!-- ========== 下部风险提示 ========== -->
    <div v-if="riskAlerts.length > 0" class="risk-section">
      <div class="risk-title">⚠️ 风险提示</div>
      <div class="risk-grid">
        <div v-for="alert in riskAlerts" :key="alert.id" :class="['risk-card', 'risk-' + alert.level]">
          <div class="risk-icon">{{ alert.icon }}</div>
          <div class="risk-body">
            <div class="risk-label">{{ alert.label }}</div>
            <div class="risk-desc">{{ alert.desc }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 底部：系统状态 ========== -->
    <AdminSectionCard title="系统状态">
      <div class="system-status">
        <div class="status-item">
          <span class="status-dot dot-green"></span>
          <span>后端服务 <code>http://127.0.0.1:8011</code></span>
          <AdminStatusBadge label="正常" type="success" />
        </div>
        <div class="status-item">
          <span class="status-dot dot-green"></span>
          <span>数据库 <code>demo_platform.db</code></span>
          <AdminStatusBadge label="正常" type="success" />
        </div>
        <div class="status-item">
          <span :class="['status-dot', emailConfigured ? 'dot-green' : 'dot-gray']"></span>
          <span>邮件服务</span>
          <AdminStatusBadge :label="emailConfigured ? '已配置' : '未配置'" :type="emailConfigured ? 'success' : 'default'" />
        </div>
        <div class="status-item">
          <span class="status-dot dot-gray"></span>
          <span>支付网关</span>
          <AdminStatusBadge label="沙箱模式" type="default" />
        </div>
      </div>
    </AdminSectionCard>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import AdminStatCard from '@/components/admin/AdminStatCard.vue'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminStatusBadge from '@/components/admin/AdminStatusBadge.vue'
import { adminOrdersApi, adminProvidersApi, adminProviderKeysApi } from '@/api/admin'
import { adminFinanceApi } from '@/api/adminFinance'
import { adminProxyMonitorApi } from '@/api/adminProxyMonitor'
import { adminProxyLogsApi } from '@/api/adminProxyLogs'
import { adminSystemApi } from '@/api/adminSystem'

const stats = reactive({
  totalUsers: undefined as number | undefined,
  activeOrders: undefined as number | undefined,
  activeProviders: undefined as number | undefined,
  activeKeys: undefined as number | undefined,
  recentUsageCount: undefined as number | undefined,
  recentLedgerCount: undefined as number | undefined,
})

const recentOrders = ref<any[]>([])
const recentLedger = ref<any[]>([])
const recentProxyAnomalies = ref<any[]>([])
const recentPaymentEvents = ref<any[]>([])
const providerMap = ref<Record<number, string>>({})
const riskAlerts = ref<any[]>([])
const emailConfigured = ref(false)
const proxyOverview = reactive({
  healthy_provider_count: 0,
  success_rate_24h: 0,
  failed_requests_24h: 0,
  avg_latency_ms_24h: 0,
})

const fmtDate = (d: string) => {
  if (!d) return '—'
  return new Date(d).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadAll = async () => {
  riskAlerts.value = []
  await Promise.allSettled([
    loadOverview(),
    loadOrders(),
    loadProviders(),
    loadLedger(),
    loadProxyOverview(),
    loadProxyAnomalies(),
    loadPaymentEvents(),
  ])
}

const loadProxyOverview = async () => {
  try {
    const res = await adminProxyMonitorApi.overview()
    proxyOverview.healthy_provider_count = res.healthy_provider_count || 0
    proxyOverview.success_rate_24h = res.success_rate_24h || 0
    proxyOverview.failed_requests_24h = res.failed_requests_24h || 0
    proxyOverview.avg_latency_ms_24h = res.avg_latency_ms_24h || 0
  } catch (e) {
    console.warn('proxy monitor overview 加载失败:', e)
  }
}

const loadOverview = async () => {
  try {
    const overview = await adminFinanceApi.overview()
    stats.totalUsers = overview.user_count
    stats.recentUsageCount = overview.usage_count
    stats.recentLedgerCount = overview.ledger_count
  } catch (e) {
    console.warn('finance/overview 加载失败:', e)
  }
}

const loadOrders = async () => {
  try {
    const orders = await adminOrdersApi.list({ limit: 5 })
    recentOrders.value = orders
    stats.activeOrders = orders.filter((o: any) => ['pending', 'paid'].includes(o.status)).length
  } catch (e) {
    console.warn('orders 加载失败:', e)
  }
}

const loadProviders = async () => {
  try {
    const providers = await adminProvidersApi.list()
    const keys = await adminProviderKeysApi.list()
    stats.activeProviders = providers.filter((p: any) => p.is_active).length
    stats.activeKeys = keys.filter((k: any) => k.status === 'active').length
    providerMap.value = Object.fromEntries(providers.map((p: any) => [p.id, p.name]))

    // 风险：unhealthy providers
    providers.forEach((p: any) => {
      if (p.health_status === 'unreachable' || p.health_status === 'degraded') {
        riskAlerts.value.push({
          id: 'provider-' + p.id,
          icon: '🌐',
          level: p.health_status === 'unreachable' ? 'danger' : 'warning',
          label: `Provider 不健康：${p.name}`,
          desc: `当前状态：${p.health_status}，最后检查：${p.last_health_check_at ? fmtDate(p.last_health_check_at) : '—'}`,
        })
      }
    })
  } catch (e) {
    console.warn('providers/keys 加载失败:', e)
  }
}

const loadLedger = async () => {
  try {
    const res = await adminFinanceApi.ledger({ limit: 5 })
    recentLedger.value = res.records
  } catch (e) {
    console.warn('ledger 加载失败:', e)
  }
}

const loadProxyAnomalies = async () => {
  try {
    const res: any = await adminProxyLogsApi.list({ request_status: 'error', limit: 100, offset: 0 })
    const records = Array.isArray(res) ? res : (res?.records ?? [])
    recentProxyAnomalies.value = records.slice(0, 5)
  } catch (e) {
    console.warn('proxy logs 加载失败:', e)
  }
}

const loadPaymentEvents = async () => {
  try {
    const res = await adminSystemApi.paymentEvents({ limit: 100 })
    const records = res.records || []
    recentPaymentEvents.value = records.slice(0, 5)

    // 风险：最近有验签失败
    const recentFailures = records.filter((e: any) => e.verify_result === 'failed')
    if (recentFailures.length > 0) {
      riskAlerts.value.push({
        id: 'webhook-verify',
        icon: '🔐',
        level: 'danger',
        label: 'Webhook 验签失败',
        desc: `最近 ${recentFailures.length} 条支付事件验签失败，请检查 Webhook Secret 配置`,
      })
    }
  } catch (e) {
    console.warn('payment events 加载失败:', e)
  }
}

onMounted(loadAll)
</script>

<style scoped>
.page-title-row {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 24px;
}
.page-title { font-size: 20px; font-weight: 700; color: #1a1a2e; }

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.proxy-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
}
.proxy-summary-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px 18px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
}
.proxy-summary-label {
  font-size: 12px;
  color: #888;
}
.proxy-summary-value {
  font-size: 24px;
  color: #1a1a2e;
}
.mid-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}
@media (max-width: 900px) { .mid-grid { grid-template-columns: 1fr; } }

.link-more { font-size: 12px; color: #1677ff; text-decoration: none; }
.link-more:hover { text-decoration: underline; }

.admin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.admin-table th {
  text-align: left; padding: 10px 12px; font-size: 11px; font-weight: 700;
  color: #999; text-transform: uppercase; letter-spacing: 0.5px;
  background: #fafafa; border-bottom: 1px solid #f0f0f0;
}
.admin-table td { padding: 10px 12px; border-bottom: 1px solid #f5f5f5; color: #333; }
.admin-table tr:last-child td { border-bottom: none; }
.admin-table code { font-size: 11px; background: #f5f5f5; padding: 1px 5px; border-radius: 3px; }
.td-empty { text-align: center; color: #bbb; padding: 32px !important; }
.td-time { white-space: nowrap; color: #888; font-size: 12px; }
.td-small { font-size: 11px; color: #888; }
.td-error { font-size: 11px; color: #ff4d4f; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.td-plus { color: #52c41a; font-weight: 600; }
.td-minus { color: #ff4d4f; font-weight: 600; }
.op-tag { font-size: 11px; background: #f0f0ff; color: #5b53ff; padding: 1px 5px; border-radius: 3px; }

/* Risk section */
.risk-section { margin-bottom: 24px; }
.risk-title { font-size: 14px; font-weight: 700; color: #1a1a2e; margin-bottom: 12px; }
.risk-grid { display: flex; flex-direction: column; gap: 10px; }
.risk-card {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 14px 18px; border-radius: 8px; border: 1px solid transparent;
}
.risk-danger { background: #fff1f0; border-color: #ffccc7; }
.risk-warning { background: #fffbe6; border-color: #ffe58f; }
.risk-icon { font-size: 18px; flex-shrink: 0; margin-top: 1px; }
.risk-body { flex: 1; }
.risk-label { font-size: 13px; font-weight: 600; color: #333; }
.risk-desc { font-size: 12px; color: #666; margin-top: 2px; }

/* System status */
.system-status { padding: 8px 0; }
.status-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 20px; border-bottom: 1px solid #f5f5f5;
  font-size: 13px; color: #555;
}
.status-item:last-child { border-bottom: none; }
.status-item code { font-size: 11px; background: #f5f5f5; padding: 1px 5px; border-radius: 3px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot-green { background: #52c41a; }
.dot-gray { background: #d9d9d9; }
.dot-red { background: #ff4d4f; }
.dot-yellow { background: #faad14; }
</style>
