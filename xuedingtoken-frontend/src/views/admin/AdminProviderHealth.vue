<template>
  <div class="page-container">
    <div class="page-title-row">
      <div>
        <h1 class="page-title">Provider 健康</h1>
        <p class="page-subtitle">直接查看渠道是否可用、最近 24h 运行态，以及手动探测后的即时反馈。</p>
      </div>
      <div class="title-actions">
        <button class="btn-outline-sm" @click="fetchProviders">🔄 刷新</button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载中…</span>
    </div>
    <div v-else-if="error" class="error-state">
      <span class="error-msg">{{ error }}</span>
      <button class="btn-outline-sm" @click="fetchProviders">重试</button>
    </div>
    <div v-else>
      <AdminSectionCard>
        <div class="table-wrap">
          <table class="admin-table">
            <thead><tr>
              <th>ID</th><th>名称</th><th>类型</th><th>Base URL</th><th>启用</th><th>健康状态</th><th>24h 运行态</th><th>操作</th>
            </tr></thead>
            <tbody>
              <tr v-if="providers.length === 0"><td colspan="8" class="td-center td-pad">暂无渠道</td></tr>
              <tr v-else v-for="provider in providers" :key="provider.id">
                <td>{{ provider.id }}</td>
                <td>
                  <strong>{{ provider.name }}</strong>
                  <div class="sub-line">活跃 Key {{ provider.active_key_count }} / 最后检查 {{ fmtTime(provider.last_health_check_at) }}</div>
                </td>
                <td>{{ provider.provider_type }}</td>
                <td class="td-url">{{ provider.base_url || '—' }}</td>
                <td><AdminStatusBadge :value="provider.is_active ? 'active' : 'disabled'" /></td>
                <td><span :class="healthBadgeClass(provider.health_status)">{{ healthLabel(provider.health_status) }}</span></td>
                <td>
                  <div class="sub-line">请求 {{ provider.request_count_24h }}</div>
                  <div class="sub-line">成功率 {{ provider.success_rate_24h }}%</div>
                  <div class="sub-line">延迟 {{ provider.avg_latency_ms_24h ? provider.avg_latency_ms_24h + 'ms' : '—' }}</div>
                </td>
                <td>
                  <button class="btn-outline-sm" :disabled="checkingIds.has(provider.id)" @click="triggerHealthCheck(provider.id)">
                    {{ checkingIds.has(provider.id) ? '检查中…' : '🩺 健康检查' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </AdminSectionCard>
    </div>

    <div v-if="checkResult" class="toast" :class="checkResult.ok ? 'toast-success' : 'toast-error'">
      {{ checkResult.msg }}
      <button class="toast-close" @click="checkResult = null">×</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminStatusBadge from '@/components/admin/AdminStatusBadge.vue'
import { adminProvidersApi, type AdminProvider } from '@/api/adminProviders'

const loading = ref(true)
const error = ref('')
const providers = ref<AdminProvider[]>([])
const checkingIds = ref(new Set<number>())
const checkResult = ref<{ ok: boolean; msg: string } | null>(null)

async function fetchProviders() {
  loading.value = true
  error.value = ''
  try {
    providers.value = await adminProvidersApi.list()
  } catch (e: any) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function triggerHealthCheck(id: number) {
  checkingIds.value.add(id)
  try {
    const res = await adminProvidersApi.healthCheck(id)
    checkResult.value = {
      ok: res.new_status === 'healthy',
      msg: `${res.name}：${res.old_status} → ${res.new_status}`,
    }
    await fetchProviders()
  } catch (e: any) {
    checkResult.value = { ok: false, msg: '健康检查失败：' + (e?.message || '未知错误') }
  } finally {
    checkingIds.value.delete(id)
  }
  setTimeout(() => { checkResult.value = null }, 4000)
}

function fmtTime(ts?: string | null) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('zh-CN')
}

function healthLabel(status: string) {
  const map: Record<string, string> = { healthy: '健康', degraded: '降级', unreachable: '不可达', down: '宕机', unknown: '未知' }
  return map[status] || status || '未知'
}

function healthBadgeClass(status: string) {
  const value = (status || 'unknown').toLowerCase()
  if (value === 'healthy') return 'badge-success'
  if (value === 'degraded') return 'badge-warning'
  if (value === 'unreachable' || value === 'down') return 'badge-danger'
  return 'badge-default'
}

fetchProviders()
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 20px; }
.page-title-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.page-title { font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 0; }
.page-subtitle { margin: 6px 0 0; color: #667085; font-size: 13px; }
.title-actions { display: flex; gap: 8px; }
.loading-state, .error-state { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 60px 0; color: #888; }
.error-msg { color: #ff4d4f; }
.spinner { width: 32px; height: 32px; border: 3px solid #e8e8e8; border-top-color: #1677ff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.table-wrap { overflow-x: auto; }
.admin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.admin-table th { background: #fafafa; padding: 10px 12px; text-align: left; font-weight: 600; color: #666; border-bottom: 1px solid #f0f0f0; white-space: nowrap; }
.admin-table td { padding: 10px 12px; border-bottom: 1px solid #f5f5f5; color: #333; vertical-align: top; }
.admin-table tr:last-child td { border-bottom: none; }
.td-center { text-align: center; }
.td-pad { padding: 20px; color: #999; }
.sub-line { margin-top: 4px; font-size: 12px; color: #667085; }
.td-url { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12px; color: #888; }
.badge-success { background: #f6ffed; color: #52c41a; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-danger { background: #fff1f0; color: #ff4d4f; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-warning { background: #fffbe6; color: #faad14; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-default { background: #f5f5f5; color: #888; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.toast { position: fixed; bottom: 30px; right: 30px; padding: 12px 20px; border-radius: 8px; font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 12px; z-index: 9999; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.toast-success { background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; }
.toast-error { background: #fff1f0; color: #ff4d4f; border: 1px solid #ffccc7; }
.toast-close { background: none; border: none; cursor: pointer; font-size: 16px; padding: 0; color: inherit; }
</style>
