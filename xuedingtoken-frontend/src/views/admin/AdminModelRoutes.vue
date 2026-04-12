<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">模型映射</h1>
      <div class="title-actions">
        <button class="btn-outline-sm" @click="fetchAll">🔄 刷新</button>
        <button class="btn-primary" @click="openCreate">+ 新增映射</button>
      </div>
    </div>

    <div class="overview-grid">
      <div class="overview-card">
        <span class="overview-label">活跃路由</span>
        <strong class="overview-value">{{ activeRouteCount }}</strong>
      </div>
      <div class="overview-card">
        <span class="overview-label">带备用路由</span>
        <strong class="overview-value">{{ fallbackRouteCount }}</strong>
      </div>
      <div class="overview-card">
        <span class="overview-label">可手动切换</span>
        <strong class="overview-value">{{ switchableRouteCount }}</strong>
      </div>
      <div class="overview-card">
        <span class="overview-label">高成功率路由</span>
        <strong class="overview-value">{{ stableRouteCount }}</strong>
      </div>
    </div>

    <div v-if="showForm" class="modal-mask">
      <div class="modal-box">
        <h3 class="modal-title">{{ editingId ? '编辑映射' : '新增模型映射' }}</h3>
        <div class="form-row">
          <div class="form-group">
            <label>公版模型名 <span class="req">*</span></label>
            <input v-model="form.public_model_name" class="form-input" placeholder="如：gpt-4o" />
          </div>
          <div class="form-group">
            <label>上游模型名 <span class="req">*</span></label>
            <input v-model="form.provider_model_name" class="form-input" placeholder="如：gpt-4o-2024-08-06" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>主渠道 <span class="req">*</span></label>
            <select v-model="form.provider_id" class="form-select">
              <option value="">— 选择渠道 —</option>
              <option v-for="provider in providers" :key="provider.id" :value="provider.id">{{ provider.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>备渠道（可选）</label>
            <select v-model="form.fallback_provider_id" class="form-select">
              <option value="">无</option>
              <option v-for="provider in providers" :key="provider.id" :value="provider.id">{{ provider.name }}</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>备模型名</label>
            <input v-model="form.fallback_model_name" class="form-input" placeholder="Fallback 模型名（可选）" />
          </div>
          <div class="form-group">
            <label>优先级（越小越优先）</label>
            <input type="number" v-model.number="form.priority" class="form-input" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>成本倍率</label>
            <input type="number" step="0.1" v-model.number="form.cost_multiplier" class="form-input" />
          </div>
          <div class="form-group">
            <label>最大上下文（tokens）</label>
            <input type="number" v-model.number="form.max_context" class="form-input" placeholder="如：128000" />
          </div>
        </div>
        <div class="form-group">
          <label>备注</label>
          <input v-model="form.notes" class="form-input" placeholder="如：主 OpenAI，备 Azure" />
        </div>
        <div class="form-group">
          <label>是否启用</label>
          <select v-model="form.is_active" class="form-select">
            <option :value="true">启用</option>
            <option :value="false">停用</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn-outline" @click="closeForm">取消</button>
          <button class="btn-primary" @click="handleSave" :disabled="saving">{{ saving ? '保存中…' : '确认' }}</button>
        </div>
      </div>
    </div>

    <AdminSectionCard>
      <AdminTableToolbar>
        <AdminFilterBar>
          <input class="filter-input" placeholder="搜索公版模型 / 上游模型" v-model="filters.search" />
          <select class="filter-select" v-model="filters.provider_id">
            <option value="">全部渠道</option>
            <option v-for="provider in providers" :key="provider.id" :value="provider.id">{{ provider.name }}</option>
          </select>
          <select class="filter-select" v-model="filters.is_active">
            <option value="">全部状态</option>
            <option value="true">启用</option>
            <option value="false">停用</option>
          </select>
        </AdminFilterBar>
      </AdminTableToolbar>

      <div class="table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>公版模型</th>
              <th>主路由</th>
              <th>备用路由</th>
              <th>策略 / 成本</th>
              <th>24h 运行态</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="7" class="td-center td-pad">加载中…</td></tr>
            <tr v-else-if="error"><td colspan="7" class="td-center td-pad td-error">{{ error }}</td></tr>
            <tr v-else-if="displayItems.length === 0"><td colspan="7" class="td-center td-pad"><AdminEmptyState icon="🔀" title="暂无映射" /></td></tr>
            <tr v-else v-for="route in displayItems" :key="route.id" class="tr-body">
              <td>
                <strong>{{ route.public_model_name }}</strong>
                <div class="sub-line">最大上下文 {{ route.max_context ? route.max_context.toLocaleString() : '—' }}</div>
              </td>
              <td>
                <div>{{ providerMap[route.provider_id] || route.provider_name || route.provider_id || '—' }}</div>
                <code>{{ route.provider_model_name }}</code>
              </td>
              <td>
                <div>{{ route.fallback_provider_id ? (providerMap[route.fallback_provider_id] || route.fallback_provider_name || route.fallback_provider_id) : '—' }}</div>
                <code>{{ route.fallback_model_name || '—' }}</code>
              </td>
              <td>
                <div class="metric-line">{{ route.policy_type || 'fixed' }}</div>
                <div class="metric-line">倍率 {{ route.cost_multiplier }}x</div>
              </td>
              <td>
                <div class="metric-line">成功率 {{ route.success_rate_24h ?? 0 }}%</div>
                <div class="metric-line">失败 {{ route.failure_count_24h ?? 0 }}</div>
                <div class="metric-line">延迟 {{ route.avg_latency_ms_24h ? route.avg_latency_ms_24h + 'ms' : '—' }}</div>
              </td>
              <td><AdminStatusBadge :value="route.is_active ? 'active' : 'disabled'" /></td>
              <td>
                <div class="td-actions">
                  <button class="btn-action-sm" @click="openEdit(route)">编辑</button>
                  <button class="btn-action-sm" :disabled="!route.fallback_provider_id || switchingIds.has(route.id)" @click="handleSwitch(route.id)">
                    {{ switchingIds.has(route.id) ? '切换中…' : '切主备' }}
                  </button>
                  <button v-if="route.is_active" class="btn-danger-sm" @click="confirmToggle(route)">停用</button>
                  <button v-else class="btn-success-sm" @click="confirmToggle(route)">启用</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </AdminSectionCard>

    <div v-if="confirm.show" class="modal-mask">
      <div class="confirm-box">
        <h3 class="confirm-title">{{ confirm.title }}</h3>
        <p class="confirm-msg">{{ confirm.msg }}</p>
        <div class="modal-actions">
          <button class="btn-outline" @click="confirm.show = false">取消</button>
          <button :class="['btn-confirm', confirm.danger ? 'btn-danger' : 'btn-primary']" @click="doConfirm">确认{{ confirm.title }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminTableToolbar from '@/components/admin/AdminTableToolbar.vue'
import AdminFilterBar from '@/components/admin/AdminFilterBar.vue'
import AdminStatusBadge from '@/components/admin/AdminStatusBadge.vue'
import AdminEmptyState from '@/components/admin/AdminEmptyState.vue'
import { adminModelRoutesApi, adminProvidersApi } from '@/api/admin'
import { adminProxyMonitorApi } from '@/api/adminProxyMonitor'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()
const items = ref<any[]>([])
const providers = ref<any[]>([])
const metricsRows = ref<Record<number, any>>({})
const loading = ref(false)
const error = ref('')
const showForm = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const switchingIds = ref(new Set<number>())
const filters = reactive({ search: '', provider_id: '', is_active: '' })

const defaultForm = () => ({
  public_model_name: '',
  provider_id: '',
  provider_model_name: '',
  fallback_provider_id: '',
  fallback_model_name: '',
  priority: 100,
  cost_multiplier: 1.0,
  max_context: null as number | null,
  notes: '',
  is_active: true,
})
const form = reactive(defaultForm())
const confirm = reactive({ show: false, title: '', msg: '', danger: false, action: null as null | (() => Promise<void>) })

const providerMap = computed(() => {
  const map: Record<number, string> = {}
  for (const provider of providers.value) map[provider.id] = provider.name
  return map
})

const displayItems = computed(() => {
  const keyword = filters.search.trim().toLowerCase()
  return items.value
    .map(item => ({ ...item, ...(metricsRows.value[item.id] || {}) }))
    .filter(item => {
      const matchKeyword = !keyword || [item.public_model_name, item.provider_model_name, item.fallback_model_name]
        .filter(Boolean)
        .some((value: string) => value.toLowerCase().includes(keyword))
      const matchProvider = !filters.provider_id || String(item.provider_id) === filters.provider_id
      const matchStatus = !filters.is_active || String(item.is_active) === filters.is_active
      return matchKeyword && matchProvider && matchStatus
    })
    .sort((a, b) => (a.priority ?? 999) - (b.priority ?? 999))
})

const activeRouteCount = computed(() => displayItems.value.filter(item => item.is_active).length)
const fallbackRouteCount = computed(() => displayItems.value.filter(item => item.fallback_provider_id).length)
const switchableRouteCount = computed(() => displayItems.value.filter(item => item.fallback_provider_id).length)
const stableRouteCount = computed(() => displayItems.value.filter(item => Number(item.success_rate_24h || 0) >= 95).length)

const fetchAll = async () => {
  loading.value = true
  error.value = ''
  try {
    const [routes, providerRows, monitorRoutes] = await Promise.all([
      adminModelRoutesApi.list(),
      adminProvidersApi.list(),
      adminProxyMonitorApi.models(),
    ])
    items.value = routes
    providers.value = providerRows
    metricsRows.value = Object.fromEntries(monitorRoutes.map(row => [row.id, row]))
  } catch (e: any) {
    error.value = e.message || '加载失败'
    items.value = []
    metricsRows.value = {}
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingId.value = null
  Object.assign(form, defaultForm())
  showForm.value = true
}

const openEdit = (route: any) => {
  editingId.value = route.id
  Object.assign(form, {
    public_model_name: route.public_model_name,
    provider_id: route.provider_id,
    provider_model_name: route.provider_model_name,
    fallback_provider_id: route.fallback_provider_id || '',
    fallback_model_name: route.fallback_model_name || '',
    priority: route.priority,
    cost_multiplier: route.cost_multiplier,
    max_context: route.max_context || null,
    notes: route.notes || '',
    is_active: route.is_active,
  })
  showForm.value = true
}

const closeForm = () => {
  showForm.value = false
  editingId.value = null
  Object.assign(form, defaultForm())
}

const handleSave = async () => {
  if (!form.public_model_name?.trim() || !form.provider_model_name?.trim() || !form.provider_id) {
    feedback.warning('请填写公版模型名、主渠道和上游模型名')
    return
  }
  saving.value = true
  try {
    const payload: any = { ...form }
    if (!payload.fallback_provider_id) delete payload.fallback_provider_id
    if (!payload.fallback_model_name) delete payload.fallback_model_name
    if (editingId.value) {
      await adminModelRoutesApi.update(editingId.value, payload)
    } else {
      await adminModelRoutesApi.create(payload)
    }
    closeForm()
    feedback.success(editingId.value ? '映射已更新' : '映射已创建')
    await fetchAll()
  } catch (e: any) {
    feedback.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleSwitch = async (routeId: number) => {
  switchingIds.value = new Set([...switchingIds.value, routeId])
  try {
    await adminProxyMonitorApi.switchModel(routeId, 'swap')
    feedback.success('主备路由已切换')
    await fetchAll()
  } catch (e: any) {
    feedback.error(e.message || '路由切换失败')
  } finally {
    const next = new Set(switchingIds.value)
    next.delete(routeId)
    switchingIds.value = next
  }
}

const confirmToggle = (route: any) => {
  confirm.title = route.is_active ? '停用映射' : '启用映射'
  confirm.msg = `确定要${route.is_active ? '停用' : '启用'}「${route.public_model_name}」吗？`
  confirm.danger = route.is_active
  confirm.action = async () => {
    await adminModelRoutesApi.update(route.id, { is_active: !route.is_active })
    feedback.success(route.is_active ? '映射已停用' : '映射已启用')
    await fetchAll()
  }
  confirm.show = true
}

const doConfirm = async () => {
  confirm.show = false
  try {
    await confirm.action?.()
  } catch (e: any) {
    feedback.error(e.message || '操作失败')
  }
}

fetchAll()
</script>

<style scoped>
.page-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; }
.title-actions { display:flex; gap:10px; }
.overview-grid { display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:20px; }
.overview-card { background:#fff; border:1px solid #eef1f4; border-radius:12px; padding:14px 16px; }
.overview-label { display:block; font-size:12px; color:#7b8794; margin-bottom:8px; }
.overview-value { font-size:22px; color:#111827; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.btn-primary { font-size:13px; padding:8px 18px; background:#1677ff; color:#fff; border:none; border-radius:6px; cursor:pointer; }
.btn-primary:disabled { opacity:0.6; cursor:not-allowed; }
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.45); display:flex; align-items:center; justify-content:center; z-index:1000; overflow-y:auto; padding:20px; }
.modal-box { background:#fff; border-radius:12px; padding:28px; width:580px; max-width:95vw; box-shadow:0 8px 32px rgba(0,0,0,0.15); }
.modal-title { font-size:16px; font-weight:700; margin:0 0 20px; color:#1a1a2e; }
.form-row { display:flex; gap:14px; }
.form-group { flex:1; margin-bottom:14px; }
.form-group label { display:block; font-size:12px; color:#666; margin-bottom:4px; font-weight:600; }
.req { color:#ff4d4f; }
.form-input, .form-select, .filter-input, .filter-select { width:100%; font-size:13px; padding:8px 10px; border:1px solid #e8e8e8; border-radius:6px; outline:none; color:#333; box-sizing:border-box; background:#fff; }
.form-input:focus, .form-select:focus, .filter-input:focus, .filter-select:focus { border-color:#1677ff; }
.modal-actions { display:flex; justify-content:flex-end; gap:12px; margin-top:20px; }
.btn-outline { font-size:13px; padding:8px 18px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.table-wrap { overflow-x:auto; }
.admin-table { width:100%; border-collapse:collapse; font-size:13px; }
.admin-table th { text-align:left; padding:10px 14px; font-size:11px; font-weight:700; color:#999; text-transform:uppercase; letter-spacing:0.5px; background:#fafafa; border-bottom:1px solid #f0f0f0; white-space:nowrap; }
.admin-table td { padding:10px 14px; border-bottom:1px solid #f5f5f5; color:#333; vertical-align:top; }
.tr-body:hover td { background:#fafafa; }
.tr-body:last-child td { border-bottom:none; }
.td-center { text-align:center; }
.td-pad { padding:32px !important; }
.td-error { color:#ff4d4f; }
.metric-line, .sub-line { font-size:12px; color:#667085; margin-top:4px; }
code { font-size:11px; background:#f5f5f5; padding:2px 6px; border-radius:4px; display:inline-block; margin-top:6px; }
.td-actions { display:flex; gap:6px; flex-wrap:wrap; }
.btn-action-sm { font-size:11px; padding:3px 8px; color:#1677ff; background:none; border:1px solid #1677ff; border-radius:4px; cursor:pointer; }
.btn-action-sm:hover { background:#e6f7ff; }
.btn-danger-sm { font-size:11px; padding:3px 8px; color:#ff4d4f; background:none; border:1px solid #ff4d4f; border-radius:4px; cursor:pointer; }
.btn-danger-sm:hover { background:#fff1f0; }
.btn-success-sm { font-size:11px; padding:3px 8px; color:#52c41a; background:none; border:1px solid #52c41a; border-radius:4px; cursor:pointer; }
.btn-success-sm:hover { background:#f6ffed; }
.confirm-box { background:#fff; border-radius:12px; padding:28px; width:420px; max-width:95vw; box-shadow:0 8px 32px rgba(0,0,0,0.15); }
.confirm-title { font-size:16px; font-weight:700; margin:0 0 12px; color:#1a1a2e; }
.confirm-msg { font-size:13px; color:#555; margin:0 0 20px; }
.btn-confirm { font-size:13px; padding:8px 18px; border:none; border-radius:6px; cursor:pointer; }
.btn-danger { background:#ff4d4f; color:#fff; }

@media (max-width: 1100px) {
  .overview-grid { grid-template-columns:repeat(2, 1fr); }
}
</style>
