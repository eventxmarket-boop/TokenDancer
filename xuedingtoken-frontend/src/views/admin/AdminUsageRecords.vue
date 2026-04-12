<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">Usage 明细</h1>
      <button class="btn-outline-sm" @click="fetchUsage">🔄 刷新</button>
    </div>

    <AdminSectionCard>
      <AdminTableToolbar>
        <AdminFilterBar>
          <input class="filter-input" placeholder="用户ID" v-model.number="filters.user_id" type="number" min="1" @change="fetchUsage" />
          <input class="filter-input" placeholder="模型名称（如 gpt-4o）" v-model="filters.model" @change="fetchUsage" />
          <select class="filter-select" v-model="filters.limit" @change="fetchUsage">
            <option :value="50">50条/页</option>
            <option :value="100">100条/页</option>
            <option :value="200">200条/页</option>
          </select>
        </AdminFilterBar>
      </AdminTableToolbar>

      <div class="table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户 / Key</th>
              <th>模型</th>
              <th>Provider</th>
              <th>状态</th>
              <th>Tokens</th>
              <th>成本</th>
              <th>延迟</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="9" class="td-center td-pad">加载中…</td></tr>
            <tr v-else-if="error"><td colspan="9" class="td-center td-pad td-error">{{ error }} <button class="btn-link" @click="fetchUsage">重试</button></td></tr>
            <tr v-else-if="records.length === 0"><td colspan="9" class="td-center td-pad">暂无记录</td></tr>
            <tr v-else v-for="record in records" :key="record.id" class="tr-body">
              <td>{{ record.id }}</td>
              <td>
                <div>用户 {{ record.user_id }}</div>
                <div class="sub-line">API Key {{ record.api_key_id }}</div>
              </td>
              <td>
                <code class="model-tag">{{ record.public_model_name || record.model_name }}</code>
                <div class="sub-line">上游 {{ record.upstream_model_name || record.model_name }}</div>
              </td>
              <td>
                <div>{{ record.provider_id || '—' }}</div>
                <div class="sub-line">Provider Key {{ record.provider_key_id || '—' }}</div>
              </td>
              <td><AdminStatusBadge :value="record.request_status || 'success'" /></td>
              <td>
                <div class="td-num">{{ record.total_tokens.toLocaleString() }}</div>
                <div class="sub-line">in {{ record.input_tokens.toLocaleString() }} / out {{ record.output_tokens.toLocaleString() }}</div>
              </td>
              <td>
                <div class="td-money">总成本 ${{ Number(record.cost_amount ?? record.cost ?? 0).toFixed(6) }}</div>
                <div class="sub-line">余额扣减 ${{ Number(record.cost ?? 0).toFixed(6) }}</div>
              </td>
              <td>{{ record.latency_ms }}ms</td>
              <td>{{ fmtDate(record.requested_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination-bar">
        <span class="page-info">共 {{ total }} 条</span>
        <div class="page-controls">
          <button class="btn-page" :disabled="offset <= 0" @click="changePage(-1)">上一页</button>
          <span class="page-num">{{ currentPage }} / {{ totalPages }}</span>
          <button class="btn-page" :disabled="offset + records.length >= total" @click="changePage(1)">下一页</button>
        </div>
      </div>
    </AdminSectionCard>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { adminFinanceApi } from '@/api/adminFinance'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminTableToolbar from '@/components/admin/AdminTableToolbar.vue'
import AdminFilterBar from '@/components/admin/AdminFilterBar.vue'
import AdminStatusBadge from '@/components/admin/AdminStatusBadge.vue'

const filters = ref({ user_id: undefined as number | undefined, model: '', limit: 50 })
const offset = ref(0)
const total = ref(0)
const records = ref<any[]>([])
const loading = ref(false)
const error = ref('')

const currentPage = computed(() => Math.floor(offset.value / filters.value.limit) + 1)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / filters.value.limit)))

const fmtDate = (value: string) => value ? new Date(value).toLocaleString('zh-CN') : '—'

async function fetchUsage() {
  loading.value = true
  error.value = ''
  try {
    const result = await adminFinanceApi.usage({
      user_id: filters.value.user_id || undefined,
      model: filters.value.model || undefined,
      limit: filters.value.limit,
      offset: offset.value,
    })
    records.value = result?.records || []
    total.value = result?.total || 0
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
  fetchUsage()
}

onMounted(() => fetchUsage())
</script>

<style scoped>
.page-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.page-title { font-size:20px; font-weight:700; color:#222; margin:0; }
.table-wrap { overflow-x:auto; }
.admin-table { width:100%; border-collapse:collapse; font-size:13px; }
.admin-table th { text-align:left; padding:10px 14px; font-size:11px; font-weight:700; color:#999; text-transform:uppercase; letter-spacing:0.5px; background:#fafafa; border-bottom:1px solid #f0f0f0; white-space:nowrap; }
.admin-table td { padding:10px 14px; border-bottom:1px solid #f5f5f5; color:#333; vertical-align:top; }
.tr-body:hover td { background:#fafafa; }
.model-tag { font-size:12px; background:#f0f5ff; color:#3b5bdb; padding:2px 6px; border-radius:4px; }
.sub-line { margin-top:4px; font-size:12px; color:#667085; }
.td-num { text-align:right; font-variant-numeric: tabular-nums; font-weight:600; }
.td-money { color:#1677ff; font-weight:600; }
.pagination-bar { display:flex; align-items:center; justify-content:space-between; padding:14px 16px; border-top:1px solid #f0f0f0; }
.page-info { font-size:13px; color:#888; }
.page-controls { display:flex; align-items:center; gap:12px; }
.page-num { font-size:13px; color:#666; }
.btn-page, .btn-outline-sm { padding:4px 14px; font-size:13px; border:1px solid #d9d9d9; border-radius:6px; background:#fff; cursor:pointer; transition:all 0.15s; }
.btn-page:hover:not(:disabled), .btn-outline-sm:hover { border-color:#1677ff; color:#1677ff; }
.btn-page:disabled { opacity:0.4; cursor:default; }
.btn-link { background:none; border:none; color:#1677ff; cursor:pointer; text-decoration:underline; }
.td-center { text-align:center; }
.td-pad { padding:32px !important; }
.td-error { color:#ff4d4f; }
</style>
