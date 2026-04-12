<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">Proxy 运行状态</h1>
      <div class="title-actions">
        <button class="btn-outline-sm" @click="fetchLogs">🔄 刷新</button>
      </div>
    </div>

    <!-- KPI -->
    <div class="kpi-grid">
      <AdminStatCard label="最近24h 请求数" :value="kpi.total" icon="📡" />
      <AdminStatCard label="最近24h 失败数" :value="kpi.failed" icon="❌" />
      <AdminStatCard label="成功率" :value="kpi.successRate" icon="✅" />
      <AdminStatCard label="平均延迟" :value="kpi.avgLatency" icon="⚡" />
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载中…</span>
    </div>
    <div v-else-if="error" class="error-state">
      <span class="error-msg">{{ error }}</span>
      <button class="btn-outline-sm" @click="fetchLogs">重试</button>
    </div>
    <div v-else>
      <AdminSectionCard>
        <AdminTableToolbar>
          <AdminFilterBar>
            <input class="filter-input" placeholder="公版模型名" v-model="filters.public_model_name" @input="debouncedFetch" />
            <select class="filter-select" v-model="filters.provider_id" @change="fetchLogs">
              <option value="">全部渠道</option>
              <option v-for="p in providers" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
            <select class="filter-select" v-model="filters.request_status" @change="fetchLogs">
              <option value="">全部状态</option>
              <option value="success">success</option>
              <option value="failed">failed</option>
              <option value="rate_limited">rate_limited</option>
            </select>
            <input class="filter-input" type="date" v-model="filters.date_from" @change="fetchLogs" />
            <input class="filter-input" type="date" v-model="filters.date_to" @change="fetchLogs" />
            <button class="btn-outline-sm" @click="resetFilters">重置</button>
          </AdminFilterBar>
        </AdminTableToolbar>

        <div class="table-wrap">
          <table class="admin-table">
            <thead><tr>
              <th>时间</th><th>公版模型</th><th>渠道</th><th>状态</th><th>Total Tokens</th><th>Cost($)</th><th>延迟</th><th>错误信息</th><th>策略</th>
            </tr></thead>
            <tbody>
              <tr v-if="logs.length === 0"><td colspan="9" class="td-center td-pad">暂无日志</td></tr>
              <tr v-else v-for="log in logs" :key="log.id">
                <td>{{ fmtTime(log.requested_at) }}</td>
                <td><strong>{{ log.public_model_name }}</strong></td>
                <td>{{ providerMap[log.provider_id] || log.provider_id || '—' }}</td>
                <td><span :class="statusBadgeClass(log.request_status)">{{ log.request_status }}</span></td>
                <td>{{ log.total_tokens?.toLocaleString() || '—' }}</td>
                <td>{{ typeof log.cost === 'number' ? '$' + log.cost.toFixed(4) : '—' }}</td>
                <td>{{ log.latency_ms ? log.latency_ms + 'ms' : '—' }}</td>
                <td class="td-error">{{ log.error_message || '—' }}</td>
                <td>{{ log.policy_type || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页 -->
        <div class="pagination-bar">
          <span class="page-info">本页 {{ logs.length }} 条</span>
          <div class="page-controls">
            <button class="btn-outline-sm" :disabled="offset === 0" @click="changePage(-1)">上一页</button>
            <span class="page-num">{{ Math.floor(offset / limit) + 1 }}</span>
            <button class="btn-outline-sm" :disabled="logs.length < limit" @click="changePage(1)">下一页</button>
          </div>
        </div>
      </AdminSectionCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { adminProxyLogsApi } from '@/api/adminProxyLogs'
import { adminProvidersApi } from '@/api/adminProviders'

const loading = ref(true)
const error = ref('')
const logs = ref<any[]>([])
const providers = ref<any[]>([])
const limit = 50
const offset = ref(0)
const total = ref(0)
let debounceTimer: ReturnType<typeof setTimeout> | null = null

const filters = reactive({
  public_model_name: '',
  provider_id: '',
  request_status: '',
  date_from: '',
  date_to: '',
})

const kpi = reactive({ total: 0, failed: 0, successRate: '—', avgLatency: '—' })

const providerMap = computed(() => {
  const m: Record<number, string> = {}
  providers.value.forEach((p: any) => { m[p.id] = p.name })
  return m
})

function computeKpi(data: any[]) {
  kpi.total = data.length
  kpi.failed = data.filter((l: any) => l.request_status === 'failed').length
  kpi.successRate = data.length > 0 ? ((kpi.total - kpi.failed) / kpi.total * 100).toFixed(1) + '%' : '—'
  const lats = data.filter((l: any) => l.latency_ms).map((l: any) => l.latency_ms)
  kpi.avgLatency = lats.length > 0 ? (Math.round(lats.reduce((a: number, b: number) => a + b, 0) / lats.length)) + 'ms' : '—'
}

async function fetchLogs() {
  loading.value = true
  error.value = ''
  try {
    const params: any = { limit, offset: offset.value }
    if (filters.public_model_name) params.public_model_name = filters.public_model_name
    if (filters.provider_id) params.provider_id = Number(filters.provider_id)
    if (filters.request_status) params.request_status = filters.request_status
    if (filters.date_from) params.date_from = filters.date_from
    if (filters.date_to) params.date_to = filters.date_to

    const [logData, prov] = await Promise.all([
      adminProxyLogsApi.list(params) as Promise<any[]>,
      adminProvidersApi.list() as Promise<any[]>,
    ])
    logs.value = logData
    providers.value = prov
    total.value = (logData as any).length || 0
    computeKpi(logData as any[])
  } catch (e: any) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function debouncedFetch() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchLogs, 400)
}

function resetFilters() {
  filters.public_model_name = ''
  filters.provider_id = ''
  filters.request_status = ''
  filters.date_from = ''
  filters.date_to = ''
  offset.value = 0
  fetchLogs()
}

function changePage(delta: number) {
  offset.value = Math.max(0, offset.value + delta * limit)
  fetchLogs()
}

function fmtTime(ts: string | null) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('zh-CN')
}

function statusBadgeClass(s: string) {
  if (s === 'success') return 'badge-success'
  if (s === 'failed') return 'badge-danger'
  if (s === 'rate_limited') return 'badge-warning'
  return 'badge-default'
}

fetchLogs()
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
.td-error { color: #ff4d4f; font-size: 12px; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.badge-success { background: #f6ffed; color: #52c41a; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-danger { background: #fff1f0; color: #ff4d4f; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-warning { background: #fffbe6; color: #faad14; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-default { background: #f5f5f5; color: #888; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.pagination-bar { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-top: 1px solid #f0f0f0; }
.page-info { font-size: 13px; color: #888; }
.page-controls { display: flex; align-items: center; gap: 8px; }
.page-num { font-size: 13px; color: #666; padding: 0 8px; }
</style>
