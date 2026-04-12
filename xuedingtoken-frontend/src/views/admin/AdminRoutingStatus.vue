<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">路由配置状态</h1>
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
      <AdminSectionCard>
        <div class="table-wrap">
          <table class="admin-table">
            <thead><tr>
              <th>公版模型</th><th>主渠道</th><th>备用渠道</th><th>渠道模型名</th><th>策略</th><th>重试</th><th>冷却(秒)</th><th>启用</th><th>健康风险</th><th>操作</th>
            </tr></thead>
            <tbody>
              <tr v-if="routes.length === 0"><td colspan="10" class="td-center td-pad">暂无路由配置</td></tr>
              <tr v-else v-for="r in routes" :key="r.id">
                <td><strong>{{ r.public_model_name }}</strong></td>
                <td>{{ providerMap[r.provider_id] || r.provider_id }}</td>
                <td>{{ r.fallback_provider_id ? (providerMap[r.fallback_provider_id] || r.fallback_provider_id) : '—' }}</td>
                <td>{{ r.provider_model_name }}</td>
                <td>{{ policyTypeLabel(r.priority) }}</td>
                <td>{{ r.priority }}</td>
                <td>—</td>
                <td><AdminStatusBadge :value="r.is_active" /></td>
                <td><span :class="healthRiskBadge(r)">{{ healthRiskLabel(r) }}</span></td>
                <td>
                  <router-link :to="`/admin/api-proxy/model-routes`" class="link-btn">查看详情</router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </AdminSectionCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { adminModelRoutesApi } from '@/api/adminModelRoutes'
import { adminProvidersApi } from '@/api/adminProviders'

const loading = ref(true)
const error = ref('')
const routes = ref<any[]>([])
const providers = ref<any[]>([])

const providerMap = computed(() => {
  const m: Record<number, string> = {}
  providers.value.forEach((p: any) => { m[p.id] = p.name })
  return m
})

const providerHealthMap = computed(() => {
  const m: Record<number, string> = {}
  providers.value.forEach((p: any) => { m[p.id] = p.health_status || 'unknown' })
  return m
})

async function fetchAll() {
  loading.value = true
  error.value = ''
  try {
    const [routeList, provList] = await Promise.all([
      adminModelRoutesApi.list() as Promise<any[]>,
      adminProvidersApi.list() as Promise<any[]>,
    ])
    routes.value = routeList
    providers.value = provList
  } catch (e: any) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function healthRiskLabel(r: any) {
  const primaryHealth = providerHealthMap.value[r.provider_id]
  const fallbackHealth = r.fallback_provider_id ? providerHealthMap.value[r.fallback_provider_id] : null

  if (!primaryHealth || primaryHealth === 'unknown') return 'unknown'
  if (primaryHealth === 'healthy') {
    if (!fallbackHealth || fallbackHealth === 'unknown') return 'healthy'
    return fallbackHealth === 'healthy' ? 'healthy' : 'fallback_risk'
  }
  if (primaryHealth === 'degraded') return 'primary_degraded'
  if (primaryHealth === 'unreachable' || primaryHealth === 'down') {
    if (!fallbackHealth) return 'no_fallback'
    return fallbackHealth === 'healthy' ? 'fallover_ready' : 'all_unreachable'
  }
  return 'unknown'
}

function healthRiskBadge(r: any) {
  const label = healthRiskLabel(r)
  if (label === 'healthy' || label === 'fallover_ready') return 'badge-success'
  if (label === 'primary_degraded' || label === 'fallback_risk') return 'badge-warning'
  if (label === 'no_fallback' || label === 'all_unreachable') return 'badge-danger'
  return 'badge-default'
}

function policyTypeLabel(priority: number) {
  if (priority <= 10) return '高优先级'
  if (priority <= 50) return '正常'
  return '低优先级'
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
.table-wrap { overflow-x: auto; }
.admin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.admin-table th { background: #fafafa; padding: 10px 12px; text-align: left; font-weight: 600; color: #666; border-bottom: 1px solid #f0f0f0; white-space: nowrap; }
.admin-table td { padding: 10px 12px; border-bottom: 1px solid #f5f5f5; color: #333; }
.admin-table tr:last-child td { border-bottom: none; }
.td-center { text-align: center; }
.td-pad { padding: 20px; color: #999; }
.badge-success { background: #f6ffed; color: #52c41a; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-danger { background: #fff1f0; color: #ff4d4f; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-warning { background: #fffbe6; color: #faad14; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-default { background: #f5f5f5; color: #888; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.link-btn { color: #1677ff; text-decoration: none; font-size: 12px; }
.link-btn:hover { text-decoration: underline; }
</style>
