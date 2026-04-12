<template>
  <div class="page-container">
    <div class="page-title-row">
      <div>
        <h1 class="page-title">渠道管理</h1>
        <p class="page-subtitle">先创建可用 Provider，再继续创建源 Key 和模型映射。</p>
      </div>
      <div class="title-actions">
        <button class="btn-outline-sm" @click="fetchItems">🔄 刷新</button>
        <button class="btn-primary" @click="openCreate">+ 新增渠道</button>
      </div>
    </div>

    <div class="overview-grid">
      <div class="overview-card">
        <span class="overview-label">总渠道数</span>
        <strong class="overview-value">{{ displayItems.length }}</strong>
      </div>
      <div class="overview-card">
        <span class="overview-label">健康渠道</span>
        <strong class="overview-value">{{ healthyCount }}</strong>
      </div>
      <div class="overview-card">
        <span class="overview-label">Cooldown 中</span>
        <strong class="overview-value">{{ cooldownCount }}</strong>
      </div>
      <div class="overview-card">
        <span class="overview-label">24h 高成功率</span>
        <strong class="overview-value">{{ highSuccessCount }}</strong>
      </div>
    </div>

    <div class="catalog-card">
      <div class="catalog-title">当前统一支持的 Provider 类型</div>
      <div class="catalog-grid">
        <div v-for="option in providerTypeOptions" :key="option.value" class="catalog-item">
          <div class="catalog-name">{{ option.label }}</div>
          <div class="catalog-hint">{{ option.hint }}</div>
          <code v-if="option.defaultBaseUrl" class="catalog-url">{{ option.defaultBaseUrl }}</code>
        </div>
      </div>
    </div>

    <div v-if="showForm" class="modal-mask">
      <div class="modal-box">
        <h3 class="modal-title">{{ editingId ? '编辑渠道' : '新增渠道' }}</h3>
        <div class="form-group">
          <label>渠道名称 <span class="req">*</span></label>
          <input v-model="form.name" class="form-input" placeholder="如：Minimax 主通道" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>类型 <span class="req">*</span></label>
            <select v-model="form.provider_type" class="form-select" @change="handleProviderTypeChanged">
              <option v-for="option in providerTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
            <div class="field-help">{{ selectedProviderType?.hint }}</div>
          </div>
          <div class="form-group">
            <label>优先级（越小越优先）</label>
            <input type="number" v-model.number="form.priority" class="form-input" />
          </div>
        </div>
        <div class="form-group">
          <label>Base URL</label>
          <input v-model="form.base_url" class="form-input" :placeholder="selectedProviderType?.defaultBaseUrl || 'https://.../v1'" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>超时（秒）</label>
            <input type="number" v-model.number="form.timeout_seconds" class="form-input" />
          </div>
          <div class="form-group">
            <label>备注</label>
            <input v-model="form.notes" class="form-input" placeholder="如：生产主路由 / 海外备用" />
          </div>
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
          <input class="filter-input" placeholder="搜索渠道名称 / Base URL / 最近错误" v-model="filters.search" />
          <select class="filter-select" v-model="filters.provider_type">
            <option value="">全部类型</option>
            <option v-for="option in providerTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
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
              <th>ID</th>
              <th>渠道</th>
              <th>类型 / Endpoint</th>
              <th>状态</th>
              <th>24h 运行态</th>
              <th>Cooldown</th>
              <th>最后检查</th>
              <th>最近错误</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="9" class="td-center td-pad">加载中…</td></tr>
            <tr v-else-if="error"><td colspan="9" class="td-center td-pad td-error">{{ error }}</td></tr>
            <tr v-else-if="displayItems.length === 0"><td colspan="9" class="td-center td-pad"><AdminEmptyState icon="🌐" title="暂无渠道" desc="先创建一个可用 Provider，后续源 Key 才能绑定。" /></td></tr>
            <tr v-else v-for="provider in displayItems" :key="provider.id" class="tr-body">
              <td>{{ provider.id }}</td>
              <td>
                <strong>{{ provider.name }}</strong>
                <div class="sub-line">优先级 {{ provider.priority }}</div>
              </td>
              <td>
                <div class="badge-type">{{ provider.provider_type }}</div>
                <code class="url-text">{{ provider.base_url || '—' }}</code>
              </td>
              <td>
                <AdminStatusBadge :value="provider.is_active ? 'active' : 'disabled'" />
                <div class="sub-line"><AdminStatusBadge :value="provider.health_status || 'unknown'" type="info" /></div>
              </td>
              <td>
                <div class="metric-line">成功率 {{ provider.success_rate_24h ?? 0 }}%</div>
                <div class="metric-line">延迟 {{ provider.avg_latency_ms_24h ? provider.avg_latency_ms_24h + 'ms' : '—' }}</div>
                <div class="metric-line">活跃 Key {{ provider.active_key_count ?? 0 }}</div>
              </td>
              <td>
                <span v-if="provider.cooldown_active" class="warn-text">{{ provider.cooldown_remaining_seconds }}s</span>
                <span v-else>—</span>
              </td>
              <td>{{ provider.last_health_check_at ? fmtDate(provider.last_health_check_at) : '—' }}</td>
              <td><div class="error-preview">{{ provider.last_error || '—' }}</div></td>
              <td>
                <div class="td-actions">
                  <button class="btn-action-sm" :disabled="probingIds.has(provider.id)" @click="handleProbe(provider.id)">
                    {{ probingIds.has(provider.id) ? '探测中…' : '探测' }}
                  </button>
                  <button class="btn-action-sm" @click="openEdit(provider)">编辑</button>
                  <button v-if="provider.is_active" class="btn-danger-sm" @click="confirmToggle(provider)">停用</button>
                  <button v-else class="btn-success-sm" @click="confirmToggle(provider)">启用</button>
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
import { adminProvidersApi } from '@/api/adminProviders'
import { adminProxyMonitorApi } from '@/api/adminProxyMonitor'
import { PROVIDER_TYPE_MAP, PROVIDER_TYPE_OPTIONS, type ProviderType } from '@/constants/providerTypes'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()
const providerTypeOptions = PROVIDER_TYPE_OPTIONS
const items = ref<any[]>([])
const runtimeRows = ref<Record<number, any>>({})
const loading = ref(false)
const error = ref('')
const showForm = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const probingIds = ref(new Set<number>())
const filters = reactive({ search: '', provider_type: '', is_active: '' })

const defaultForm = (): {
  name: string
  provider_type: ProviderType
  base_url: string
  priority: number
  timeout_seconds: number
  notes: string
  is_active: boolean
} => ({
  name: '',
  provider_type: 'openai',
  base_url: '',
  priority: 100,
  timeout_seconds: 60,
  notes: '',
  is_active: true,
})
const form = reactive(defaultForm())
const confirm = reactive({ show: false, title: '', msg: '', danger: false, action: null as null | (() => Promise<void>) })

const selectedProviderType = computed(() => PROVIDER_TYPE_MAP[form.provider_type as keyof typeof PROVIDER_TYPE_MAP])

const displayItems = computed(() => {
  const keyword = filters.search.trim().toLowerCase()
  return items.value
    .map((item) => ({ ...item, ...(runtimeRows.value[item.id] || {}) }))
    .filter((item) => {
      const matchKeyword = !keyword || [item.name, item.base_url, item.last_error]
        .filter(Boolean)
        .some((value: string) => value.toLowerCase().includes(keyword))
      const matchType = !filters.provider_type || item.provider_type === filters.provider_type
      const matchStatus = !filters.is_active || String(item.is_active) === filters.is_active
      return matchKeyword && matchType && matchStatus
    })
    .sort((a, b) => (a.priority ?? 999) - (b.priority ?? 999))
})

const healthyCount = computed(() => displayItems.value.filter((item) => item.health_status === 'healthy').length)
const cooldownCount = computed(() => displayItems.value.filter((item) => item.cooldown_active).length)
const highSuccessCount = computed(() => displayItems.value.filter((item) => Number(item.success_rate_24h || 0) >= 95).length)

const fmtDate = (value: string) => value ? new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'

const fetchItems = async () => {
  loading.value = true
  error.value = ''
  try {
    const [providers, monitorProviders] = await Promise.all([
      adminProvidersApi.list(),
      adminProxyMonitorApi.providers(),
    ])
    items.value = providers
    runtimeRows.value = Object.fromEntries(monitorProviders.map((row) => [row.id, row]))
  } catch (e: any) {
    error.value = `加载失败：${e.message || ''}`
    items.value = []
    runtimeRows.value = {}
  } finally {
    loading.value = false
  }
}

const applyProviderDefaults = (providerType: string) => {
  const meta = PROVIDER_TYPE_MAP[providerType as keyof typeof PROVIDER_TYPE_MAP]
  if (!meta?.defaultBaseUrl) return
  if (!form.base_url || Object.values(PROVIDER_TYPE_MAP).some((item) => item.defaultBaseUrl === form.base_url)) {
    form.base_url = meta.defaultBaseUrl
  }
}

const handleProviderTypeChanged = () => {
  applyProviderDefaults(form.provider_type)
}

const openCreate = () => {
  editingId.value = null
  Object.assign(form, defaultForm())
  applyProviderDefaults(form.provider_type)
  showForm.value = true
}

const openEdit = (provider: any) => {
  editingId.value = provider.id
  Object.assign(form, {
    name: provider.name,
    provider_type: provider.provider_type,
    base_url: provider.base_url || '',
    priority: provider.priority,
    timeout_seconds: provider.timeout_seconds,
    notes: provider.notes || '',
    is_active: provider.is_active,
  })
  showForm.value = true
}

const closeForm = () => {
  showForm.value = false
  editingId.value = null
  Object.assign(form, defaultForm())
}

const handleSave = async () => {
  if (!form.name?.trim()) {
    feedback.warning('请填写渠道名称')
    return
  }
  saving.value = true
  try {
    const payload = {
      ...form,
      name: form.name.trim(),
      base_url: form.base_url.trim(),
      notes: form.notes.trim(),
    }
    if (editingId.value) {
      await adminProvidersApi.update(editingId.value, payload)
    } else {
      await adminProvidersApi.create(payload)
    }
    closeForm()
    feedback.success(editingId.value ? '渠道已更新' : '渠道已创建')
    await fetchItems()
  } catch (e: any) {
    feedback.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleProbe = async (providerId: number) => {
  probingIds.value = new Set([...probingIds.value, providerId])
  try {
    const result = await adminProxyMonitorApi.probeProvider(providerId)
    feedback.success(`探测完成：${result.status}`)
    await fetchItems()
  } catch (e: any) {
    feedback.error(e.message || '探测失败')
  } finally {
    const next = new Set(probingIds.value)
    next.delete(providerId)
    probingIds.value = next
  }
}

const confirmToggle = (provider: any) => {
  confirm.title = provider.is_active ? '停用渠道' : '启用渠道'
  confirm.msg = `确定要${provider.is_active ? '停用' : '启用'}渠道「${provider.name}」吗？`
  confirm.danger = provider.is_active
  confirm.action = async () => {
    await adminProvidersApi.update(provider.id, { is_active: !provider.is_active })
    feedback.success(provider.is_active ? '渠道已停用' : '渠道已启用')
    await fetchItems()
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

fetchItems()
</script>

<style scoped>
.page-title-row { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:20px; }
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; margin:0; }
.page-subtitle { margin:6px 0 0; color:#667085; font-size:13px; }
.title-actions { display:flex; gap:10px; align-items:center; }
.overview-grid { display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:20px; }
.overview-card, .catalog-card { background:#fff; border:1px solid #eef1f4; border-radius:12px; padding:14px 16px; }
.overview-label { display:block; font-size:12px; color:#7b8794; margin-bottom:8px; }
.overview-value { font-size:22px; color:#111827; }
.catalog-card { margin-bottom:20px; }
.catalog-title { font-size:14px; font-weight:700; color:#1f2937; margin-bottom:12px; }
.catalog-grid { display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:12px; }
.catalog-item { background:#f8fafc; border:1px solid #e5e7eb; border-radius:10px; padding:12px; }
.catalog-name { font-size:13px; font-weight:700; color:#111827; margin-bottom:4px; }
.catalog-hint { font-size:12px; color:#667085; line-height:1.5; min-height:36px; }
.catalog-url { display:block; margin-top:8px; font-size:11px; color:#2563eb; background:#eef4ff; padding:4px 6px; border-radius:6px; overflow:hidden; text-overflow:ellipsis; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.btn-primary { font-size:13px; padding:8px 18px; background:#1677ff; color:#fff; border:none; border-radius:6px; cursor:pointer; }
.btn-primary:hover { background:#4096ff; }
.btn-primary:disabled { opacity:0.6; cursor:not-allowed; }
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.45); display:flex; align-items:center; justify-content:center; z-index:1000; overflow-y:auto; padding:20px; }
.modal-box { background:#fff; border-radius:12px; padding:28px; width:520px; max-width:100%; box-shadow:0 8px 32px rgba(0,0,0,0.15); }
.modal-title { font-size:16px; font-weight:700; margin:0 0 20px; color:#1a1a2e; }
.form-row { display:flex; gap:14px; }
.form-group { flex:1; margin-bottom:14px; }
.form-group label { display:block; font-size:12px; color:#666; margin-bottom:4px; font-weight:600; }
.field-help { margin-top:6px; font-size:12px; color:#667085; line-height:1.5; }
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
.badge-type { font-size:11px; background:#f0f5ff; color:#3b5bdb; padding:2px 8px; border-radius:10px; font-weight:600; display:inline-block; margin-bottom:6px; }
.url-text { font-size:11px; background:#f5f5f5; padding:2px 6px; border-radius:4px; display:inline-block; max-width:220px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.metric-line, .sub-line { font-size:12px; color:#667085; margin-top:4px; }
.warn-text { color:#ff4d4f; font-weight:700; }
.error-preview { max-width:220px; white-space:normal; word-break:break-word; line-height:1.45; color:#c1121f; }
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
  .catalog-grid { grid-template-columns:repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 720px) {
  .page-title-row, .form-row { flex-direction:column; }
  .catalog-grid { grid-template-columns:1fr; }
}
</style>
