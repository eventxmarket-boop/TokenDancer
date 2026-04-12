<template>
  <div class="page-container">
    <div class="page-title-row">
      <div>
        <h1 class="page-title">Source Key 状态</h1>
        <p class="page-subtitle">核对源 Key 是否成功绑定到 Provider，并观察最近使用、错误与 24h 请求情况。</p>
      </div>
      <div class="title-actions">
        <button class="btn-outline-sm" @click="fetchKeys">🔄 刷新</button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载中…</span>
    </div>
    <div v-else-if="error" class="error-state">
      <span class="error-msg">{{ error }}</span>
      <button class="btn-outline-sm" @click="fetchKeys">重试</button>
    </div>
    <div v-else>
      <AdminSectionCard>
        <AdminTableToolbar>
          <AdminFilterBar>
            <select class="filter-select" v-model="filters.provider_id" @change="fetchKeys">
              <option value="">全部渠道</option>
              <option v-for="provider in providers" :key="provider.id" :value="provider.id">{{ provider.name }}</option>
            </select>
            <select class="filter-select" v-model="filters.status" @change="fetchKeys">
              <option value="">全部状态</option>
              <option value="active">启用</option>
              <option value="disabled">停用</option>
              <option value="invalid">无效</option>
            </select>
          </AdminFilterBar>
        </AdminTableToolbar>

        <div class="table-wrap">
          <table class="admin-table">
            <thead><tr>
              <th>ID</th><th>名称</th><th>所属渠道</th><th>Key（掩码）</th><th>状态</th><th>权重</th><th>24h 请求</th><th>最后使用</th><th>最后错误</th>
            </tr></thead>
            <tbody>
              <tr v-if="keys.length === 0"><td colspan="9" class="td-center td-pad">暂无 Key</td></tr>
              <tr v-else v-for="key in keys" :key="key.id">
                <td>{{ key.id }}</td>
                <td>
                  <strong>{{ key.name || '—' }}</strong>
                  <div class="sub-line">支持模型 {{ key.supported_models || '全部模型' }}</div>
                </td>
                <td>
                  <div>{{ key.provider_name || key.provider_id }}</div>
                  <div class="sub-line">{{ key.provider_type || '—' }} / 健康 {{ key.provider_health_status || 'unknown' }}</div>
                </td>
                <td><code class="key-masked">{{ key.key_masked || '—' }}</code></td>
                <td><AdminStatusBadge :value="key.status" /></td>
                <td>{{ key.weight ?? '—' }}</td>
                <td>
                  <div class="sub-line">总请求 {{ key.request_count_24h }}</div>
                  <div class="sub-line">成功 {{ key.success_count_24h }} / 失败 {{ key.failure_count_24h }}</div>
                </td>
                <td>{{ fmtTime(key.last_used_at) }}</td>
                <td class="td-error">{{ key.last_error || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </AdminSectionCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminTableToolbar from '@/components/admin/AdminTableToolbar.vue'
import AdminFilterBar from '@/components/admin/AdminFilterBar.vue'
import AdminStatusBadge from '@/components/admin/AdminStatusBadge.vue'
import { adminProviderKeysApi, type AdminProviderKey } from '@/api/adminProviderKeys'
import { adminProvidersApi, type AdminProvider } from '@/api/adminProviders'

const loading = ref(true)
const error = ref('')
const keys = ref<AdminProviderKey[]>([])
const providers = ref<AdminProvider[]>([])
const filters = reactive({ provider_id: '', status: '' })

async function fetchKeys() {
  loading.value = true
  error.value = ''
  try {
    const [keyList, providerList] = await Promise.all([
      adminProviderKeysApi.list({ provider_id: filters.provider_id || undefined, status: filters.status || undefined }),
      adminProvidersApi.list(),
    ])
    keys.value = keyList
    providers.value = providerList
  } catch (e: any) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function fmtTime(ts?: string | null) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('zh-CN')
}

fetchKeys()
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 20px; }
.page-title-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.page-title { font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 0; }
.page-subtitle { margin: 6px 0 0; color: #667085; font-size: 13px; }
.title-actions { display: flex; gap: 8px; }
.loading-state, .error-state { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 60px 0; color: #888; }
.error-msg { color: #ff4d4f; }
.spinner { width: 32px; height: 32px; border: 3px solid #e8e8e8; border-top-color: #1677ff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.table-wrap { overflow-x: auto; }
.admin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.admin-table th { background: #fafafa; padding: 10px 12px; text-align: left; font-weight: 600; color: #666; border-bottom: 1px solid #f0f0f0; white-space: nowrap; }
.admin-table td { padding: 10px 12px; border-bottom: 1px solid #f5f5f5; color: #333; vertical-align: top; }
.admin-table tr:last-child td { border-bottom: none; }
.td-center { text-align: center; }
.td-pad { padding: 20px; color: #999; }
.sub-line { margin-top: 4px; font-size: 12px; color: #667085; }
.td-error { color: #b42318; font-size: 12px; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.key-masked { font-size: 12px; color: #888; background: #f5f5f5; padding: 2px 6px; border-radius: 4px; }
</style>
