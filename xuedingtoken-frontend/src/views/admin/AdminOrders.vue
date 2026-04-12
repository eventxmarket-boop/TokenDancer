<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">订单管理</h1>
      <button class="btn-outline-sm" @click="fetchOrders">🔄 刷新</button>
    </div>

    <AdminSectionCard>
      <AdminTableToolbar>
        <AdminFilterBar>
          <input class="filter-input" placeholder="搜索订单号" v-model="filters.order_no" @input="debouncedFetch" />
          <select class="filter-select" v-model="filters.status" @change="fetchOrders">
            <option value="">全部状态</option>
            <option value="pending">待支付</option>
            <option value="paid">已支付</option>
            <option value="delivered">已发货</option>
            <option value="completed">已完成</option>
            <option value="refunded">已退款</option>
            <option value="cancelled">已取消</option>
            <option value="failed">失败</option>
          </select>
        </AdminFilterBar>
      </AdminTableToolbar>

      <div class="table-wrap">
        <table class="admin-table">
          <thead><tr>
            <th>订单号</th><th>用户</th><th>金额</th><th>状态</th><th>支付方式</th><th>创建时间</th><th>操作</th>
          </tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="7" class="td-center td-pad">加载中…</td></tr>
            <tr v-else-if="error"><td colspan="7" class="td-center td-pad td-error">{{ error }}</td></tr>
            <tr v-else-if="orders.length === 0"><td colspan="7" class="td-center td-pad"><AdminEmptyState icon="🧾" title="暂无订单" /></td></tr>
            <tr v-else v-for="o in orders" :key="o.id" class="tr-body">
              <td><code class="order-no">{{ o.order_no }}</code></td>
              <td>{{ o.user_email || '用户#' + o.user_id || '—' }}</td>
              <td class="td-money">¥{{ typeof o.total_amount === 'number' ? o.total_amount.toFixed(2) : o.total_amount }}</td>
              <td><AdminStatusBadge :value="o.status" /></td>
              <td>{{ o.payment_method || '—' }}</td>
              <td>{{ fmtDate(o.created_at) }}</td>
              <td>
                <div class="td-actions">
                  <button class="btn-action-sm" @click="openDetail(o)">详情</button>
                  <button class="btn-action-sm" @click="showStatusChange(o)">改状态</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination-bar">
        <span class="page-info">共 {{ orders.length }} 条</span>
      </div>
    </AdminSectionCard>

    <!-- 订单详情抽屉 -->
    <AdminDetailDrawer v-model="showDetail" :title="'订单 ' + (selectedOrder?.order_no || '')">
      <template v-if="selectedOrder">
        <div class="detail-section-title">基本信息</div>
        <div class="detail-grid">
          <div class="detail-row"><span class="detail-label">订单ID</span><span>{{ selectedOrder.id }}</span></div>
          <div class="detail-row"><span class="detail-label">订单号</span><code>{{ selectedOrder.order_no }}</code></div>
          <div class="detail-row"><span class="detail-label">状态</span><AdminStatusBadge :value="selectedOrder.status" /></div>
          <div class="detail-row"><span class="detail-label">金额</span><span class="td-money-lg">¥{{ typeof selectedOrder.total_amount === 'number' ? selectedOrder.total_amount.toFixed(2) : selectedOrder.total_amount }}</span></div>
          <div class="detail-row"><span class="detail-label">支付方式</span><span>{{ selectedOrder.payment_method || '—' }}</span></div>
          <div class="detail-row"><span class="detail-label">优惠券</span><span>{{ selectedOrder.coupon_code || '无' }}</span></div>
          <div class="detail-row"><span class="detail-label">创建时间</span><span>{{ fmtDate(selectedOrder.created_at) }}</span></div>
          <div class="detail-row"><span class="detail-label">更新时间</span><span>{{ fmtDate(selectedOrder.updated_at) }}</span></div>
        </div>

        <div v-if="selectedOrder.items?.length" class="detail-section-title" style="margin-top:24px">订单商品</div>
        <div v-if="selectedOrder.items?.length" class="order-items">
          <div v-for="item in selectedOrder.items" :key="item.id" class="order-item-row">
            <span class="item-name">{{ item.product_name }}</span>
            <span class="item-qty">x{{ item.quantity }}</span>
            <span class="item-price">¥{{ typeof item.subtotal === 'number' ? item.subtotal.toFixed(2) : item.subtotal }}</span>
          </div>
        </div>
      </template>

      <template #footer>
        <button class="btn-outline" @click="showDetail = false">关闭</button>
      </template>
    </AdminDetailDrawer>

    <!-- 改状态弹窗 -->
    <div v-if="showStatusModal" class="modal-mask">
      <div class="confirm-box">
        <h3 class="confirm-title">修改订单状态</h3>
        <p class="confirm-msg">订单：<code>{{ statusTarget?.order_no }}</code></p>
        <div class="form-group">
          <label>新状态</label>
          <select class="form-select" v-model="newStatus">
            <option value="pending">待支付</option>
            <option value="paid">已支付</option>
            <option value="delivered">已发货</option>
            <option value="completed">已完成</option>
            <option value="cancelled">已取消</option>
            <option value="refunded">已退款</option>
            <option value="failed">失败</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn-outline" @click="showStatusModal = false">取消</button>
          <div v-if="confirmChange" class="confirm-warning">
            <span>⚠️ 确认要修改订单状态？</span>
          </div>
          <div class="modal-actions">
            <button class="btn-outline" @click="showStatusModal = false">取消</button>
            <button class="btn-danger" @click="doStatusChange" :disabled="savingStatus">{{ confirmChange ? '确认修改' : '下一步' }}</button>
          </div>
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
import { adminOrdersApi } from '@/api/admin'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()
const orders = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const filters = reactive({ order_no: '', status: '' })

const showDetail = ref(false)
const selectedOrder = ref<any>(null)
const showStatusModal = ref(false)
const statusTarget = ref<any>(null)
const newStatus = ref('')
const savingStatus = ref(false)
const confirmChange = ref(false)

let debounceTimer: ReturnType<typeof setTimeout>
const debouncedFetch = () => { clearTimeout(debounceTimer); debounceTimer = setTimeout(fetchOrders, 350) }

const fmtDate = (d: string) => d ? new Date(d).toLocaleString('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) : '—'

const fetchOrders = async () => {
  loading.value = true; error.value = ''
  try { orders.value = await adminOrdersApi.list({ ...filters }) }
  catch (e: any) { error.value = '加载失败：' + (e.message || '未知错误'); orders.value = [] }
  finally { loading.value = false }
}

const openDetail = async (o: any) => {
  try {
    selectedOrder.value = await adminOrdersApi.get(o.id)
    showDetail.value = true
  } catch { feedback.error('获取详情失败') }
}

const showStatusChange = (o: any) => {
  statusTarget.value = o
  newStatus.value = o.status
  showStatusModal.value = true
  confirmChange.value = false // reset confirm
}
const doStatusChange = async () => {
  if (!confirmChange.value) { confirmChange.value = true; return }
  if (!statusTarget.value) return
  savingStatus.value = true
  try {
    const updated = await adminOrdersApi.updateStatus(statusTarget.value.id, newStatus.value)
    statusTarget.value.status = updated.status
    if (selectedOrder.value?.id === statusTarget.value.id) selectedOrder.value.status = updated.status
    showStatusModal.value = false
    feedback.success('状态已更新')
  } catch (e: any) { feedback.error(e.message || '更新失败') }
  finally { savingStatus.value = false }
}

fetchOrders()
</script>

<style scoped>
.page-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }

.table-wrap { overflow-x:auto; }
.admin-table { width:100%; border-collapse:collapse; font-size:13px; }
.admin-table th { text-align:left; padding:10px 14px; font-size:11px; font-weight:700; color:#999; text-transform:uppercase; letter-spacing:0.5px; background:#fafafa; border-bottom:1px solid #f0f0f0; white-space:nowrap; }
.admin-table td { padding:10px 14px; border-bottom:1px solid #f5f5f5; color:#333; }
.tr-body:hover td { background:#fafafa; }
.tr-body:last-child td { border-bottom:none; }
.td-center { text-align:center; }
.td-pad { padding:32px !important; }
.td-error { color:#ff4d4f; }
.order-no { font-size:11px; background:#f5f5f5; padding:1px 5px; border-radius:3px; }
.td-money { font-weight:600; color:#1677ff; }
.td-money-lg { font-size:18px; font-weight:700; color:#1677ff; }

.td-actions { display:flex; gap:6px; }
.btn-action-sm { font-size:11px; padding:3px 8px; color:#1677ff; background:none; border:1px solid #1677ff; border-radius:4px; cursor:pointer; }
.btn-action-sm:hover { background:#e6f7ff; }

.filter-input, .filter-select { font-size:13px; padding:6px 10px; border:1px solid #e8e8e8; border-radius:6px; background:#fff; outline:none; color:#333; }
.filter-input:focus, .filter-select:focus { border-color:#1677ff; }
.filter-input { min-width:180px; }

.pagination-bar { display:flex; align-items:center; justify-content:flex-end; padding:12px 20px; border-top:1px solid #f0f0f0; }
.page-info { font-size:13px; color:#888; }

.detail-section-title { font-size:13px; font-weight:700; color:#1a1a2e; margin:0 0 12px; padding-bottom:8px; border-bottom:1px solid #f0f0f0; }
.detail-grid { display:flex; flex-direction:column; }
.detail-row { display:flex; align-items:center; justify-content:space-between; padding:10px 0; border-bottom:1px solid #f5f5f5; font-size:13px; }
.detail-row:last-child { border-bottom:none; }
.detail-label { color:#888; font-size:12px; font-weight:600; }

.order-items { display:flex; flex-direction:column; gap:8px; }
.order-item-row { display:flex; align-items:center; justify-content:space-between; padding:10px 12px; background:#fafafa; border-radius:8px; font-size:13px; }
.item-name { flex:1; font-weight:500; }
.item-qty { color:#888; margin:0 12px; }
.item-price { font-weight:600; color:#1677ff; }

/* Status modal */
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.45); display:flex; align-items:center; justify-content:center; z-index:1100; }
.confirm-box { background:#fff; border-radius:12px; padding:28px; width:420px; max-width:95vw; box-shadow:0 8px 32px rgba(0,0,0,0.15); }
.confirm-title { font-size:16px; font-weight:700; margin:0 0 12px; color:#1a1a2e; }
.confirm-msg { font-size:13px; color:#555; margin:0 0 16px; }
.form-group { margin-bottom:16px; }
.form-group label { display:block; font-size:12px; color:#666; margin-bottom:4px; font-weight:600; }
.form-select { width:100%; font-size:13px; padding:8px 10px; border:1px solid #e8e8e8; border-radius:6px; outline:none; color:#333; box-sizing:border-box; }
.modal-actions { display:flex; justify-content:flex-end; gap:12px; margin-top:20px; }
.btn-outline { font-size:13px; padding:8px 18px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.btn-danger { font-size:13px; padding:8px 18px; background:#ff4d4f; color:#fff; border:none; border-radius:6px; cursor:pointer; }
.btn-danger:disabled { opacity:0.6; cursor:not-allowed; }
</style>
