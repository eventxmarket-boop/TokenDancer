<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">审计日志</h1>
      <button class="btn-outline-sm" @click="fetchLogs">🔄 刷新</button>
    </div>

    <!-- 筛选栏 -->
    <AdminSectionCard>
      <AdminTableToolbar>
        <AdminFilterBar>
          <input
            class="filter-input"
            placeholder="管理员ID"
            v-model.number="filters.admin_user_id"
            type="number"
            min="1"
            @change="fetchLogs"
          />
          <input
            class="filter-input"
            placeholder="操作类型，如 provider_key.create"
            v-model="filters.action"
            @change="fetchLogs"
            style="max-width:220px"
          />
          <input
            class="filter-input"
            placeholder="目标类型，如 provider_key / user / order"
            v-model="filters.target_type"
            @change="fetchLogs"
            style="max-width:200px"
          />
          <select class="filter-select" v-model="filters.limit" @change="fetchLogs">
            <option :value="20">20条/页</option>
            <option :value="50">50条/页</option>
            <option :value="100">100条/页</option>
          </select>
        </AdminFilterBar>
      </AdminTableToolbar>

      <!-- 表格 -->
      <div class="table-wrap">
        <table class="admin-table">
          <thead><tr>
            <th>时间</th>
            <th>管理员ID</th>
            <th>操作</th>
            <th>目标类型</th>
            <th>目标ID</th>
            <th>IP地址</th>
            <th>变更前</th>
            <th>变更后</th>
          </tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="8" class="td-center td-pad">加载中…</td></tr>
            <tr v-else-if="error"><td colspan="8" class="td-center td-pad td-error">{{ error }}</td></tr>
            <tr v-else-if="records.length === 0"><td colspan="8" class="td-center td-pad">暂无记录</td></tr>
            <tr v-else v-for="r in records" :key="r.id" class="tr-body">
              <td class="td-time">{{ fmtDate(r.created_at) }}</td>
              <td>{{ r.admin_user_id ?? '—' }}</td>
              <td><code class="action-code">{{ r.action }}</code></td>
              <td>{{ r.target_type ?? '—' }}</td>
              <td><code>{{ r.target_id ?? '—' }}</code></td>
              <td>{{ r.ip_address ?? '—' }}</td>
              <td>
                <details v-if="r.before_state" class="json-details">
                  <summary>JSON</summary>
                  <pre class="json-pre">{{ fmtJson(r.before_state) }}</pre>
                </details>
                <span v-else class="text-muted">—</span>
              </td>
              <td>
                <details v-if="r.after_state" class="json-details">
                  <summary>JSON</summary>
                  <pre class="json-pre">{{ fmtJson(r.after_state) }}</pre>
                </details>
                <span v-else class="text-muted">—</span>
              </td>
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
            @click="goPage(Math.max(0, offset - pageSize))"
          >上一页</button>
          <span class="page-num">{{ Math.floor(offset / pageSize) + 1 }} / {{ Math.max(1, Math.ceil(total / pageSize)) }}</span>
          <button
            class="btn-page"
            :disabled="offset + pageSize >= total"
            @click="goPage(offset + pageSize)"
          >下一页</button>
        </div>
      </div>
    </AdminSectionCard>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminTableToolbar from '@/components/admin/AdminTableToolbar.vue'
import AdminFilterBar from '@/components/admin/AdminFilterBar.vue'
import { adminAuditApi } from '@/api/adminAudit'

const loading = ref(false)
const error = ref('')
const records = ref<any[]>([])
const total = ref(0)
const offset = ref(0)

const filters = reactive({
  admin_user_id: undefined as number | undefined,
  action: '',
  target_type: '',
  limit: 50,
})

const pageSize = computed(() => filters.limit)

const fmtDate = (d: string) => {
  if (!d) return '—'
  return new Date(d).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

const fmtJson = (s: string) => {
  try { return JSON.stringify(JSON.parse(s), null, 2) }
  catch { return s }
}

const fetchLogs = async () => {
  loading.value = true
  error.value = ''
  try {
    const params: any = { limit: filters.limit, offset: offset.value }
    if (filters.admin_user_id) params.admin_user_id = filters.admin_user_id
    if (filters.action) params.action = filters.action
    if (filters.target_type) params.target_type = filters.target_type
    const res = await adminAuditApi.list(params)
    total.value = res.total
    records.value = res.records
  } catch (e: any) {
    error.value = '加载失败：' + (e.message || '未知错误')
    records.value = []
  } finally {
    loading.value = false
  }
}

const goPage = (newOffset: number) => {
  offset.value = newOffset
  fetchLogs()
}

onMounted(fetchLogs)
</script>

<style scoped>
.page-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-title { font-size: 20px; font-weight: 700; color: #1a1a2e; }

.admin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.admin-table th {
  text-align: left; padding: 10px 12px; font-size: 11px; font-weight: 700;
  color: #999; text-transform: uppercase; letter-spacing: 0.5px;
  background: #fafafa; border-bottom: 1px solid #f0f0f0; white-space: nowrap;
}
.admin-table td { padding: 10px 12px; border-bottom: 1px solid #f5f5f5; color: #333; vertical-align: top; }
.admin-table tr:last-child td { border-bottom: none; }
.tr-body:hover { background: #fafafa; }
.td-center { text-align: center; }
.td-pad { padding: 32px !important; }
.td-error { color: #ff4d4f; }
.td-time { white-space: nowrap; color: #888; font-size: 12px; }
code { font-size: 11px; background: #f5f5f5; padding: 1px 5px; border-radius: 3px; }
.action-code { color: #5b53ff; background: #f0f0ff; }
.text-muted { color: #bbb; }

.json-details { font-size: 11px; }
.json-details summary { cursor: pointer; color: #1677ff; outline: none; }
.json-pre {
  margin-top: 6px; padding: 8px; background: #f5f5f5;
  border-radius: 4px; font-size: 11px; color: #333;
  max-width: 300px; overflow-x: auto; white-space: pre-wrap; word-break: break-all;
}

.pagination-bar { display: flex; align-items: center; justify-content: space-between; padding: 12px 20px; border-top: 1px solid #f0f0f0; }
.page-info { font-size: 13px; color: #888; }
.page-controls { display: flex; align-items: center; gap: 12px; }
.btn-page { font-size: 13px; padding: 5px 14px; border: 1px solid #d9d9d9; border-radius: 6px; background: #fff; cursor: pointer; color: #333; }
.btn-page:disabled { opacity: 0.4; cursor: default; }
.btn-page:not(:disabled):hover { border-color: #1677ff; color: #1677ff; }
.page-num { font-size: 13px; color: #666; }

.table-wrap { overflow-x: auto; }
</style>
