<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">系统总览</h1>
      <div class="title-actions">
        <button class="btn-outline-sm" @click="fetchAll">🔄 刷新</button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载中…</span>
    </div>
    <div v-else-if="error" class="error-state">
      <span class="error-msg">{{ error }}</span>
      <button class="btn-outline-sm" @click="fetchAll">重试</button>
    </div>
    <div v-else>

      <!-- KPI 卡片 -->
      <div class="kpi-grid">
        <AdminStatCard label="活跃渠道" :value="stats.activeProviders" icon="🌐" />
        <AdminStatCard label="不健康渠道" :value="stats.unhealthyProviders" icon="⚠️" />
        <AdminStatCard label="活跃 Key" :value="stats.activeKeys" icon="🔑" />
        <AdminStatCard label="无效 Key" :value="stats.invalidKeys" icon="🚫" />
        <AdminStatCard label="最近24h Proxy 请求" :value="stats.proxyRequests24h" icon="📡" />
        <AdminStatCard label="最近24h 失败数" :value="stats.proxyFailures24h" icon="❌" />
        <AdminStatCard label="Webhook 事件数" :value="stats.webhookEvents" icon="🧾" />
        <AdminStatCard label="验签失败数" :value="stats.verifyFailures" icon="🔒" />
      </div>

      <!-- 最近健康检查 -->
      <AdminSectionCard title="最近健康检查结果">
        <div class="table-wrap">
          <table class="admin-table">
            <thead><tr>
              <th>ID</th><th>渠道名称</th><th>类型</th><th>健康状态</th><th>最后检查时间</th>
            </tr></thead>
            <tbody>
              <tr v-if="recentHealthChecks.length === 0"><td colspan="5" class="td-center td-pad">暂无数据</td></tr>
              <tr v-else v-for="p in recentHealthChecks" :key="p.id">
                <td>{{ p.id }}</td>
                <td>{{ p.name }}</td>
                <td>{{ p.provider_type }}</td>
                <td><span :class="healthBadgeClass(p.health_status)">{{ healthLabel(p.health_status) }}</span></td>
                <td>{{ fmtTime(p.last_health_check_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </AdminSectionCard>

      <!-- 最近 Proxy 失败 -->
      <AdminSectionCard title="最近 Proxy 失败">
        <div class="table-wrap">
          <table class="admin-table">
            <thead><tr>
              <th>时间</th><th>公版模型</th><th>渠道</th><th>状态</th><th>错误信息</th>
            </tr></thead>
            <tbody>
              <tr v-if="recentProxyFailures.length === 0"><td colspan="5" class="td-center td-pad">暂无数据</td></tr>
              <tr v-else v-for="log in recentProxyFailures" :key="log.id">
                <td>{{ fmtTime(log.requested_at) }}</td>
                <td>{{ log.public_model_name }}</td>
                <td>{{ log.provider_id }}</td>
                <td><span class="badge-danger">{{ log.request_status }}</span></td>
                <td class="td-error">{{ log.error_message || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </AdminSectionCard>

      <!-- 最近支付事件 -->
      <AdminSectionCard title="最近支付事件">
        <div class="table-wrap">
          <table class="admin-table">
            <thead><tr>
              <th>时间</th><th>Provider</th><th>事件类型</th><th>验签</th><th>处理结果</th><th>错误信息</th>
            </tr></thead>
            <tbody>
              <tr v-if="recentPayments.length === 0"><td colspan="6" class="td-center td-pad">暂无数据</td></tr>
              <tr v-else v-for="e in recentPayments" :key="e.id">
                <td>{{ fmtTime(e.received_at) }}</td>
                <td>{{ e.provider }}</td>
                <td>{{ e.event_type }}</td>
                <td><span :class="verifyBadgeClass(e.verify_result)">{{ e.verify_result || '—' }}</span></td>
                <td><span :class="processedBadgeClass(e.processed_result)">{{ e.processed_result || (e.processed ? '已处理' : '未处理') }}</span></td>
                <td class="td-error">{{ e.error_message || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </AdminSectionCard>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { adminProvidersApi } from '@/api/adminProviders'
import { adminProviderKeysApi } from '@/api/adminProviderKeys'
import { adminProxyLogsApi } from '@/api/adminProxyLogs'
import { adminSystemApi } from '@/api/adminSystem'

const loading = ref(true)
const error = ref('')

const providers = ref<any[]>([])
const keys = ref<any[]>([])
const proxyLogs = ref<any[]>([])
const paymentEvents = ref<any[]>([])

const stats = reactive({
  activeProviders: 0,
  unhealthyProviders: 0,
  activeKeys: 0,
  invalidKeys: 0,
  proxyRequests24h: 0,
  proxyFailures24h: 0,
  webhookEvents: 0,
  verifyFailures: 0,
})

const recentHealthChecks = computed(() => providers.value.slice(0, 5))
const recentProxyFailures = computed(() =>
  proxyLogs.value.filter(l => l.request_status === 'failed').slice(0, 5)
)
const recentPayments = computed(() => paymentEvents.value.slice(0, 5))

async function fetchAll() {
  loading.value = true
  error.value = ''
  try {
    const now = new Date()
    const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000)
    const dateFrom = dayAgo.toISOString().split('T')[0]

    const [prov, keyList, proxy, pay] = await Promise.all([
      adminProvidersApi.list(),
      adminProviderKeysApi.list(),
      adminProxyLogsApi.list({ date_from: dateFrom, limit: 200 }),
      adminSystemApi.paymentEvents({ limit: 20 }),
    ])

    providers.value = prov as any[]
    keys.value = keyList as any[]
    proxyLogs.value = proxy as any[]
    paymentEvents.value = (pay as any).records || []

    stats.activeProviders = (prov as any[]).filter((p: any) => p.is_active).length
    stats.unhealthyProviders = (prov as any[]).filter((p: any) => p.health_status && p.health_status !== 'healthy').length
    stats.activeKeys = (keyList as any[]).filter((k: any) => k.status === 'active').length
    stats.invalidKeys = (keyList as any[]).filter((k: any) => k.status === 'invalid' || k.status === 'disabled').length
    stats.proxyRequests24h = (proxy as any[]).length
    stats.proxyFailures24h = (proxy as any[]).filter((l: any) => l.request_status === 'failed').length
    stats.webhookEvents = paymentEvents.value.length
    stats.verifyFailures = paymentEvents.value.filter((e: any) => e.verify_result === 'failed').length
  } catch (e: any) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function fmtTime(ts: string | null) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('zh-CN')
}

function healthLabel(s: string) {
  const m: Record<string, string> = { healthy: '健康', degraded: '降级', unreachable: '不可达', down: '宕机', unknown: '未知' }
  return m[s] || s || '未知'
}

function healthBadgeClass(s: string) {
  const v = (s || 'unknown').toLowerCase()
  if (v === 'healthy') return 'badge-success'
  if (v === 'degraded') return 'badge-warning'
  if (v === 'unreachable' || v === 'down') return 'badge-danger'
  return 'badge-default'
}

function verifyBadgeClass(v: string) {
  if (v === 'passed') return 'badge-success'
  if (v === 'failed') return 'badge-danger'
  return 'badge-default'
}

function processedBadgeClass(v: string) {
  if (v === 'fulfilled' || v === 'already_paid') return 'badge-success'
  if (v === 'error') return 'badge-danger'
  return 'badge-default'
}

fetchAll()
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 20px; }
.page-title-row { display: flex; align-items: center; justify-content: space-between; }
.page-title { font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 0; }
.title-actions { display: flex; gap: 8px; }
.loading-state, .error-state { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 60px 0; color: #888; }
.error-msg { color: #ff4d4f; }
.spinner { width: 32px; height: 32px; border: 3px solid #e8e8e8; border-top-color: #1677ff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
.table-wrap { overflow-x: auto; }
.admin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.admin-table th { background: #fafafa; padding: 10px 12px; text-align: left; font-weight: 600; color: #666; border-bottom: 1px solid #f0f0f0; white-space: nowrap; }
.admin-table td { padding: 10px 12px; border-bottom: 1px solid #f5f5f5; color: #333; }
.admin-table tr:last-child td { border-bottom: none; }
.td-center { text-align: center; }
.td-pad { padding: 20px; color: #999; }
.td-error { color: #ff4d4f; font-size: 12px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.badge-success { background: #f6ffed; color: #52c41a; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-danger { background: #fff1f0; color: #ff4d4f; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-warning { background: #fffbe6; color: #faad14; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-default { background: #f5f5f5; color: #888; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
</style>
