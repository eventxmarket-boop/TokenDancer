<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">用户管理</h1>
      <button class="btn-outline-sm" @click="fetchUsers">🔄 刷新</button>
    </div>

    <!-- 筛选工具栏 -->
    <AdminSectionCard>
      <AdminTableToolbar>
        <AdminFilterBar>
          <input class="filter-input" placeholder="搜索用户名 / 邮箱" v-model="filters.search" @input="debouncedFetch" />
          <select class="filter-select" v-model="filters.role" @change="fetchUsers">
            <option value="">全部角色</option>
            <option value="admin">管理员</option>
            <option value="user">普通用户</option>
          </select>
          <select class="filter-select" v-model="filters.status" @change="fetchUsers">
            <option value="">全部状态</option>
            <option value="active">正常</option>
            <option value="banned">封禁</option>
          </select>
        </AdminFilterBar>
      </AdminTableToolbar>

      <!-- 表格 -->
      <div class="table-wrap">
        <table class="admin-table">
          <thead><tr>
            <th>ID</th><th>用户名</th><th>邮箱</th><th>角色</th><th>状态</th>
            <th>总余额</th><th>可用余额</th><th>注册时间</th><th>操作</th>
          </tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="9" class="td-center td-pad">加载中…</td></tr>
            <tr v-else-if="error"><td colspan="9" class="td-center td-pad td-error">{{ error }}</td></tr>
            <tr v-else-if="users.length === 0"><td colspan="9" class="td-center td-pad"><AdminEmptyState icon="👥" title="暂无用户" /></td></tr>
            <tr v-else v-for="u in users" :key="u.id" class="tr-body">
              <td>{{ u.id }}</td>
              <td class="td-bold">{{ u.username }}</td>
              <td class="td-email">{{ u.email }}</td>
              <td><AdminStatusBadge :value="u.role" type="primary" /></td>
              <td><AdminStatusBadge :value="u.status" /></td>
              <td class="td-balance">¥{{ typeof u.balance === 'number' ? u.balance.toFixed(2) : u.balance ?? '—' }}</td>
              <td class="td-balance">¥{{ typeof u.available_balance === 'number' ? u.available_balance.toFixed(2) : u.available_balance ?? '—' }}</td>
              <td>{{ fmtDate(u.created_at) }}</td>
              <td>
                <div class="td-actions">
                  <button class="btn-action-sm" @click="openDetail(u)">详情</button>
                  <button v-if="u.status === 'active'" class="btn-danger-sm" @click="confirmAction('禁用', u, () => updateUser(u, { status: 'banned' }))">禁用</button>
                  <button v-else class="btn-success-sm" @click="confirmAction('解封', u, () => updateUser(u, { status: 'active' }))">解封</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination-bar">
        <span class="page-info">共 {{ users.length }} 条</span>
      </div>
    </AdminSectionCard>

    <!-- 用户详情抽屉 -->
    <AdminDetailDrawer v-model="showDetail" title="用户详情">
      <template v-if="selectedUser">
        <div class="detail-grid">
          <div class="detail-row"><span class="detail-label">用户ID</span><span>{{ selectedUser.id }}</span></div>
          <div class="detail-row"><span class="detail-label">用户名</span><span>{{ selectedUser.username }}</span></div>
          <div class="detail-row"><span class="detail-label">邮箱</span><span>{{ selectedUser.email }}</span></div>
          <div class="detail-row"><span class="detail-label">角色</span>
            <select class="detail-select" :value="selectedUser.role" @change="e => changeRole(selectedUser, (e.target as HTMLSelectElement).value)">
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
            </select>
          </div>
          <div class="detail-row"><span class="detail-label">状态</span><AdminStatusBadge :value="selectedUser.status" /></div>
          <div class="detail-row"><span class="detail-label">总余额</span>
            <div class="balance-edit">
              <span>¥{{ typeof selectedUser.balance === 'number' ? selectedUser.balance.toFixed(2) : selectedUser.balance ?? '—' }}</span>
              <button class="btn-link-sm" @click="showBalanceEdit = true">调整</button>
            </div>
          </div>
          <div class="detail-row"><span class="detail-label">可用余额</span>
            <span>¥{{ typeof selectedUser.available_balance === 'number' ? selectedUser.available_balance.toFixed(2) : selectedUser.available_balance ?? '—' }}</span>
          </div>
          <div class="detail-row"><span class="detail-label">注册时间</span><span>{{ fmtDate(selectedUser.created_at) }}</span></div>
        </div>

        <!-- 余额调整弹窗 -->
        <div v-if="showBalanceEdit" class="inline-modal">
          <h4 class="inline-modal-title">调整余额</h4>
          <div class="form-group">
            <label>新余额（元）</label>
            <input type="number" class="form-input" v-model.number="newBalance" step="0.01" />
          </div>
          <div class="modal-actions">
            <button class="btn-outline-sm" @click="showBalanceEdit = false; newBalance = 0">取消</button>
            <button class="btn-primary-sm" @click="saveBalance" :disabled="savingBalance">确认</button>
          </div>
        </div>
      </template>

      <template #footer>
        <button class="btn-outline" @click="showDetail = false">关闭</button>
      </template>
    </AdminDetailDrawer>

    <!-- 全局 Confirm -->
    <div v-if="confirmVisible" class="modal-mask">
      <div class="confirm-box">
        <h3 class="confirm-title">{{ confirmTitle }}</h3>
        <p class="confirm-msg">确定要 {{ confirmTitle }} 用户 <strong>{{ confirmTarget?.username }}</strong> 吗？</p>
        <div class="modal-actions">
          <button class="btn-outline" @click="confirmVisible = false">取消</button>
          <button :class="['btn-confirm', confirmDanger ? 'btn-danger' : 'btn-primary']" @click="doConfirm">确认{{ confirmTitle }}</button>
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
import AdminDetailDrawer from '@/components/admin/AdminDetailDrawer.vue'
import { adminUsersApi } from '@/api/admin'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()
const users = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const filters = reactive({ search: '', role: '', status: '' })

// Detail drawer
const showDetail = ref(false)
const selectedUser = ref<any>(null)
const showBalanceEdit = ref(false)
const newBalance = ref(0)
const savingBalance = ref(false)

// Confirm dialog
const confirmVisible = ref(false)
const confirmTitle = ref('')
const confirmDanger = ref(false)
const confirmTarget = ref<any>(null)
let pendingAction: (() => Promise<void>) | null = null

let debounceTimer: ReturnType<typeof setTimeout>
const debouncedFetch = () => { clearTimeout(debounceTimer); debounceTimer = setTimeout(fetchUsers, 350) }

const fmtDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '—'

const fetchUsers = async () => {
  loading.value = true; error.value = ''
  try {
    users.value = await adminUsersApi.list({ ...filters })
  } catch (e: any) {
    error.value = '加载失败：' + (e.message || '未知错误')
    users.value = []
  } finally {
    loading.value = false
  }
}

const openDetail = (u: any) => {
  selectedUser.value = { ...u }
  showBalanceEdit.value = false
  newBalance.value = 0
  showDetail.value = true
}

const confirmAction = (title: string, user: any, actionFn: () => Promise<void>) => {
  confirmTitle.value = title
  confirmDanger.value = title !== '解封'
  confirmTarget.value = user
  pendingAction = actionFn
  confirmVisible.value = true
}

const doConfirm = async () => {
  confirmVisible.value = false
  if (pendingAction) {
    try { await pendingAction(); feedback.success('操作成功') }
    catch (e: any) { feedback.error(e.message || '操作失败') }
  }
}

const updateUser = async (u: any, data: { status?: string; role?: string; balance?: number }) => {
  await adminUsersApi.update(u.id, data)
  Object.assign(u, data)
}

const changeRole = (u: any, role: string) => {
  confirmAction('修改角色为 ' + (role === 'admin' ? '管理员' : '普通用户'), u, async () => {
    await updateUser(u, { role })
    u.role = role
  })
}

const saveBalance = async () => {
  if (!selectedUser.value) return
  savingBalance.value = true
  try {
    await adminUsersApi.update(selectedUser.value.id, { balance: newBalance.value })
    selectedUser.value.balance = newBalance.value
    users.value.forEach(u => { if (u.id === selectedUser.value!.id) u.balance = newBalance.value })
    showBalanceEdit.value = false
    feedback.success('余额已更新')
  } catch (e: any) {
    feedback.error(e.message || '更新失败')
  } finally {
    savingBalance.value = false
  }
}

fetchUsers()
</script>

<style scoped>
.page-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.btn-outline-sm:hover { color:#333; border-color:#333; }

.table-wrap { overflow-x:auto; }
.admin-table { width:100%; border-collapse:collapse; font-size:13px; }
.admin-table th { text-align:left; padding:10px 14px; font-size:11px; font-weight:700; color:#999; text-transform:uppercase; letter-spacing:0.5px; background:#fafafa; border-bottom:1px solid #f0f0f0; white-space:nowrap; }
.admin-table td { padding:10px 14px; border-bottom:1px solid #f5f5f5; color:#333; }
.tr-body:hover td { background:#fafafa; }
.tr-body:last-child td { border-bottom:none; }
.td-center { text-align:center; }
.td-pad { padding:32px !important; }
.td-bold { font-weight:600; }
.td-email { color:#666; font-size:12px; }
.td-balance { font-weight:600; color:#1677ff; }
.td-error { color:#ff4d4f; }

.td-actions { display:flex; gap:6px; align-items:center; }
.btn-action-sm { font-size:11px; padding:3px 8px; color:#1677ff; background:none; border:1px solid #1677ff; border-radius:4px; cursor:pointer; }
.btn-action-sm:hover { background:#e6f7ff; }
.btn-danger-sm { font-size:11px; padding:3px 8px; color:#ff4d4f; background:none; border:1px solid #ff4d4f; border-radius:4px; cursor:pointer; }
.btn-danger-sm:hover { background:#fff1f0; }
.btn-success-sm { font-size:11px; padding:3px 8px; color:#52c41a; background:none; border:1px solid #52c41a; border-radius:4px; cursor:pointer; }
.btn-success-sm:hover { background:#f6ffed; }

.filter-input, .filter-select { font-size:13px; padding:6px 10px; border:1px solid #e8e8e8; border-radius:6px; background:#fff; outline:none; color:#333; }
.filter-input:focus, .filter-select:focus { border-color:#1677ff; }
.filter-input { min-width:180px; }

.pagination-bar { display:flex; align-items:center; justify-content:flex-end; padding:12px 20px; border-top:1px solid #f0f0f0; }
.page-info { font-size:13px; color:#888; }

/* Detail drawer */
.detail-grid { display:flex; flex-direction:column; gap:0; }
.detail-row {
  display:flex; align-items:center; justify-content:space-between;
  padding:12px 0; border-bottom:1px solid #f5f5f5; font-size:13px;
}
.detail-row:last-child { border-bottom:none; }
.detail-label { color:#888; font-size:12px; font-weight:600; min-width:80px; }
.balance-edit { display:flex; align-items:center; gap:12px; font-weight:600; color:#1677ff; }
.btn-link-sm { font-size:12px; color:#1677ff; background:none; border:none; cursor:pointer; text-decoration:underline; padding:0; }
.inline-modal { background:#fafafa; border:1px solid #e8e8e8; border-radius:8px; padding:16px; margin-top:16px; }
.inline-modal-title { font-size:14px; font-weight:700; margin:0 0 12px; }
.form-group { margin-bottom:12px; }
.form-group label { display:block; font-size:12px; color:#666; margin-bottom:4px; }
.form-input { width:100%; font-size:13px; padding:7px 10px; border:1px solid #e8e8e8; border-radius:6px; outline:none; color:#333; box-sizing:border-box; }
.form-input:focus { border-color:#1677ff; }
.modal-actions { display:flex; justify-content:flex-end; gap:10px; margin-top:12px; }

.detail-select { font-size:13px; padding:4px 8px; border:1px solid #e8e8e8; border-radius:4px; outline:none; color:#333; }

/* Confirm */
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.45); display:flex; align-items:center; justify-content:center; z-index:1100; }
.confirm-box { background:#fff; border-radius:12px; padding:28px; width:420px; max-width:95vw; box-shadow:0 8px 32px rgba(0,0,0,0.15); }
.confirm-title { font-size:16px; font-weight:700; margin:0 0 12px; color:#1a1a2e; }
.confirm-msg { font-size:14px; color:#555; margin:0 0 20px; line-height:1.5; }
.btn-outline { font-size:13px; padding:8px 18px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.btn-primary { font-size:13px; padding:8px 18px; background:#1677ff; color:#fff; border:none; border-radius:6px; cursor:pointer; }
.btn-danger { font-size:13px; padding:8px 18px; background:#ff4d4f; color:#fff; border:none; border-radius:6px; cursor:pointer; }
.btn-primary-sm { font-size:13px; padding:7px 16px; background:#1677ff; color:#fff; border:none; border-radius:6px; cursor:pointer; }
.btn-primary-sm:disabled { opacity:0.6; cursor:not-allowed; }
</style>
