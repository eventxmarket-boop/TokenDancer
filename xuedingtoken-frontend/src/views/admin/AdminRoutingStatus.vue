<template>
  <div class="page-container">
    <div class="page-title-row">
      <div>
        <h1 class="page-title">路由配置状态</h1>
        <p class="page-subtitle">从“模型映射 + 路由策略 + Provider 健康”三个维度一起看，判断当前路由是否可真正承载中转请求。</p>
      </div>
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
              <th>公版模型</th><th>主渠道</th><th>备用渠道</th><th>渠道模型名</th><th>策略</th><th>24h 状态</th><th>启用</th><th>健康风险</th><th>操作</th>
            </tr></thead>
            <tbody>
              <tr v-if="routes.length === 0"><td colspan="9" class="td-center td-pad">暂无路由配置</td></tr>
              <tr v-else v-for="route in routes" :key="route.id">
                <td><strong>{{ route.public_model_name }}</strong></td>
                <td>
                  <div>{{ route.provider_name || route.provider_id }}</div>
                  <div class="sub-line">{{ route.provider_type || '—' }}</div>
                </td>
                <td>
                  <div>{{ route.fallback_provider_name || '—' }}</div>
                  <div class="sub-line">{{ route.fallback_provider_type || '—' }}</div>
                </td>
                <td>
                  <div>{{ route.provider_model_name }}</div>
                  <div class="sub-line">Fallback {{ route.fallback_model_name || '—' }}</div>
                </td>
                <td>
                  <div>{{ route.policy_type }}</div>
                  <div class="sub-line">重试 {{ route.retry_count }} / 冷却 {{ route.cooldown_seconds }}s</div>
                </td>
                <td>
                  <div class="sub-line">请求 {{ route.request_count_24h }}</div>
                  <div class="sub-line">成功率 {{ route.success_rate_24h }}%</div>
                  <div class="sub-line">失败 {{ route.failure_count_24h }}</div>
                </td>
                <td><AdminStatusBadge :value="route.is_active ? 'active' : 'disabled'" /></td>
                <td><span :class="healthRiskBadge(route)">{{ healthRiskLabel(route) }}</span></td>
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
import { ref } from 'vue'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminStatusBadge from '@/components/admin/AdminStatusBadge.vue'
import { adminModelRoutesApi, type AdminModelRoute } from '@/api/adminModelRoutes'
import { adminProvidersApi, type AdminProvider } from '@/api/adminProviders'

const loading = ref(true)
const error = ref('')
const routes = ref<AdminModelRoute[]>([])
const providers = ref<AdminProvider[]>([])

async function fetchAll() {
  loading.value = true
  error.value = ''
  try {
    const [routeList, providerList] = await Promise.all([
      adminModelRoutesApi.list(),
      adminProvidersApi.list(),
    ])
    routes.value = routeList
    providers.value = providerList
  } catch (e: any) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function providerHealth(providerId?: number | null) {
  if (!providerId) return 'unknown'
  return providers.value.find((provider) => provider.id === providerId)?.health_status || 'unknown'
}

function healthRiskLabel(route: AdminModelRoute) {
  const primaryHealth = providerHealth(route.provider_id)
  const fallbackHealth = route.fallback_provider_id ? providerHealth(route.fallback_provider_id) : null

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

function healthRiskBadge(route: AdminModelRoute) {
  const label = healthRiskLabel(route)
  if (label === 'healthy' || label === 'fallover_ready') return 'badge-success'
  if (label === 'primary_degraded' || label === 'fallback_risk') return 'badge-warning'
  if (label === 'no_fallback' || label === 'all_unreachable') return 'badge-danger'
  return 'badge-default'
}

fetchAll()
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
.badge-success { background: #f6ffed; color: #52c41a; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-danger { background: #fff1f0; color: #ff4d4f; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-warning { background: #fffbe6; color: #faad14; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-default { background: #f5f5f5; color: #888; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.link-btn { color: #1677ff; text-decoration: none; font-size: 12px; }
.link-btn:hover { text-decoration: underline; }
</style>
