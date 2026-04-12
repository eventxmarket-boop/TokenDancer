<template>
  <div class="page-container">
    <div class="page-title-row">
      <div>
        <h1 class="page-title">路由策略</h1>
        <p class="page-subtitle">策略不再只是配置项，它会直接约束真实请求如何在当前模型映射的 Provider 对之间切换。</p>
      </div>
      <div class="title-actions">
        <button class="btn-outline-sm" @click="fetchAll">🔄 刷新</button>
        <button class="btn-primary" @click="openCreate">+ 新增策略</button>
      </div>
    </div>

    <div class="overview-grid">
      <div class="overview-card">
        <span class="overview-label">策略总数</span>
        <strong class="overview-value">{{ displayItems.length }}</strong>
      </div>
      <div class="overview-card">
        <span class="overview-label">已就绪策略</span>
        <strong class="overview-value">{{ readyPolicyCount }}</strong>
      </div>
      <div class="overview-card">
        <span class="overview-label">Fallback / Weighted</span>
        <strong class="overview-value">{{ advancedPolicyCount }}</strong>
      </div>
      <div class="overview-card">
        <span class="overview-label">路由不匹配</span>
        <strong class="overview-value">{{ invalidBindingCount }}</strong>
      </div>
    </div>

    <div v-if="showForm" class="modal-mask">
      <div class="modal-box">
        <h3 class="modal-title">{{ editingId ? '编辑策略' : '新增路由策略' }}</h3>
        <div class="form-row">
          <div class="form-group span2">
            <label>策略名称 <span class="req">*</span></label>
            <input v-model="form.name" class="form-input" placeholder="如：GPT-4 固定线路" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>公版模型名 <span class="req">*</span></label>
            <select v-model="form.public_model_name" class="form-select" @change="handleModelChange">
              <option value="">— 选择模型映射 —</option>
              <option v-for="route in modelRoutes" :key="route.id" :value="route.public_model_name">{{ route.public_model_name }}</option>
            </select>
            <div class="field-help">策略只能绑定到已存在的 Model Route。</div>
          </div>
          <div class="form-group">
            <label>策略类型 <span class="req">*</span></label>
            <select v-model="form.policy_type" class="form-select">
              <option value="fixed">fixed（固定）</option>
              <option value="fallback">fallback（主失败切换备）</option>
              <option value="weighted">weighted（权重分配）</option>
              <option value="cost_first">cost_first（优先低价）</option>
            </select>
          </div>
        </div>
        <div class="binding-preview" v-if="selectedRoute">
          <div class="binding-title">当前模型映射候选</div>
          <div class="binding-line">主路由：{{ selectedRoute.provider_name }} / {{ selectedRoute.provider_model_name }}</div>
          <div class="binding-line">备用路由：{{ selectedRoute.fallback_provider_name || '未配置' }} / {{ selectedRoute.fallback_model_name || '—' }}</div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>主渠道 <span class="req">*</span></label>
            <select v-model="form.primary_provider_id" class="form-select">
              <option value="">— 选择渠道 —</option>
              <option v-for="provider in routeProviderOptions" :key="provider.id" :value="provider.id">{{ provider.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>备渠道（可选）</label>
            <select v-model="form.secondary_provider_id" class="form-select">
              <option value="">无</option>
              <option v-for="provider in routeSecondaryOptions" :key="provider.id" :value="provider.id">{{ provider.name }}</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>重试次数</label>
            <input type="number" v-model.number="form.retry_count" class="form-input" min="0" />
          </div>
          <div class="form-group">
            <label>超时（秒）</label>
            <input type="number" v-model.number="form.timeout_seconds" class="form-input" />
          </div>
          <div class="form-group">
            <label>冷却（秒）</label>
            <input type="number" v-model.number="form.cooldown_seconds" class="form-input" />
          </div>
        </div>
        <div class="form-group">
          <label>备注</label>
          <input v-model="form.notes" class="form-input" placeholder="如：主 OpenAI，备 Minimax" />
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
          <input class="filter-input" placeholder="搜索策略名称" v-model="filters.search" />
          <input class="filter-input" placeholder="公版模型名" v-model="filters.public_model_name" />
          <select class="filter-select" v-model="filters.policy_type">
            <option value="">全部类型</option>
            <option value="fixed">fixed</option>
            <option value="fallback">fallback</option>
            <option value="weighted">weighted</option>
            <option value="cost_first">cost_first</option>
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
              <th>名称</th>
              <th>公版模型</th>
              <th>主渠道</th>
              <th>备渠道</th>
              <th>类型</th>
              <th>重试 / 超时 / 冷却</th>
              <th>绑定状态</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="9" class="td-center td-pad">加载中…</td></tr>
            <tr v-else-if="error"><td colspan="9" class="td-center td-pad td-error">{{ error }}</td></tr>
            <tr v-else-if="displayItems.length === 0"><td colspan="9" class="td-center td-pad"><AdminEmptyState icon="⚙️" title="暂无策略" desc="先配置模型映射，再按模型配置具体路由策略。" /></td></tr>
            <tr v-else v-for="item in displayItems" :key="item.id" class="tr-body">
              <td>
                <strong>{{ item.name }}</strong>
                <div class="sub-line">{{ item.notes || '—' }}</div>
              </td>
              <td>{{ item.public_model_name }}</td>
              <td>{{ item.primary_provider_name || item.primary_provider_id }}</td>
              <td>{{ item.secondary_provider_name || '—' }}</td>
              <td><span class="badge-type">{{ item.policy_type }}</span></td>
              <td>{{ item.retry_count }} / {{ item.timeout_seconds }}s / {{ item.cooldown_seconds }}s</td>
              <td>
                <div class="sub-line">模型映射 {{ item.route_ready ? '已就绪' : '缺失' }}</div>
                <div class="sub-line">Provider 对 {{ item.route_provider_pair_valid ? '匹配' : '不匹配' }}</div>
              </td>
              <td><AdminStatusBadge :value="item.is_active ? 'active' : 'disabled'" /></td>
              <td>
                <div class="td-actions">
                  <button class="btn-action-sm" @click="openEdit(item)">编辑</button>
                  <button v-if="item.is_active" class="btn-danger-sm" @click="confirmToggle(item)">停用</button>
                  <button v-else class="btn-success-sm" @click="confirmToggle(item)">启用</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination-bar">
        <span class="page-info">共 {{ displayItems.length }} 条</span>
      </div>
    </AdminSectionCard>

    <div v-if="confirm.show" class="modal-mask">
      <div class="confirm-box">
        <h3 class="confirm-title">{{ confirm.title }}</h3>
        <p class="confirm-msg">{{ confirm.msg }}</p>
        <div class="modal-actions">
          <button class="btn-outline" @click="confirm.show=false">取消</button>
          <button :class="['btn-confirm', confirm.danger ? 'btn-danger' : 'btn-primary']" @click="doConfirm">确认{{ confirm.title }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminTableToolbar from '@/components/admin/AdminTableToolbar.vue'
import AdminFilterBar from '@/components/admin/AdminFilterBar.vue'
import AdminStatusBadge from '@/components/admin/AdminStatusBadge.vue'
import AdminEmptyState from '@/components/admin/AdminEmptyState.vue'
import { adminRoutePoliciesApi, type AdminRoutePolicy, type RoutePolicyType } from '@/api/adminRoutePolicies'
import { adminModelRoutesApi, type AdminModelRoute } from '@/api/adminModelRoutes'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()
const items = ref<AdminRoutePolicy[]>([])
const modelRoutes = ref<AdminModelRoute[]>([])
const loading = ref(false)
const error = ref('')
const showForm = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const filters = reactive({ search: '', public_model_name: '', policy_type: '', is_active: '' })

const defaultForm = () => ({
  name: '',
  public_model_name: '',
  primary_provider_id: '',
  secondary_provider_id: '',
  policy_type: 'fixed' as RoutePolicyType,
  retry_count: 1,
  timeout_seconds: 60,
  cooldown_seconds: 60,
  notes: '',
  is_active: true,
})
const form = reactive(defaultForm())
const confirm = reactive({ show: false, title: '', msg: '', danger: false, action: null as null | (() => Promise<void>) })

const selectedRoute = computed(() => modelRoutes.value.find((route) => route.public_model_name === form.public_model_name) || null)
const routeProviderOptions = computed(() => {
  if (!selectedRoute.value) return []
  const options = [{ id: selectedRoute.value.provider_id, name: selectedRoute.value.provider_name || `Provider #${selectedRoute.value.provider_id}` }]
  if (selectedRoute.value.fallback_provider_id) {
    options.push({ id: selectedRoute.value.fallback_provider_id, name: selectedRoute.value.fallback_provider_name || `Provider #${selectedRoute.value.fallback_provider_id}` })
  }
  return options
})
const routeSecondaryOptions = computed(() => routeProviderOptions.value.filter((provider) => String(provider.id) !== String(form.primary_provider_id)))

const displayItems = computed(() => {
  const searchKeyword = filters.search.trim().toLowerCase()
  const modelKeyword = filters.public_model_name.trim().toLowerCase()
  return items.value.filter((item) => {
    const matchSearch = !searchKeyword || item.name.toLowerCase().includes(searchKeyword)
    const matchModel = !modelKeyword || item.public_model_name.toLowerCase().includes(modelKeyword)
    const matchType = !filters.policy_type || item.policy_type === filters.policy_type
    const matchStatus = !filters.is_active || String(item.is_active) === filters.is_active
    return matchSearch && matchModel && matchType && matchStatus
  })
})
const readyPolicyCount = computed(() => displayItems.value.filter((item) => item.route_ready && item.route_provider_pair_valid).length)
const advancedPolicyCount = computed(() => displayItems.value.filter((item) => ['fallback', 'weighted', 'cost_first'].includes(item.policy_type)).length)
const invalidBindingCount = computed(() => displayItems.value.filter((item) => !item.route_provider_pair_valid).length)

const fetchAll = async () => {
  loading.value = true
  error.value = ''
  try {
    const [policies, routes] = await Promise.all([
      adminRoutePoliciesApi.list(),
      adminModelRoutesApi.list(),
    ])
    items.value = policies
    modelRoutes.value = routes
  } catch (e: any) {
    error.value = e.message || '加载失败'
    items.value = []
  } finally {
    loading.value = false
  }
}

const handleModelChange = () => {
  const route = selectedRoute.value
  if (!route) return
  form.primary_provider_id = String(route.provider_id)
  form.secondary_provider_id = route.fallback_provider_id ? String(route.fallback_provider_id) : ''
}

const openCreate = () => {
  editingId.value = null
  Object.assign(form, defaultForm())
  showForm.value = true
}

const openEdit = (policy: AdminRoutePolicy) => {
  editingId.value = policy.id
  Object.assign(form, {
    name: policy.name,
    public_model_name: policy.public_model_name,
    primary_provider_id: String(policy.primary_provider_id),
    secondary_provider_id: policy.secondary_provider_id ? String(policy.secondary_provider_id) : '',
    policy_type: policy.policy_type,
    retry_count: policy.retry_count ?? 1,
    timeout_seconds: policy.timeout_seconds ?? 60,
    cooldown_seconds: policy.cooldown_seconds ?? 60,
    notes: policy.notes || '',
    is_active: policy.is_active,
  })
  showForm.value = true
}

const closeForm = () => {
  showForm.value = false
  editingId.value = null
  Object.assign(form, defaultForm())
}

const handleSave = async () => {
  if (!form.name?.trim() || !form.public_model_name?.trim() || !form.primary_provider_id) {
    feedback.warning('请填写策略名称、公版模型名和主渠道')
    return
  }
  saving.value = true
  const currentEditing = editingId.value
  try {
    const payload: any = {
      name: form.name.trim(),
      public_model_name: form.public_model_name.trim(),
      primary_provider_id: Number(form.primary_provider_id),
      secondary_provider_id: form.secondary_provider_id ? Number(form.secondary_provider_id) : null,
      policy_type: form.policy_type,
      retry_count: form.retry_count,
      timeout_seconds: form.timeout_seconds,
      cooldown_seconds: form.cooldown_seconds,
      notes: form.notes.trim() || null,
      is_active: form.is_active,
    }
    if (currentEditing) {
      await adminRoutePoliciesApi.update(currentEditing, payload)
    } else {
      await adminRoutePoliciesApi.create(payload)
    }
    closeForm()
    feedback.success(currentEditing ? '策略已更新' : '策略已创建')
    await fetchAll()
  } catch (e: any) {
    feedback.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const confirmToggle = (policy: AdminRoutePolicy) => {
  confirm.title = policy.is_active ? '停用策略' : '启用策略'
  confirm.msg = `确定要${policy.is_active ? '停用' : '启用'}「${policy.name}」吗？`
  confirm.danger = policy.is_active
  confirm.action = async () => {
    await adminRoutePoliciesApi.update(policy.id, { is_active: !policy.is_active })
    feedback.success(policy.is_active ? '策略已停用' : '策略已启用')
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

onMounted(fetchAll)
</script>

<style scoped>
.page-title-row { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:20px; }
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; margin:0; }
.page-subtitle { margin:6px 0 0; color:#667085; font-size:13px; }
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
.span2 { flex:2; }
.form-group { flex:1; margin-bottom:14px; }
.form-group label { display:block; font-size:12px; color:#666; margin-bottom:4px; font-weight:600; }
.req { color:#ff4d4f; }
.field-help { margin-top:6px; font-size:12px; color:#667085; }
.binding-preview { background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:12px 14px; margin-bottom:14px; }
.binding-title { font-size:13px; font-weight:700; color:#1a1a2e; margin-bottom:8px; }
.binding-line { font-size:12px; color:#667085; line-height:1.5; }
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
.badge-type { font-size:11px; background:#f0f0ff; color:#5b53ff; padding:2px 8px; border-radius:10px; font-weight:600; }
.sub-line { margin-top:4px; font-size:12px; color:#667085; }
.td-actions { display:flex; gap:6px; }
.btn-action-sm { font-size:11px; padding:3px 8px; color:#1677ff; background:none; border:1px solid #1677ff; border-radius:4px; cursor:pointer; }
.btn-danger-sm { font-size:11px; padding:3px 8px; color:#ff4d4f; background:none; border:1px solid #ff4d4f; border-radius:4px; cursor:pointer; }
.btn-success-sm { font-size:11px; padding:3px 8px; color:#52c41a; background:none; border:1px solid #52c41a; border-radius:4px; cursor:pointer; }
.pagination-bar { display:flex; align-items:center; justify-content:flex-end; padding:12px 20px; border-top:1px solid #f0f0f0; }
.page-info { font-size:13px; color:#888; }
.confirm-box { background:#fff; border-radius:12px; padding:28px; width:420px; max-width:95vw; box-shadow:0 8px 32px rgba(0,0,0,0.15); }
.confirm-title { font-size:16px; font-weight:700; margin:0 0 12px; color:#1a1a2e; }
.confirm-msg { font-size:13px; color:#555; margin:0 0 20px; }
.btn-confirm { font-size:13px; padding:8px 18px; border:none; border-radius:6px; cursor:pointer; }
.btn-danger { background:#ff4d4f; color:#fff; }

@media (max-width: 980px) {
  .overview-grid { grid-template-columns:repeat(2, 1fr); }
}

@media (max-width: 720px) {
  .page-title-row, .title-actions, .form-row { flex-direction:column; }
  .overview-grid { grid-template-columns:1fr; }
}
</style>
