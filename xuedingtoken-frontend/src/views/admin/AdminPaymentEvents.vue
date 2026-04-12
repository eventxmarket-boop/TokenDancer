<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">支付事件</h1>
      <div class="title-actions">
        <button class="btn-outline-sm" @click="fetchEvents">🔄 刷新</button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载中…</span>
    </div>
    <div v-else-if="error" class="error-state">
      <span class="error-msg">{{ error }}</span>
      <button class="btn-outline-sm" @click="fetchEvents">重试</button>
    </div>
    <div v-else>
      <AdminSectionCard>
        <AdminTableToolbar>
          <AdminFilterBar>
            <select class="filter-select" v-model="filters.provider" @change="fetchEvents">
              <option value="">全部渠道</option>
              <option value="stripe">stripe</option>
              <option value="alipay">alipay</option>
              <option value="wxpay_qr">wxpay_qr</option>
              <option value="custom">custom</option>
            </select>
            <select class="filter-select" v-model="filters.processed_result" @change="fetchEvents">
              <option value="">全部处理结果</option>
              <option value="fulfilled">fulfilled</option>
              <option value="already_paid">already_paid</option>
              <option value="order_not_found">order_not_found</option>
              <option value="error">error</option>
            </select>
            <select class="filter-select" v-model="filters.verify_result" @change="fetchEvents">
              <option value="">全部验签结果</option>
              <option value="passed">passed</option>
              <option value="failed">failed</option>
              <option value="missing_secret">missing_secret</option>
            </select>
          </AdminFilterBar>
        </AdminTableToolbar>

        <div class="table-wrap">
          <table class="admin-table">
            <thead><tr>
              <th>ID</th><th>Provider</th><th>订单ID</th><th>事件类型</th><th>验签结果</th><th>已处理</th><th>处理结果</th><th>错误信息</th><th>收到时间</th>
            </tr></thead>
            <tbody>
              <tr v-if="events.length === 0"><td colspan="9" class="td-center td-pad">暂无事件</td></tr>
              <tr v-else v-for="e in events" :key="e.id">
                <td>{{ e.id }}</td>
                <td>{{ e.provider || '—' }}</td>
                <td>{{ e.order_id || '—' }}</td>
                <td><code class="event-type">{{ e.event_type }}</code></td>
                <td><span :class="verifyBadgeClass(e.verify_result)">{{ e.verify_result || '—' }}</span></td>
                <td><span :class="e.processed ? 'badge-success' : 'badge-warning'">{{ e.processed ? '是' : '否' }}</span></td>
                <td><span :class="processedBadgeClass(e.processed_result)">{{ e.processed_result || '—' }}</span></td>
                <td class="td-error">{{ e.error_message || '—' }}</td>
                <td>{{ fmtTime(e.received_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页 -->
        <div class="pagination-bar">
          <span class="page-info">共 {{ total }} 条</span>
          <div class="page-controls">
            <button class="btn-outline-sm" :disabled="offset === 0" @click="changePage(-1)">上一页</button>
            <span class="page-num">{{ Math.floor(offset / limit) + 1 }} / {{ Math.ceil(total / limit) || 1 }}</span>
            <button class="btn-outline-sm" :disabled="offset + limit >= total" @click="changePage(1)">下一页</button>
          </div>
        </div>
      </AdminSectionCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { adminSystemApi } from '@/api/adminSystem'

const loading = ref(true)
const error = ref('')
const events = ref<any[]>([])
const total = ref(0)
const limit = 50
const offset = ref(0)
const filters = reactive({ provider: '', processed_result: '', verify_result: '' })

async function fetchEvents() {
  loading.value = true
  error.value = ''
  try {
    const res = await adminSystemApi.paymentEvents({
      provider: filters.provider || undefined,
      processed_result: filters.processed_result || undefined,
      verify_result: filters.verify_result || undefined,
      limit,
      offset: offset.value,
    }) as any
    events.value = res.records || []
    total.value = res.total || 0
  } catch (e: any) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function changePage(delta: number) {
  offset.value = Math.max(0, offset.value + delta * limit)
  fetchEvents()
}

function fmtTime(ts: string | null) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('zh-CN')
}

function verifyBadgeClass(v: string | null) {
  if (v === 'passed') return 'badge-success'
  if (v === 'failed') return 'badge-danger'
  if (v === 'missing_secret') return 'badge-warning'
  return 'badge-default'
}

function processedBadgeClass(v: string | null) {
  if (v === 'fulfilled' || v === 'already_paid') return 'badge-success'
  if (v === 'error') return 'badge-danger'
  if (!v) return 'badge-default'
  return 'badge-default'
}

fetchEvents()
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
.table-wrap { overflow-x: auto; }
.admin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.admin-table th { background: #fafafa; padding: 10px 12px; text-align: left; font-weight: 600; color: #666; border-bottom: 1px solid #f0f0f0; white-space: nowrap; }
.admin-table td { padding: 10px 12px; border-bottom: 1px solid #f5f5f5; color: #333; }
.admin-table tr:last-child td { border-bottom: none; }
.td-center { text-align: center; }
.td-pad { padding: 20px; color: #999; }
.td-error { color: #ff4d4f; font-size: 12px; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.event-type { font-size: 11px; background: #f0f0ff; color: #5b53ff; padding: 2px 6px; border-radius: 4px; }
.badge-success { background: #f6ffed; color: #52c41a; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-danger { background: #fff1f0; color: #ff4d4f; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-warning { background: #fffbe6; color: #faad14; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-default { background: #f5f5f5; color: #888; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.pagination-bar { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-top: 1px solid #f0f0f0; }
.page-info { font-size: 13px; color: #888; }
.page-controls { display: flex; align-items: center; gap: 8px; }
.page-num { font-size: 13px; color: #666; }
</style>
