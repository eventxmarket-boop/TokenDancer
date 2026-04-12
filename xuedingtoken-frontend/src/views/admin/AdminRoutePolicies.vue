<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">路由策略</h1>
      <div class="title-actions">
        <button class="btn-outline-sm" @click="fetchItems">🔄 刷新</button>
        <button class="btn-primary" @click="openCreate">+ 新增策略</button>
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
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
            <input v-model="form.public_model_name" class="form-input" placeholder="如：gpt-4o" />
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
        <div class="form-row">
          <div class="form-group">
            <label>主渠道 <span class="req">*</span></label>
            <select v-model="form.primary_provider_id" class="form-select">
              <option value="">— 选择渠道 —</option>
              <option v-for="p in providers" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>备渠道（可选）</label>
            <select v-model="form.secondary_provider_id" class="form-select">
              <option value="">无</option>
              <option v-for="p in providers" :key="p.id" :value="p.id">{{ p.name }}</option>
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
          <input v-model="form.notes" class="form-input" placeholder="可选备注…" />
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

    <!-- 列表 -->
    <AdminSectionCard>
      <AdminTableToolbar>
        <AdminFilterBar>
          <input class="filter-input" placeholder="搜索策略名称" v-model="filters.search" @input="debouncedFetch" />
          <input class="filter-input" placeholder="公版模型名" v-model="filters.public_model_name" @input="debouncedFetch" />
          <select class="filter-select" v-model="filters.policy_type" @change="fetchItems">
            <option value="">全部类型</option>
            <option value="fixed">fixed</option>
            <option value="fallback">fallback</option>
            <option value="weighted">weighted</option>
            <option value="cost_first">cost_first</option>
          </select>
          <select class="filter-select" v-model="filters.is_active" @change="fetchItems">
            <option value="">全部状态</option>
            <option :value="true">启用</option>
            <option :value="false">停用</option>
          </select>
        </AdminFilterBar>
      </AdminTableToolbar>

      <div class="table-wrap">
        <table class="admin-table">
          <thead><tr>
            <th>名称</th><th>公版模型</th><th>主渠道</th><th>备渠道</th>
            <th>类型</th><th>重试</th><th>超时</th><th>冷却</th>
            <th>状态</th><th>操作</th>
          </tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="10" class="td-center td-pad">加载中…</td></tr>
            <tr v-else-if="error"><td colspan="10" class="td-center td-pad td-error">{{ error }}</td></tr>
            <tr v-else-if="items.length===0"><td colspan="10" class="td-center td-pad"><AdminEmptyState icon="⚙️" title="暂无策略" /></td></tr>
            <tr v-else v-for="p in items" :key="p.id" class="tr-body">
              <td><strong>{{ p.name }}</strong></td>
              <td>{{ p.public_model_name }}</td>
              <td>{{ providerMap[p.primary_provider_id] || p.primary_provider_id }}</td>
              <td>{{ p.secondary_provider_id ? (providerMap[p.secondary_provider_id] || '—') : '—' }}</td>
              <td><span class="badge-type">{{ p.policy_type }}</span></td>
              <td>{{ p.retry_count ?? 0 }}</td>
              <td>{{ p.timeout_seconds ?? 60 }}s</td>
              <td>{{ p.cooldown_seconds ?? 60 }}s</td>
              <td><AdminStatusBadge :value="p.is_active ? 'active' : 'disabled'" /></td>
              <td>
                <div class="td-actions">
                  <button class="btn-action-sm" @click="openEdit(p)">编辑</button>
                  <button v-if="p.is_active" class="btn-danger-sm" @click="confirmToggle(p)">停用</button>
                  <button v-else class="btn-success-sm" @click="confirmToggle(p)">启用</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination-bar">
        <span class="page-info">共 {{ items.length }} 条</span>
      </div>
    </AdminSectionCard>

    <!-- Confirm -->
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
import { ref, reactive, computed } from 'vue'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminTableToolbar from '@/components/admin/AdminTableToolbar.vue'
import AdminFilterBar from '@/components/admin/AdminFilterBar.vue'
import AdminStatusBadge from '@/components/admin/AdminStatusBadge.vue'
import AdminEmptyState from '@/components/admin/AdminEmptyState.vue'
import { adminRoutePoliciesApi, adminProvidersApi } from '@/api/admin'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()
const items = ref<any[]>([])
const providers = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const showForm = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const filters = reactive({ search: '', public_model_name: '', policy_type: '', is_active: '' })

const providerMap = computed(() => { const m: Record<number,string> = {}; for (const p of providers.value) m[p.id] = p.name; return m })

const defaultForm = () => ({
  name: '', public_model_name: '', primary_provider_id: '', secondary_provider_id: '',
  policy_type: 'fixed', retry_count: 1, timeout_seconds: 60, cooldown_seconds: 60,
  notes: '', is_active: true,
})
const form = reactive(defaultForm())

const confirm = reactive({ show: false, title: '', msg: '', danger: false, target: null as any, action: null as any })

let debounceTimer: ReturnType<typeof setTimeout>
const debouncedFetch = () => { clearTimeout(debounceTimer); debounceTimer = setTimeout(fetchItems, 350) }

const fetchItems = async () => {
  loading.value = true; error.value = ''
  try { items.value = await adminRoutePoliciesApi.list() }
  catch (e: any) { error.value = '加载失败'; items.value = [] }
  finally { loading.value = false }
}

const fetchAll = async () => {
  await Promise.all([
    fetchItems(),
    adminProvidersApi.list().then(p => providers.value = p).catch(() => {})
  ])
}

const openCreate = () => { editingId.value = null; Object.assign(form, defaultForm()); showForm.value = true }
const openEdit = (r: any) => {
  editingId.value = r.id
  Object.assign(form, {
    name: r.name, public_model_name: r.public_model_name,
    primary_provider_id: r.primary_provider_id, secondary_provider_id: r.secondary_provider_id || '',
    policy_type: r.policy_type, retry_count: r.retry_count ?? 1,
    timeout_seconds: r.timeout_seconds ?? 60, cooldown_seconds: r.cooldown_seconds ?? 60,
    notes: r.notes || '', is_active: r.is_active,
  })
  showForm.value = true
}
const closeForm = () => { showForm.value = false; editingId.value = null; Object.assign(form, defaultForm()) }

const handleSave = async () => {
  if (!form.name?.trim() || !form.public_model_name?.trim()) { feedback.warning('请填写策略名称和公版模型名'); return }
  saving.value = true
  try {
    const payload: any = { ...form }
    if (!payload.secondary_provider_id) delete payload.secondary_provider_id
    if (editingId.value) { await adminRoutePoliciesApi.update(editingId.value, payload) }
    else { await adminRoutePoliciesApi.create(payload) }
    closeForm(); feedback.success(editingId.value ? '策略已更新' : '策略已创建'); fetchItems()
  } catch (e: any) { feedback.error(e.message || '保存失败') }
  finally { saving.value = false }
}

const confirmToggle = (r: any) => {
  confirm.title = r.is_active ? '停用策略' : '启用策略'
  confirm.msg = `确定要${r.is_active ? '停用' : '启用'}「${r.name}」吗？`
  confirm.danger = r.is_active; confirm.target = r
  confirm.action = async () => {
    await adminRoutePoliciesApi.update(r.id, { is_active: !r.is_active })
    r.is_active = !r.is_active
    feedback.success(r.is_active ? '已启用' : '已停用')
  }
  confirm.show = true
}
const doConfirm = async () => { confirm.show = false; try { await confirm.action?.() } catch (e: any) { feedback.error(e.message || '操作失败') } }

fetchAll()
</script>

<style scoped>
.page-container {}
.page-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; }
.title-actions { display:flex; gap:10px; }
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
.form-input, .form-select { width:100%; font-size:13px; padding:8px 10px; border:1px solid #e8e8e8; border-radius:6px; outline:none; color:#333; box-sizing:border-box; background:#fff; }
.form-input:focus, .form-select:focus { border-color:#1677ff; }
.modal-actions { display:flex; justify-content:flex-end; gap:12px; margin-top:20px; }
.btn-outline { font-size:13px; padding:8px 18px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }

.table-wrap { overflow-x:auto; }
.admin-table { width:100%; border-collapse:collapse; font-size:13px; }
.admin-table th { text-align:left; padding:10px 14px; font-size:11px; font-weight:700; color:#999; text-transform:uppercase; letter-spacing:0.5px; background:#fafafa; border-bottom:1px solid #f0f0f0; white-space:nowrap; }
.admin-table td { padding:10px 14px; border-bottom:1px solid #f5f5f5; color:#333; }
.tr-body:hover td { background:#fafafa; }
.tr-body:last-child td { border-bottom:none; }
.td-center { text-align:center; }
.td-pad { padding:32px !important; }
.td-error { color:#ff4d4f; }
.badge-type { font-size:11px; background:#f0f0ff; color:#5b53ff; padding:2px 8px; border-radius:10px; font-weight:600; }
.td-actions { display:flex; gap:6px; }
.btn-action-sm { font-size:11px; padding:3px 8px; color:#1677ff; background:none; border:1px solid #1677ff; border-radius:4px; cursor:pointer; }
.btn-action-sm:hover { background:#e6f7ff; }
.btn-danger-sm { font-size:11px; padding:3px 8px; color:#ff4d4f; background:none; border:1px solid #ff4d4f; border-radius:4px; cursor:pointer; }
.btn-danger-sm:hover { background:#fff1f0; }
.btn-success-sm { font-size:11px; padding:3px 8px; color:#52c41a; background:none; border:1px solid #52c41a; border-radius:4px; cursor:pointer; }
.btn-success-sm:hover { background:#f6ffed; }

.filter-input, .filter-select { font-size:13px; padding:6px 10px; border:1px solid #e8e8e8; border-radius:6px; background:#fff; outline:none; color:#333; }
.filter-input:focus, .filter-select:focus { border-color:#1677ff; }
.filter-input { min-width:150px; }

.pagination-bar { display:flex; align-items:center; justify-content:flex-end; padding:12px 20px; border-top:1px solid #f0f0f0; }
.page-info { font-size:13px; color:#888; }

.confirm-box { background:#fff; border-radius:12px; padding:28px; width:420px; max-width:95vw; box-shadow:0 8px 32px rgba(0,0,0,0.15); }
.confirm-title { font-size:16px; font-weight:700; margin:0 0 12px; color:#1a1a2e; }
.confirm-msg { font-size:13px; color:#555; margin:0 0 20px; }
.btn-confirm { font-size:13px; padding:8px 18px; border:none; border-radius:6px; cursor:pointer; }
.btn-primary { background:#1677ff; color:#fff; }
.btn-danger { background:#ff4d4f; color:#fff; }
</style>
