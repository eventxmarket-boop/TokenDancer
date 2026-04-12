<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">Source Key 状态</h1>
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
              <option v-for="p in providers" :key="p.id" :value="p.id">{{ p.name }}</option>
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
              <th>ID</th><th>名称</th><th>所属渠道</th><th>Key（掩码）</th><th>状态</th><th>权重</th><th>最后使用</th><th>最后错误</th>
            </tr></thead>
            <tbody>
              <tr v-if="filteredKeys.length === 0"><td colspan="8" class="td-center td-pad">暂无 Key</td></tr>
              <tr v-else v-for="k in filteredKeys" :key="k.id">
                <td>{{ k.id }}</td>
                <td><strong>{{ k.name || '—' }}</strong></td>
                <td>{{ providerMap[k.provider_id] || k.provider_id }}</td>
                <td><code class="key-masked">{{ k.key_masked || '—' }}</code></td>
                <td><AdminStatusBadge :value="k.status" /></td>
                <td>{{ k.weight ?? '—' }}</td>
                <td>{{ fmtTime(k.last_used_at) }}</td>
                <td class="td-error">{{ k.last_error || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </AdminSectionCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { adminProviderKeysApi } from '@/api/adminProviderKeys'
import { adminProvidersApi } from '@/api/adminProviders'

const loading = ref(true)
const error = ref('')
const keys = ref<any[]>([])
const providers = ref<any[]>([])
const filters = reactive({ provider_id: '', status: '' })

const providerMap = computed(() => {
  const m: Record<number, string> = {}
  providers.value.forEach((p: any) => { m[p.id] = p.name })
  return m
})

const filteredKeys = computed(() => {
  return keys.value.filter((k: any) => {
    if (filters.provider_id && k.provider_id !== Number(filters.provider_id)) return false
    if (filters.status && k.status !== filters.status) return false
    return true
  })
})

async function fetchKeys() {
  loading.value = true
  error.value = ''
  try {
    const [keyList, prov] = await Promise.all([
      adminProviderKeysApi.list() as Promise<any[]>,
      adminProvidersApi.list() as Promise<any[]>,
    ])
    keys.value = keyList
    providers.value = prov
  } catch (e: any) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function fmtTime(ts: string | null) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('zh-CN')
}

fetchKeys()
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 20px; }
.page-title-row { display: flex; align-items: center; justify-content: space-between; }
.page-title { font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 0; }
.title-actions { display: flex; gap: 8px; }
.loading-state, .error-state { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 60px 0; color: #888; }
.error-msg { color: #ff4d4f; }
.spinner { width: 32px; height: 32px; border: 3px solid #e8e8e8; border-top-color: #1677ff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.table-wrap { overflow-x: auto; }
.admin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.admin-table th { background: #fafafa; padding: 10px 12px; text-align: left; font-weight: 600; color: #666; border-bottom: 1px solid #f0f0f0; white-space: nowrap; }
.admin-table td { padding: 10px 12px; border-bottom: 1px solid #f5f5f5; color: #333; }
.admin-table tr:last-child td { border-bottom: none; }
.td-center { text-align: center; }
.td-pad { padding: 20px; color: #999; }
.td-error { color: #ff4d4f; font-size: 12px; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.key-masked { font-size: 12px; color: #888; background: #f5f5f5; padding: 2px 6px; border-radius: 4px; }
</style>
