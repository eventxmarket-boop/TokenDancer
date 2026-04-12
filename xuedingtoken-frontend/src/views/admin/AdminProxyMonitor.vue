<template>
  <div class="page-container">
    <div class="page-title-row">
      <div>
        <h1 class="page-title">API 中转监控</h1>
        <p class="page-subtitle">把 Provider、Model Route、失败链和最近运行态放在同一块面板里，直接观察后台配置是否真的驱动了请求。</p>
      </div>
      <button class="btn-outline-sm" @click="loadAll">🔄 刷新</button>
    </div>

    <div class="stat-grid">
      <AdminStatCard label="24h 请求数" :value="overview.total_requests_24h" icon="📡" />
      <AdminStatCard label="健康 Provider" :value="overview.healthy_provider_count" icon="🌐" />
      <AdminStatCard label="活跃源 Key" :value="overview.active_provider_key_count" icon="🔑" />
      <AdminStatCard label="24h 成功率" :value="successRateLabel" icon="✅" />
      <AdminStatCard label="24h 平均延迟" :value="latencyLabel" icon="⏱️" />
      <AdminStatCard label="24h 失败数" :value="overview.failed_requests_24h" icon="⚠️" />
    </div>

    <div class="monitor-grid">
      <AdminSectionCard title="Provider 状态表">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Provider</th>
              <th>类型</th>
              <th>健康</th>
              <th>Key 数</th>
              <th>24h 运行态</th>
              <th>Cooldown</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="providerLoading"><td colspan="7" class="td-empty">加载中…</td></tr>
            <tr v-else-if="providers.length === 0"><td colspan="7" class="td-empty">暂无 Provider</td></tr>
            <tr v-for="provider in providers" :key="provider.id">
              <td>
                <div class="cell-title">{{ provider.name }}</div>
                <div class="cell-sub">{{ provider.base_url || '未配置 base_url' }}</div>
              </td>
              <td>{{ provider.provider_type }}</td>
              <td><AdminStatusBadge :value="provider.health_status" /></td>
              <td>{{ provider.active_key_count }}</td>
              <td>
                <div class="cell-sub">请求 {{ provider.request_count_24h }}</div>
                <div class="cell-sub">成功率 {{ provider.success_rate_24h }}%</div>
                <div class="cell-sub">延迟 {{ provider.avg_latency_ms_24h ? provider.avg_latency_ms_24h + 'ms' : '—' }}</div>
              </td>
              <td>
                <span v-if="provider.cooldown_active" class="warn-text">{{ provider.cooldown_remaining_seconds }}s</span>
                <span v-else>—</span>
              </td>
              <td>
                <button class="btn-action-sm" :disabled="probingIds.has(provider.id)" @click="handleProbe(provider.id)">
                  {{ probingIds.has(provider.id) ? '探测中…' : '手动探测' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </AdminSectionCard>

      <AdminSectionCard title="模型路由表">
        <table class="admin-table">
          <thead>
            <tr>
              <th>公版模型</th>
              <th>主路由</th>
              <th>备用路由</th>
              <th>策略</th>
              <th>24h 运行态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="modelLoading"><td colspan="6" class="td-empty">加载中…</td></tr>
            <tr v-else-if="models.length === 0"><td colspan="6" class="td-empty">暂无模型路由</td></tr>
            <tr v-for="route in models" :key="route.id">
              <td>
                <div class="cell-title">{{ route.public_model_name }}</div>
                <div class="cell-sub">{{ route.provider_model_name }}</div>
              </td>
              <td>{{ route.provider_name || route.provider_id || '—' }}</td>
              <td>{{ route.fallback_provider_name || '—' }}</td>
              <td>
                <div class="cell-sub">{{ route.policy_type }}</div>
                <div class="cell-sub">重试 {{ route.retry_count }} / 冷却 {{ route.cooldown_seconds }}s</div>
              </td>
              <td>
                <div class="cell-sub">请求 {{ route.request_count_24h }}</div>
                <div class="cell-sub">成功率 {{ route.success_rate_24h }}%</div>
                <div class="cell-sub">失败 {{ route.failure_count_24h }}</div>
              </td>
              <td>
                <button class="btn-action-sm" :disabled="!route.fallback_provider_id || switchingIds.has(route.id)" @click="handleSwitch(route.id)">
                  {{ switchingIds.has(route.id) ? '切换中…' : '切主备' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </AdminSectionCard>
    </div>

    <AdminSectionCard title="最近失败日志">
      <table class="admin-table">
        <thead>
          <tr>
            <th>时间</th>
            <th>模型</th>
            <th>Provider / Key</th>
            <th>状态</th>
            <th>策略</th>
            <th>延迟</th>
            <th>错误</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="failureLoading"><td colspan="7" class="td-empty">加载中…</td></tr>
          <tr v-else-if="failures.length === 0"><td colspan="7" class="td-empty">暂无失败记录</td></tr>
          <tr v-for="item in failures" :key="item.id">
            <td>{{ fmtDate(item.requested_at || '') }}</td>
            <td>{{ item.public_model_name }}</td>
            <td>
              <div>{{ item.provider_name || item.provider_id || '—' }}</div>
              <div class="cell-sub">{{ item.provider_key_name || item.provider_key_id || '—' }}</div>
            </td>
            <td><AdminStatusBadge :value="item.request_status" /></td>
            <td>{{ item.policy_type || 'fixed' }}</td>
            <td>{{ item.latency_ms ? item.latency_ms + 'ms' : '—' }}</td>
            <td class="error-text">{{ item.error_message || item.failure_chain_summary || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </AdminSectionCard>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminStatCard from '@/components/admin/AdminStatCard.vue'
import AdminStatusBadge from '@/components/admin/AdminStatusBadge.vue'
import { adminProxyMonitorApi, type AdminProxyFailureLog, type AdminProxyOverview } from '@/api/adminProxyMonitor'
import type { AdminModelRoute } from '@/api/adminModelRoutes'
import type { AdminProvider } from '@/api/adminProviders'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()
const overview = reactive<AdminProxyOverview>({
  total_requests_24h: 0,
  success_rate_24h: 0,
  failed_requests_24h: 0,
  avg_latency_ms_24h: 0,
  healthy_provider_count: 0,
  active_provider_count: 0,
  active_model_count: 0,
  active_provider_key_count: 0,
})
const providers = ref<AdminProvider[]>([])
const models = ref<AdminModelRoute[]>([])
const failures = ref<AdminProxyFailureLog[]>([])
const providerLoading = ref(false)
const modelLoading = ref(false)
const failureLoading = ref(false)
const probingIds = ref(new Set<number>())
const switchingIds = ref(new Set<number>())

const successRateLabel = computed(() => `${overview.success_rate_24h}%`)
const latencyLabel = computed(() => overview.avg_latency_ms_24h ? `${overview.avg_latency_ms_24h}ms` : '—')

const fmtDate = (value: string) => value ? new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'

const loadOverview = async () => {
  Object.assign(overview, await adminProxyMonitorApi.overview())
}
const loadProviders = async () => {
  providerLoading.value = true
  try {
    providers.value = await adminProxyMonitorApi.providers()
  } finally {
    providerLoading.value = false
  }
}
const loadModels = async () => {
  modelLoading.value = true
  try {
    models.value = await adminProxyMonitorApi.models()
  } finally {
    modelLoading.value = false
  }
}
const loadFailures = async () => {
  failureLoading.value = true
  try {
    failures.value = await adminProxyMonitorApi.failures({ limit: 20 })
  } finally {
    failureLoading.value = false
  }
}

const loadAll = async () => {
  try {
    await Promise.all([loadOverview(), loadProviders(), loadModels(), loadFailures()])
  } catch (e: any) {
    feedback.error(e.message || '监控数据加载失败')
  }
}

const handleProbe = async (providerId: number) => {
  probingIds.value = new Set([...probingIds.value, providerId])
  try {
    const result = await adminProxyMonitorApi.probeProvider(providerId)
    feedback.success(`探测完成：${result.status}`)
    await Promise.all([loadOverview(), loadProviders()])
  } catch (e: any) {
    feedback.error(e.message || 'Provider 探测失败')
  } finally {
    const next = new Set(probingIds.value)
    next.delete(providerId)
    probingIds.value = next
  }
}

const handleSwitch = async (routeId: number) => {
  switchingIds.value = new Set([...switchingIds.value, routeId])
  try {
    await adminProxyMonitorApi.switchModel(routeId, 'swap')
    feedback.success('主备路由已切换')
    await Promise.all([loadModels(), loadFailures()])
  } catch (e: any) {
    feedback.error(e.message || '路由切换失败')
  } finally {
    const next = new Set(switchingIds.value)
    next.delete(routeId)
    switchingIds.value = next
  }
}

onMounted(loadAll)
</script>

<style scoped>
.page-title-row { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:20px; }
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; margin:0; }
.page-subtitle { margin:6px 0 0; color:#667085; font-size:13px; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.stat-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(170px, 1fr)); gap:16px; margin-bottom:24px; }
.monitor-grid { display:grid; grid-template-columns:1fr; gap:20px; margin-bottom:24px; }
.admin-table { width:100%; border-collapse:collapse; font-size:13px; }
.admin-table th { text-align:left; padding:10px 12px; font-size:11px; font-weight:700; color:#999; text-transform:uppercase; letter-spacing:.5px; background:#fafafa; border-bottom:1px solid #f0f0f0; }
.admin-table td { padding:10px 12px; border-bottom:1px solid #f5f5f5; color:#333; vertical-align:top; }
.admin-table tr:last-child td { border-bottom:none; }
.td-empty { text-align:center; color:#bbb; padding:28px !important; }
.cell-title { font-weight:600; color:#1a1a2e; }
.cell-sub { font-size:12px; color:#888; margin-top:4px; word-break:break-all; }
.warn-text { color:#ff4d4f; font-weight:600; }
.error-text { color:#ff4d4f; max-width:320px; white-space:normal; word-break:break-word; line-height:1.45; }
.btn-action-sm { font-size:12px; padding:6px 10px; background:#fff; color:#1677ff; border:1px solid #91caff; border-radius:6px; cursor:pointer; }
.btn-action-sm:disabled { cursor:not-allowed; opacity:.6; }
</style>
