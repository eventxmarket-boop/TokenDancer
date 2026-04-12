<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">兑换码管理</h1>
      <div class="title-actions">
        <button class="btn-outline-sm" @click="fetchCodes">🔄 刷新</button>
        <button class="btn-primary" @click="openCreate">+ 创建兑换码</button>
      </div>
    </div>

    <!-- 创建弹窗 -->
    <div v-if="showCreate" class="modal-mask">
      <div class="modal-box">
        <h3 class="modal-title">创建兑换码</h3>
        <div class="form-row">
          <div class="form-group">
            <label>奖励类型</label>
            <select class="form-select" v-model="form.reward_type">
              <option value="balance">余额</option>
              <option value="coupon">优惠券</option>
            </select>
          </div>
          <div class="form-group">
            <label>奖励金额</label>
            <input type="number" v-model.number="form.reward_amount" class="form-input" placeholder="如：10" min="0" step="0.01" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>兑换码（留空自动生成）</label>
            <input v-model="form.code" class="form-input" placeholder="不填则自动生成" />
          </div>
          <div class="form-group">
            <label>过期时间（可选）</label>
            <input type="date" v-model="form.expires_at" class="form-input" />
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-outline" @click="closeCreate">取消</button>
          <button class="btn-primary" @click="handleCreate" :disabled="creating">
            {{ creating ? '创建中…' : '确认创建' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 列表 -->
    <AdminSectionCard>
      <AdminTableToolbar>
        <AdminFilterBar>
          <input class="filter-input" placeholder="搜索兑换码" v-model="filters.code" @input="debouncedFetch" />
          <select class="filter-select" v-model="filters.is_used" @change="fetchCodes">
            <option value="">全部</option>
            <option value="false">未使用</option>
            <option value="true">已使用</option>
          </select>
        </AdminFilterBar>
      </AdminTableToolbar>

      <div class="table-wrap">
        <table class="admin-table">
          <thead><tr>
            <th>兑换码</th><th>类型</th><th>金额</th><th>状态</th>
            <th>使用人</th><th>过期时间</th><th>创建时间</th><th>操作</th>
          </tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="8" class="td-center td-pad">加载中…</td></tr>
            <tr v-else-if="error"><td colspan="8" class="td-center td-pad td-error">{{ error }}</td></tr>
            <tr v-else-if="codes.length === 0"><td colspan="8" class="td-center td-pad"><AdminEmptyState icon="🎫" title="暂无兑换码" /></td></tr>
            <tr v-else v-for="c in codes" :key="c.id" class="tr-body">
              <td><code class="code-text">{{ c.code }}</code></td>
              <td>{{ c.reward_type === 'balance' ? '余额' : '优惠券' }}</td>
              <td class="td-amount">{{ c.reward_amount }}</td>
              <td>
                <AdminStatusBadge v-if="c.is_used" value="used" />
                <AdminStatusBadge v-else-if="c.is_expired" value="expired" />
                <AdminStatusBadge v-else value="unused" />
              </td>
              <td>{{ c.used_by ? '用户#' + c.used_by : '—' }}</td>
              <td>{{ c.expires_at ? new Date(c.expires_at).toLocaleDateString('zh-CN') : '永不过期' }}</td>
              <td>{{ fmtDate(c.created_at) }}</td>
              <td>
                <button v-if="!c.is_used" class="btn-danger-sm" @click="confirmDelete(c)">删除</button>
                <span v-else class="text-muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination-bar">
        <span class="page-info">共 {{ codes.length }} 条</span>
      </div>
    </AdminSectionCard>

    <!-- 确认删除 -->
    <div v-if="confirmDeleteVisible" class="modal-mask">
      <div class="confirm-box">
        <h3 class="confirm-title">确认删除</h3>
        <p class="confirm-msg">确定删除兑换码 <code>{{ deleteTarget?.code }}</code>？此操作不可恢复。</p>
        <div class="modal-actions">
          <button class="btn-outline" @click="confirmDeleteVisible = false">取消</button>
          <button class="btn-danger" @click="doDelete" :disabled="deleting">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminTableToolbar from '@/components/admin/AdminTableToolbar.vue'
import AdminFilterBar from '@/components/admin/AdminFilterBar.vue'
import AdminStatusBadge from '@/components/admin/AdminStatusBadge.vue'
import AdminEmptyState from '@/components/admin/AdminEmptyState.vue'
import { adminRedeemCodesApi } from '@/api/admin'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()
const codes = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const showCreate = ref(false)
const creating = ref(false)
const filters = reactive({ code: '', is_used: '' })
const form = reactive({ reward_type: 'balance', reward_amount: 10, code: '', expires_at: '' })

const confirmDeleteVisible = ref(false)
const deleteTarget = ref<any>(null)
const deleting = ref(false)

const defaultForm = () => ({ reward_type: 'balance', reward_amount: 10, code: '', expires_at: '' })

let debounceTimer: ReturnType<typeof setTimeout>
const debouncedFetch = () => { clearTimeout(debounceTimer); debounceTimer = setTimeout(fetchCodes, 350) }

const fmtDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '—'

const fetchCodes = async () => {
  loading.value = true; error.value = ''
  try {
    const params: any = {}
    if (filters.code) params.code = filters.code
    if (filters.is_used !== '') params.is_used = filters.is_used === 'true'
    codes.value = await adminRedeemCodesApi.list(params)
  } catch (e: any) { error.value = '加载失败：' + (e.message || ''); codes.value = [] }
  finally { loading.value = false }
}

const openCreate = () => {
  Object.assign(form, defaultForm())
  showCreate.value = true
}

const closeCreate = () => {
  showCreate.value = false
  Object.assign(form, defaultForm())
}

const handleCreate = async () => {
  if (!form.reward_amount || form.reward_amount <= 0) { feedback.warning('请输入正确的奖励金额'); return }
  creating.value = true
  try {
    const payload: any = { reward_type: form.reward_type, reward_amount: form.reward_amount }
    if (form.code.trim()) payload.code = form.code.trim()
    if (form.expires_at) payload.expires_at = form.expires_at
    await adminRedeemCodesApi.create(payload)
    closeCreate()
    feedback.success('兑换码创建成功')
    fetchCodes()
  } catch (e: any) { feedback.error(e.message || '创建失败') }
  finally { creating.value = false }
}

const confirmDelete = (c: any) => { deleteTarget.value = c; confirmDeleteVisible.value = true }

const doDelete = async () => {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await adminRedeemCodesApi.delete(deleteTarget.value.id)
    codes.value = codes.value.filter(x => x.id !== deleteTarget.value!.id)
    confirmDeleteVisible.value = false
    feedback.success('兑换码已删除')
  } catch (e: any) { feedback.error(e.message || '删除失败') }
  finally { deleting.value = false }
}

fetchCodes()
</script>

<style scoped>
.page-container {}
.page-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; }
.title-actions { display:flex; gap:10px; align-items:center; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.btn-outline-sm:hover { color:#333; }
.btn-primary { font-size:13px; padding:8px 18px; background:#1677ff; color:#fff; border:none; border-radius:6px; cursor:pointer; }
.btn-primary:hover { background:#4096ff; }
.btn-primary:disabled { opacity:0.6; cursor:not-allowed; }

.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.45); display:flex; align-items:center; justify-content:center; z-index:1000; }
.modal-box { background:#fff; border-radius:12px; padding:28px; width:480px; max-width:95vw; box-shadow:0 8px 32px rgba(0,0,0,0.15); }
.modal-title { font-size:16px; font-weight:700; margin:0 0 20px; color:#1a1a2e; }
.form-row { display:flex; gap:16px; margin-bottom:0; }
.form-group { flex:1; margin-bottom:14px; }
.form-group label { display:block; font-size:12px; color:#666; margin-bottom:4px; font-weight:600; }
.form-input, .form-select { width:100%; font-size:13px; padding:8px 10px; border:1px solid #e8e8e8; border-radius:6px; outline:none; color:#333; box-sizing:border-box; }
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
.code-text { font-size:11px; background:#f5f5f5; padding:1px 5px; border-radius:3px; }
.td-amount { font-weight:600; color:#52c41a; }
.btn-danger-sm { font-size:11px; padding:3px 8px; color:#ff4d4f; background:none; border:1px solid #ff4d4f; border-radius:4px; cursor:pointer; }
.btn-danger-sm:hover { background:#fff1f0; }
.text-muted { color:#bbb; font-size:12px; }

.filter-input, .filter-select { font-size:13px; padding:6px 10px; border:1px solid #e8e8e8; border-radius:6px; background:#fff; outline:none; color:#333; }
.filter-input:focus, .filter-select:focus { border-color:#1677ff; }
.filter-input { min-width:160px; }

.pagination-bar { display:flex; align-items:center; justify-content:flex-end; padding:12px 20px; border-top:1px solid #f0f0f0; }
.page-info { font-size:13px; color:#888; }

.confirm-box { background:#fff; border-radius:12px; padding:28px; width:420px; max-width:95vw; box-shadow:0 8px 32px rgba(0,0,0,0.15); }
.confirm-title { font-size:16px; font-weight:700; margin:0 0 12px; color:#1a1a2e; }
.confirm-msg { font-size:13px; color:#555; margin:0 0 20px; }
.btn-danger { font-size:13px; padding:8px 18px; background:#ff4d4f; color:#fff; border:none; border-radius:6px; cursor:pointer; }
.btn-danger:disabled { opacity:0.6; cursor:not-allowed; }
</style>
