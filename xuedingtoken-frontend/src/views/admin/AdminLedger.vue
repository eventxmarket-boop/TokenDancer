<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">余额账本</h1>
      <button class="btn-outline-sm" @click="fetchLedger">🔄 刷新</button>
    </div>

    <!-- 筛选栏 -->
    <AdminSectionCard>
      <AdminTableToolbar>
        <AdminFilterBar>
          <input
            class="filter-input"
            placeholder="用户ID"
            v-model.number="filters.user_id"
            type="number"
            min="1"
            @change="fetchLedger"
          />
          <select class="filter-select" v-model="filters.entry_type" @change="fetchLedger">
            <option value="">全部类型</option>
            <option value="redeem_credit">充值</option>
            <option value="usage_debit">API扣费</option>
            <option value="manual_credit">人工增加</option>
            <option value="manual_debit">人工扣减</option>
            <option value="order_refund">订单退款</option>
          </select>
          <select class="filter-select" v-model="filters.limit" @change="fetchLedger">
            <option :value="50">50条/页</option>
            <option :value="100">100条/页</option>
            <option :value="200">200条/页</option>
          </select>
        </AdminFilterBar>
      </AdminTableToolbar>

      <div class="table-wrap">
        <table class="admin-table">
          <thead><tr>
            <th>ID</th>
            <th>用户ID</th>
            <th>用户邮箱</th>
            <th>类型</th>
            <th>金额</th>
            <th>变动前</th>
            <th>变动后</th>
            <th>关联类型</th>
            <th>关联ID</th>
            <th>备注</th>
            <th>时间</th>
          </tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="11" class="td-center td-pad">加载中…</td></tr>
            <tr v-else-if="error"><td colspan="11" class="td-center td-pad td-error">
              {{ error }} <button class="btn-link" @click="fetchLedger">重试</button>
            </td></tr>
            <tr v-else-if="records.length === 0"><td colspan="11" class="td-center td-pad">暂无记录</td></tr>
            <tr v-else v-for="r in records" :key="r.id" class="tr-body">
              <td>{{ r.id }}</td>
              <td>{{ r.user_id }}</td>
              <td>{{ r.user_email || '—' }}</td>
              <td><span class="op-badge" :class="'op-' + r.operation">{{ r.operation }}</span></td>
              <td :class="r.amount >= 0 ? 'td-positive' : 'td-negative'">
                {{ r.amount >= 0 ? '+' : '' }}{{ r.amount.toFixed(4) }}
              </td>
              <td>{{ r.balance_before.toFixed(4) }}</td>
              <td>{{ r.balance_after.toFixed(4) }}</td>
              <td>{{ r.redeem_log_id ? 'redeem' : r.usage_record_id ? 'usage' : r.order_id ? 'order' : '—' }}</td>
              <td>{{ r.redeem_log_id || r.usage_record_id || r.order_id || '—' }}</td>
              <td class="td-remark">{{ r.remark || '—' }}</td>
              <td>{{ fmtDate(r.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="pagination-bar">
        <span class="page-info">共 {{ total }} 条</span>
        <div class="page-controls">
          <button
            class="btn-page"
            :disabled="offset <= 0"
            @click="changePage(-1)"
          >上一页</button>
          <span class="page-num">{{ currentPage }} / {{ totalPages }}</span>
          <button
            class="btn-page"
            :disabled="offset + records.length >= total"
            @click="changePage(1)"
          >下一页</button>
        </div>
      </div>
    </AdminSectionCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { adminFinanceApi } from '@/api/adminFinance'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminTableToolbar from '@/components/admin/AdminTableToolbar.vue'
import AdminFilterBar from '@/components/admin/AdminFilterBar.vue'

const filters = ref({ user_id: undefined as number | undefined, entry_type: '', limit: 50 })
const offset = ref(0)
const total = ref(0)
const records = ref<any[]>([])
const loading = ref(false)
const error = ref('')

const currentPage = computed(() => Math.floor(offset.value / filters.value.limit) + 1)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / filters.value.limit)))

function fmtDate(v: string) {
  if (!v) return '—'
  return new Date(v).toLocaleString('zh-CN')
}

async function fetchLedger() {
  loading.value = true
  error.value = ''
  try {
    const res = await adminFinanceApi.ledger({
      user_id: filters.value.user_id || undefined,
      entry_type: filters.value.entry_type || undefined,
      limit: filters.value.limit,
      offset: offset.value,
    })
    records.value = res?.records || []
    total.value = res?.total || 0
  } catch (e: any) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function changePage(delta: number) {
  const next = offset.value + delta * filters.value.limit
  if (next < 0 || next >= total.value) return
  offset.value = next
  fetchLedger()
}

onMounted(() => fetchLedger())
</script>

<style scoped>
.page-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #222;
  margin: 0;
}
.op-badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}
.op-redeem_credit { background: #f6ffed; color: #52c41a; }
.op-usage_debit { background: #fff1f0; color: #ff4d4f; }
.op-manual_credit { background: #e6f7ff; color: #1677ff; }
.op-manual_debit { background: #fff7e6; color: #fa8c16; }
.op-order_refund { background: #f9f0ff; color: #722ed1; }
.td-positive { color: #52c41a; }
.td-negative { color: #ff4d4f; }
.td-remark {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: #666;
}
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-top: 1px solid #f0f0f0;
}
.page-info { font-size: 13px; color: #888; }
.page-controls { display: flex; align-items: center; gap: 12px; }
.page-num { font-size: 13px; color: #666; }
.btn-page {
  padding: 4px 14px;
  font-size: 13px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-page:hover:not(:disabled) { border-color: #1677ff; color: #1677ff; }
.btn-page:disabled { opacity: 0.4; cursor: default; }
.btn-link { background: none; border: none; color: #1677ff; cursor: pointer; text-decoration: underline; }
</style>
