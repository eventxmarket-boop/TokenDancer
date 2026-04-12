<template>
  <div class="page-container">
    <div class="page-title-row">
      <div>
        <h1 class="page-title">源 Key 池</h1>
        <p class="page-subtitle">先选择已创建的 Provider，再录入真实上游 Key。</p>
      </div>
      <div class="title-actions">
        <button class="btn-outline-sm" @click="fetchAll">🔄 刷新</button>
        <button class="btn-primary" :disabled="!hasProviders" @click="openCreate">+ 新增 Key</button>
      </div>
    </div>

    <div v-if="providerError" class="alert-card alert-danger">{{ providerError }}</div>
    <div v-else-if="!providersLoading && !hasProviders" class="alert-card alert-warning">
      当前还没有 Provider。请先到“渠道管理”创建 Provider，再回来添加源 Key。
    </div>

    <div v-if="showForm" class="modal-mask">
      <div class="modal-box">
        <h3 class="modal-title">{{ editingId ? '编辑源 Key' : '新增源 Key' }}</h3>
        <div class="form-group">
          <label>所属渠道 <span class="req">*</span></label>
          <select v-model="form.provider_id" class="form-select" :disabled="!hasProviders">
            <option value="">{{ hasProviders ? '— 选择渠道 —' : '请先创建 Provider' }}</option>
            <option v-for="provider in providers" :key="provider.id" :value="provider.id">{{ provider.name }} ({{ provider.provider_type }})</option>
          </select>
          <div v-if="!hasProviders" class="field-help">没有可选 Provider，当前无法创建源 Key。</div>
        </div>
        <div class="form-group">
          <label>Key 名称</label>
          <input v-model="form.name" class="form-input" placeholder="如：Minimax 主 Key #1" />
        </div>
        <div class="form-group">
          <label>真实 API Key <span class="req">*</span>
            <span class="label-note">（仅创建/更新时输入，存储后不会回显）</span>
          </label>
          <input v-model="form.api_key" class="form-input" placeholder="sk-..." type="password" />
        </div>
        <div class="form-group">
          <label>支持的模型（逗号分隔）</label>
          <input v-model="form.supported_models" class="form-input" placeholder="如：abab6.5s-chat, minimax-text-01" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>权重</label>
            <input type="number" v-model.number="form.weight" class="form-input" min="0" />
          </div>
          <div class="form-group">
            <label>RPM 上限</label>
            <input type="number" v-model.number="form.rpm_limit" class="form-input" />
          </div>
          <div class="form-group">
            <label>日用量上限</label>
            <input type="number" v-model.number="form.daily_limit" class="form-input" />
          </div>
        </div>
        <div class="form-group">
          <label>状态</label>
          <select v-model="form.status" class="form-select">
            <option value="active">启用</option>
            <option value="disabled">停用</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn-outline" @click="closeForm">取消</button>
          <button class="btn-primary" @click="handleSave" :disabled="saving || !hasProviders">{{ saving ? '保存中…' : '确认' }}</button>
        </div>
      </div>
    </div>

    <AdminSectionCard>
      <AdminTableToolbar>
        <AdminFilterBar>
          <input class="filter-input" placeholder="搜索名称 / 脱敏 Key" v-model="filters.search" @input="debouncedFetch" />
          <select class="filter-select" v-model="filters.provider_id" @change="fetchItems">
            <option value="">全部渠道</option>
            <option v-for="provider in providers" :key="provider.id" :value="provider.id">{{ provider.name }}</option>
          </select>
          <select class="filter-select" v-model="filters.status" @change="fetchItems">
            <option value="">全部状态</option>
            <option value="active">启用</option>
            <option value="disabled">停用</option>
          </select>
        </AdminFilterBar>
      </AdminTableToolbar>

      <div class="table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>渠道</th>
              <th>Key（脱敏）</th>
              <th>支持模型</th>
              <th>状态</th>
              <th>权重</th>
              <th>今日用量</th>
              <th>最后使用</th>
              <th>最后错误</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="11" class="td-center td-pad">加载中…</td></tr>
            <tr v-else-if="error"><td colspan="11" class="td-center td-pad td-error">{{ error }}</td></tr>
            <tr v-else-if="items.length === 0"><td colspan="11" class="td-center td-pad"><AdminEmptyState icon="🔑" title="暂无 Key" desc="先创建 Provider，再录入真实上游 Key。" /></td></tr>
            <tr v-else v-for="item in items" :key="item.id" class="tr-body">
              <td>{{ item.id }}</td>
              <td><strong>{{ item.name }}</strong></td>
              <td>{{ providerMap[item.provider_id] || `Provider #${item.provider_id}` }}</td>
              <td><code class="key-masked">{{ item.key_masked || '—' }}</code></td>
              <td>{{ item.supported_models || '全部模型' }}</td>
              <td><AdminStatusBadge :value="item.status" /></td>
              <td>{{ item.weight }}</td>
              <td>
                <span v-if="item.daily_limit">{{ item.used_count_today || 0 }} / {{ item.daily_limit }}</span>
                <span v-else>—</span>
              </td>
              <td>{{ item.last_used_at ? fmtDate(item.last_used_at) : '—' }}</td>
              <td class="td-error">{{ item.last_error || '—' }}</td>
              <td>
                <div class="td-actions">
                  <button class="btn-action-sm" @click="openEdit(item)">编辑</button>
                  <button v-if="item.status === 'active'" class="btn-danger-sm" @click="confirmToggle(item)">停用</button>
                  <button v-else class="btn-success-sm" @click="confirmToggle(item)">启用</button>
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
import { adminProviderKeysApi } from '@/api/adminProviderKeys'
import { adminProvidersApi } from '@/api/adminProviders'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()
const items = ref<any[]>([])
const providers = ref<any[]>([])
const providersLoading = ref(false)
const providerError = ref('')
const loading = ref(false)
const error = ref('')
const showForm = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const filters = reactive({ search: '', provider_id: '', status: '' })

const providerMap = computed(() => {
  const map: Record<number, string> = {}
  for (const provider of providers.value) map[provider.id] = provider.name
  return map
})
const hasProviders = computed(() => providers.value.length > 0)

const defaultForm = () => ({
  provider_id: '',
  name: '',
  api_key: '',
  supported_models: '',
  weight: 1,
  rpm_limit: 1000,
  daily_limit: 100000,
  status: 'active',
})
const form = reactive(defaultForm())

const confirm = reactive({ show: false, title: '', msg: '', danger: false, action: null as null | (() => Promise<void>) })

let debounceTimer: ReturnType<typeof setTimeout>
const debouncedFetch = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchItems, 350)
}

const fmtDate = (value: string) => value ? new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'

const fetchProviders = async () => {
  providersLoading.value = true
  providerError.value = ''
  try {
    providers.value = await adminProvidersApi.list()
  } catch (e: any) {
    providers.value = []
    providerError.value = `Provider 列表加载失败：${e.message || '未知错误'}`
  } finally {
    providersLoading.value = false
  }
}

const fetchItems = async () => {
  loading.value = true
  error.value = ''
  try {
    const params: any = {}
    if (filters.provider_id) params.provider_id = filters.provider_id
    if (filters.status) params.status = filters.status
    items.value = await adminProviderKeysApi.list(params)
  } catch (e: any) {
    error.value = '加载失败：' + (e.message || '')
    items.value = []
  } finally {
    loading.value = false
  }
}

const fetchAll = async () => {
  await Promise.all([fetchProviders(), fetchItems()])
}

const openCreate = () => {
  if (!hasProviders.value) {
    feedback.warning('请先创建 Provider，再添加源 Key')
    return
  }
  editingId.value = null
  Object.assign(form, defaultForm())
  form.provider_id = String(providers.value[0].id)
  showForm.value = true
}

const openEdit = (key: any) => {
  editingId.value = key.id
  Object.assign(form, {
    provider_id: String(key.provider_id),
    name: key.name,
    api_key: '',
    supported_models: key.supported_models || '',
    weight: key.weight || 1,
    rpm_limit: key.rpm_limit || 1000,
    daily_limit: key.daily_limit || 100000,
    status: key.status,
  })
  showForm.value = true
}

const closeForm = () => {
  showForm.value = false
  editingId.value = null
  Object.assign(form, defaultForm())
}

const handleSave = async () => {
  if (!hasProviders.value) {
    feedback.warning('当前没有可用 Provider，请先创建 Provider')
    return
  }
  if (!form.provider_id) {
    feedback.warning('请选择渠道')
    return
  }
  if (!form.api_key && !editingId.value) {
    feedback.warning('请输入 API Key')
    return
  }

  saving.value = true
  try {
    const payload: any = {
      ...form,
      provider_id: Number(form.provider_id),
      name: form.name.trim(),
      supported_models: form.supported_models.trim() || null,
    }
    if (editingId.value && !form.api_key) {
      delete payload.api_key
    }
    if (editingId.value) {
      await adminProviderKeysApi.update(editingId.value, payload)
    } else {
      await adminProviderKeysApi.create(payload)
    }
    closeForm()
    feedback.success(editingId.value ? 'Key 已更新' : 'Key 已添加')
    await fetchItems()
  } catch (e: any) {
    feedback.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const confirmToggle = (key: any) => {
  const nextStatus = key.status === 'active' ? 'disabled' : 'active'
  confirm.title = key.status === 'active' ? '停用 Key' : '启用 Key'
  confirm.msg = `确定要${key.status === 'active' ? '停用' : '启用'}「${key.name}」吗？`
  confirm.danger = key.status === 'active'
  confirm.action = async () => {
    await adminProviderKeysApi.update(key.id, { status: nextStatus })
    feedback.success(nextStatus === 'active' ? '已启用' : '已停用')
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

fetchAll()
</script>

<style scoped>
.page-title-row { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:20px; }
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; margin:0; }
.page-subtitle { margin:6px 0 0; color:#667085; font-size:13px; }
.title-actions { display:flex; gap:10px; }
.alert-card { padding:12px 16px; border-radius:12px; margin-bottom:16px; font-size:13px; }
.alert-warning { background:#fffbe6; color:#ad6800; border:1px solid #ffe58f; }
.alert-danger { background:#fff1f0; color:#cf1322; border:1px solid #ffccc7; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.btn-primary { font-size:13px; padding:8px 18px; background:#1677ff; color:#fff; border:none; border-radius:6px; cursor:pointer; }
.btn-primary:disabled { opacity:0.6; cursor:not-allowed; }
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.45); display:flex; align-items:center; justify-content:center; z-index:1000; overflow-y:auto; padding:20px; }
.modal-box { background:#fff; border-radius:12px; padding:28px; width:560px; max-width:95vw; box-shadow:0 8px 32px rgba(0,0,0,0.15); }
.modal-title { font-size:16px; font-weight:700; margin:0 0 20px; color:#1a1a2e; }
.form-row { display:flex; gap:12px; }
.form-group { flex:1; margin-bottom:14px; }
.form-group label { display:block; font-size:12px; color:#666; margin-bottom:4px; font-weight:600; }
.req { color:#ff4d4f; }
.label-note { font-weight:400; color:#999; font-size:11px; }
.field-help { margin-top:6px; font-size:12px; color:#667085; }
.form-input, .form-select, .filter-input, .filter-select { width:100%; font-size:13px; padding:8px 10px; border:1px solid #e8e8e8; border-radius:6px; outline:none; color:#333; box-sizing:border-box; background:#fff; }
.form-input:focus, .form-select:focus, .filter-input:focus, .filter-select:focus { border-color:#1677ff; }
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
.td-error { max-width:140px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#ff4d4f; font-size:12px; }
.key-masked { font-family:monospace; font-size:11px; background:#f5f5f5; padding:2px 6px; border-radius:3px; color:#555; }
.td-actions { display:flex; gap:6px; }
.btn-action-sm { font-size:11px; padding:3px 8px; color:#1677ff; background:none; border:1px solid #1677ff; border-radius:4px; cursor:pointer; }
.btn-action-sm:hover { background:#e6f7ff; }
.btn-danger-sm { font-size:11px; padding:3px 8px; color:#ff4d4f; background:none; border:1px solid #ff4d4f; border-radius:4px; cursor:pointer; }
.btn-danger-sm:hover { background:#fff1f0; }
.btn-success-sm { font-size:11px; padding:3px 8px; color:#52c41a; background:none; border:1px solid #52c41a; border-radius:4px; cursor:pointer; }
.btn-success-sm:hover { background:#f6ffed; }
.filter-input { min-width:180px; }
.pagination-bar { display:flex; align-items:center; justify-content:flex-end; padding:12px 20px; border-top:1px solid #f0f0f0; }
.page-info { font-size:13px; color:#888; }
.confirm-box { background:#fff; border-radius:12px; padding:28px; width:420px; max-width:95vw; box-shadow:0 8px 32px rgba(0,0,0,0.15); }
.confirm-title { font-size:16px; font-weight:700; margin:0 0 12px; color:#1a1a2e; }
.confirm-msg { font-size:13px; color:#555; margin:0 0 20px; }
.btn-confirm { font-size:13px; padding:8px 18px; border:none; border-radius:6px; cursor:pointer; }
.btn-danger { background:#ff4d4f; color:#fff; }
@media (max-width: 720px) {
  .page-title-row, .form-row { flex-direction:column; }
}
</style>
