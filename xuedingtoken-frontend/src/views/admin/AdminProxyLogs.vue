<template>
  <div class="page-container">
    <h1 class="page-title">请求日志</h1>

    <AdminSectionCard>
      <AdminTableToolbar>
        <AdminFilterBar>
          <input class="filter-input" placeholder="公版模型名" v-model="filters.public_model_name" @input="debouncedFetch" />
          <select class="filter-select" v-model="filters.request_status" @change="fetchLogs">
            <option value="">全部状态</option>
            <option value="success">success</option>
            <option value="error">error</option>
            <option value="timeout">timeout</option>
            <option value="rate_limited">rate_limited</option>
          </select>
          <select class="filter-select" v-model="filters.provider_id" @change="fetchLogs">
            <option value="">全部渠道</option>
            <option v-for="provider in providers" :key="provider.id" :value="provider.id">{{ provider.name }}</option>
          </select>
          <input class="filter-input" type="date" v-model="filters.date_from" @change="fetchLogs" />
          <input class="filter-input" type="date" v-model="filters.date_to" @change="fetchLogs" />
          <button class="btn-outline-sm" @click="resetFilters">重置</button>
          <button class="btn-outline-sm" @click="fetchLogs">🔄 刷新</button>
        </AdminFilterBar>
      </AdminTableToolbar>

      <div v-if="stats" class="stats-bar">
        <div class="stat-chip">
          <span class="stat-label">总数</span>
          <span class="stat-val">{{ stats.total }}</span>
        </div>
        <div class="stat-chip stat-success">
          <span class="stat-label">成功率</span>
          <span class="stat-val">{{ stats.successRate }}%</span>
        </div>
        <div class="stat-chip stat-danger">
          <span class="stat-label">失败</span>
          <span class="stat-val">{{ stats.failed }}</span>
        </div>
        <div class="stat-chip">
          <span class="stat-label">总 Cost</span>
          <span class="stat-val">{{ stats.total_cost ? '$' + stats.total_cost.toFixed(4) : '—' }}</span>
        </div>
        <div class="stat-chip">
          <span class="stat-label">总 Tokens</span>
          <span class="stat-val">{{ stats.total_tokens?.toLocaleString() || '—' }}</span>
        </div>
      </div>

      <div class="table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>请求</th>
              <th>用户</th>
              <th>模型</th>
              <th>路由</th>
              <th>状态</th>
              <th>用量 / 成本</th>
              <th>错误 / 失败链</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="8" class="td-center td-pad">加载中…</td></tr>
            <tr v-else-if="error"><td colspan="8" class="td-center td-pad td-error">{{ error }}</td></tr>
            <tr v-else-if="logs.length === 0"><td colspan="8" class="td-center td-pad"><AdminEmptyState icon="📋" title="暂无日志" /></td></tr>
            <tr v-else v-for="log in logs" :key="log.id" class="tr-body" @click="openDetail(log)">
              <td class="td-time">{{ fmtTime(log.requested_at) }}</td>
              <td>
                <code class="req-id">{{ (log.request_id || '-').slice(0, 18) }}</code>
                <div class="sub-line">API Key {{ log.user_api_key_id || '—' }}</div>
              </td>
              <td>
                <div>{{ log.user_id || '—' }}</div>
                <div class="sub-line">Provider Key {{ log.provider_key_id || '—' }}</div>
              </td>
              <td>
                <strong>{{ log.public_model_name }}</strong>
                <div class="sub-line">上游 {{ log.provider_model_name || '—' }}</div>
              </td>
              <td>
                <div>{{ providerMap[log.provider_id] || log.provider_id || '—' }}</div>
                <div class="sub-line">{{ log.policy_type || 'fixed' }} / fallback {{ log.fallback_triggered ? 'yes' : 'no' }}</div>
                <div class="sub-line">provider切换 {{ log.provider_switch_count ?? 0 }}，key切换 {{ log.key_switch_count ?? 0 }}</div>
              </td>
              <td><AdminStatusBadge :value="log.request_status" /></td>
              <td>
                <div>{{ (log.total_tokens || 0).toLocaleString() }} tokens</div>
                <div class="sub-line">in {{ log.input_tokens || 0 }} / out {{ log.output_tokens || 0 }}</div>
                <div class="cost-line">{{ typeof log.cost === 'number' ? '$' + log.cost.toFixed(4) : '—' }} / {{ log.latency_ms ? log.latency_ms + 'ms' : '—' }}</div>
              </td>
              <td>
                <div class="error-preview">{{ log.error_message || '—' }}</div>
                <div v-if="log.failure_chain_summary" class="failure-preview">{{ log.failure_chain_summary }}</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination-bar">
        <span class="page-info">本页 {{ logs.length }} 条</span>
        <div class="page-controls">
          <button class="btn-outline-sm" :disabled="offset === 0" @click="changePage(-1)">上一页</button>
          <span class="page-num">{{ Math.floor(offset / limit) + 1 }}</span>
          <button class="btn-outline-sm" @click="changePage(1)">下一页</button>
        </div>
      </div>
    </AdminSectionCard>

    <AdminDetailDrawer v-model="showDetail" title="请求详情">
      <template v-if="selectedLog">
        <div class="detail-section-title">基本信息</div>
        <div class="detail-grid">
          <div class="detail-row"><span class="detail-label">Request ID</span><code>{{ selectedLog.request_id || '—' }}</code></div>
          <div class="detail-row"><span class="detail-label">用户ID</span><span>{{ selectedLog.user_id || '—' }}</span></div>
          <div class="detail-row"><span class="detail-label">API Key ID</span><span>{{ selectedLog.user_api_key_id || '—' }}</span></div>
          <div class="detail-row"><span class="detail-label">Provider</span><span>{{ providerMap[selectedLog.provider_id] || selectedLog.provider_id || '—' }}</span></div>
          <div class="detail-row"><span class="detail-label">Provider Key ID</span><span>{{ selectedLog.provider_key_id || '—' }}</span></div>
        </div>

        <div class="detail-section-title detail-gap">模型信息</div>
        <div class="detail-grid">
          <div class="detail-row"><span class="detail-label">公版模型</span><span>{{ selectedLog.public_model_name }}</span></div>
          <div class="detail-row"><span class="detail-label">上游模型</span><span>{{ selectedLog.provider_model_name || '—' }}</span></div>
        </div>

        <div class="detail-section-title detail-gap">路由信息</div>
        <div class="detail-grid">
          <div class="detail-row"><span class="detail-label">策略类型</span><span>{{ selectedLog.policy_type || 'fixed' }}</span></div>
          <div class="detail-row"><span class="detail-label">Fallback 触发</span><span>{{ selectedLog.fallback_triggered ? '是' : '否' }}</span></div>
          <div class="detail-row"><span class="detail-label">Provider 切换</span><span>{{ selectedLog.provider_switch_count ?? 0 }}</span></div>
          <div class="detail-row"><span class="detail-label">Key 切换</span><span>{{ selectedLog.key_switch_count ?? 0 }}</span></div>
        </div>

        <div class="detail-section-title detail-gap">用量与成本</div>
        <div class="detail-grid">
          <div class="detail-row"><span class="detail-label">Input Tokens</span><span>{{ selectedLog.input_tokens ?? '—' }}</span></div>
          <div class="detail-row"><span class="detail-label">Output Tokens</span><span>{{ selectedLog.output_tokens ?? '—' }}</span></div>
          <div class="detail-row"><span class="detail-label">Total Tokens</span><span>{{ selectedLog.total_tokens ?? '—' }}</span></div>
          <div class="detail-row"><span class="detail-label">Cost</span><span class="td-cost-lg">${{ typeof selectedLog.cost === 'number' ? selectedLog.cost.toFixed(6) : '—' }}</span></div>
          <div class="detail-row"><span class="detail-label">延迟</span><span>{{ selectedLog.latency_ms ? selectedLog.latency_ms + 'ms' : '—' }}</span></div>
        </div>

        <div class="detail-section-title detail-gap">状态</div>
        <div class="detail-grid">
          <div class="detail-row"><span class="detail-label">状态</span><AdminStatusBadge :value="selectedLog.request_status" /></div>
          <div class="detail-row"><span class="detail-label">请求时间</span><span>{{ selectedLog.requested_at ? new Date(selectedLog.requested_at).toLocaleString('zh-CN') : '—' }}</span></div>
        </div>

        <div v-if="selectedLog.error_message || selectedLog.failure_chain_summary" class="detail-gap">
          <div class="detail-section-title">异常信息</div>
          <div v-if="selectedLog.error_message" class="error-box">{{ selectedLog.error_message }}</div>
          <div v-if="selectedLog.failure_chain_summary" class="failure-box">{{ selectedLog.failure_chain_summary }}</div>
        </div>
      </template>

      <template #footer>
        <button class="btn-outline" @click="showDetail = false">关闭</button>
      </template>
    </AdminDetailDrawer>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminTableToolbar from '@/components/admin/AdminTableToolbar.vue'
import AdminFilterBar from '@/components/admin/AdminFilterBar.vue'
import AdminStatusBadge from '@/components/admin/AdminStatusBadge.vue'
import AdminEmptyState from '@/components/admin/AdminEmptyState.vue'
import AdminDetailDrawer from '@/components/admin/AdminDetailDrawer.vue'
import { adminProxyLogsApi, adminProvidersApi } from '@/api/admin'

const logs = ref<any[]>([])
const providers = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const showDetail = ref(false)
const selectedLog = ref<any>(null)
const stats = ref<{ total: number; failed: number; successRate: number; total_cost: number; total_tokens: number } | null>(null)
const filters = reactive({ public_model_name: '', request_status: '', provider_id: '', date_from: '', date_to: '' })
const limit = 100
const offset = ref(0)

const providerMap = computed(() => Object.fromEntries(providers.value.map(provider => [provider.id, provider.name])))

let debounceTimer: ReturnType<typeof setTimeout>
const debouncedFetch = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchLogs, 350)
}

const fmtTime = (value: string) => value ? new Date(value).toLocaleString('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) : '—'

const fetchLogs = async () => {
  loading.value = true
  error.value = ''
  try {
    const params: any = { limit, offset: offset.value }
    if (filters.public_model_name) params.public_model_name = filters.public_model_name
    if (filters.request_status) params.request_status = filters.request_status
    if (filters.provider_id) params.provider_id = Number(filters.provider_id)
    if (filters.date_from) params.date_from = filters.date_from
    if (filters.date_to) params.date_to = filters.date_to
    logs.value = await adminProxyLogsApi.list(params)
    computeStats()
  } catch (e: any) {
    error.value = `加载失败：${e.message || ''}`
    logs.value = []
    stats.value = null
  } finally {
    loading.value = false
  }
}

const computeStats = () => {
  if (!logs.value.length) {
    stats.value = null
    return
  }
  const success = logs.value.filter((item: any) => item.request_status === 'success').length
  const failed = logs.value.length - success
  stats.value = {
    total: logs.value.length,
    failed,
    successRate: Number(((success / logs.value.length) * 100).toFixed(2)),
    total_cost: logs.value.reduce((sum: number, item: any) => sum + Number(item.cost || 0), 0),
    total_tokens: logs.value.reduce((sum: number, item: any) => sum + Number(item.total_tokens || 0), 0),
  }
}

const changePage = (delta: number) => {
  offset.value = Math.max(0, offset.value + delta * limit)
  fetchLogs()
}

const resetFilters = () => {
  Object.assign(filters, { public_model_name: '', request_status: '', provider_id: '', date_from: '', date_to: '' })
  offset.value = 0
  fetchLogs()
}

const openDetail = (log: any) => {
  selectedLog.value = log
  showDetail.value = true
}

fetchLogs()
adminProvidersApi.list().then(rows => { providers.value = rows }).catch(() => {})
</script>

<style scoped>
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; margin-bottom:20px; }
.stats-bar { display:flex; gap:12px; padding:12px 20px; background:#fafafa; border-bottom:1px solid #f0f0f0; flex-wrap:wrap; }
.stat-chip { display:flex; flex-direction:column; align-items:center; gap:2px; padding:6px 16px; background:#fff; border:1px solid #f0f0f0; border-radius:8px; }
.stat-label { font-size:11px; color:#888; }
.stat-val { font-size:15px; font-weight:700; color:#1a1a2e; }
.stat-success .stat-val { color:#52c41a; }
.stat-danger .stat-val { color:#ff4d4f; }
.table-wrap { overflow-x:auto; }
.admin-table { width:100%; border-collapse:collapse; font-size:13px; }
.admin-table th { text-align:left; padding:10px 14px; font-size:11px; font-weight:700; color:#999; text-transform:uppercase; letter-spacing:0.5px; background:#fafafa; border-bottom:1px solid #f0f0f0; white-space:nowrap; }
.admin-table td { padding:10px 14px; border-bottom:1px solid #f5f5f5; color:#333; vertical-align:top; }
.tr-body:hover td { background:#fafafa; }
.tr-body:hover { cursor:pointer; }
.td-center { text-align:center; }
.td-pad { padding:32px !important; }
.td-error { color:#ff4d4f; }
.td-time { font-size:12px; color:#888; white-space:nowrap; }
.req-id { font-size:10px; background:#f5f5f5; padding:1px 4px; border-radius:3px; color:#666; }
.sub-line { margin-top:4px; font-size:12px; color:#667085; }
.cost-line { margin-top:6px; font-weight:600; color:#1677ff; }
.error-preview, .failure-preview { max-width:280px; white-space:normal; word-break:break-word; line-height:1.45; }
.error-preview { color:#b42318; }
.failure-preview { margin-top:6px; color:#475467; font-size:12px; }
.filter-input, .filter-select { font-size:13px; padding:6px 10px; border:1px solid #e8e8e8; border-radius:6px; background:#fff; outline:none; color:#333; }
.filter-input:focus, .filter-select:focus { border-color:#1677ff; }
.btn-outline-sm { font-size:12px; padding:5px 12px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.pagination-bar { display:flex; align-items:center; justify-content:space-between; padding:12px 20px; border-top:1px solid #f0f0f0; }
.page-info { font-size:13px; color:#888; }
.page-controls { display:flex; align-items:center; gap:8px; }
.page-num { font-size:13px; color:#666; padding:0 8px; }
.detail-section-title { font-size:13px; font-weight:700; color:#1a1a2e; margin:0 0 12px; padding-bottom:8px; border-bottom:1px solid #f0f0f0; }
.detail-gap { margin-top:20px; }
.detail-grid { display:flex; flex-direction:column; }
.detail-row { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:9px 0; border-bottom:1px solid #f5f5f5; font-size:13px; }
.detail-row:last-child { border-bottom:none; }
.detail-label { color:#888; font-size:12px; font-weight:600; }
code { font-size:11px; background:#f5f5f5; padding:1px 5px; border-radius:3px; }
.error-box, .failure-box { border-radius:6px; padding:12px; font-size:12px; white-space:pre-wrap; word-break:break-all; }
.error-box { background:#fff1f0; border:1px solid #ffccc7; color:#ff4d4f; }
.failure-box { margin-top:10px; background:#f8fafc; border:1px solid #e2e8f0; color:#334155; }
.btn-outline { font-size:13px; padding:8px 18px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.td-cost-lg { font-size:18px; font-weight:700; color:#1677ff; }
</style>
