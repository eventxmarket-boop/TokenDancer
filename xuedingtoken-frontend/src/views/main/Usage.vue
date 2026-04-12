<template>
  <MainLayout title="使用记录" subtitle="查看您的 API 使用历史">
    <!-- Stats row -->
    <div class="stats-grid-4">
      <div class="stat-card">
        <div class="stat-label">总请求数</div>
        <div class="stat-value">{{ stats.totalRequests }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">总 Token</div>
        <div class="stat-value">{{ stats.totalTokens.toLocaleString() }}</div>
        <div class="stat-sub">输入: {{ stats.totalInput.toLocaleString() }} / 输出: {{ stats.totalOutput.toLocaleString() }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">总消费</div>
        <div class="stat-value">${{ stats.totalCost }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">平均耗时</div>
        <div class="stat-value">{{ stats.avgLatency }}</div>
      </div>
    </div>

    <!-- Filters -->
    <BaseFilter :showReset="true" :showRefresh="true" :showExport="true" @reset="handleReset" @refresh="handleRefresh" @export="handleExport">
      <select class="select" v-model="usageStore.filterKey" style="max-width:200px">
        <option value="全部密钥">全部密钥</option>
        <option v-for="key in uniqueKeys" :key="key" :value="key">{{ key }}</option>
      </select>
      <select class="select" v-model="usageStore.dateRange" style="max-width:140px">
        <option v-for="opt in ['今天', '近 7 天', '近 30 天', '本月', '上月']" :key="opt" :value="opt">{{ opt }}</option>
      </select>
      <select class="select" v-model="usageStore.granularity" style="max-width:120px" @change="handleRefresh">
        <option value="按天">按天</option>
        <option value="按小时">按小时</option>
      </select>
    </BaseFilter>

    <!-- Table -->
    <div class="table-card card">
      <table class="table">
        <thead>
          <tr>
            <th>API密钥</th>
            <th>模型</th>
            <th>输入Token</th>
            <th>输出Token</th>
            <th>费用</th>
            <th>延迟</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="text-center p-8">
              <div class="loading-spinner" style="margin:0 auto"></div>
            </td>
          </tr>
          <tr v-else-if="fetchError">
            <td colspan="7" class="text-center p-8 text-danger">{{ fetchError }}</td>
          </tr>
          <tr v-else-if="filteredRecords.length === 0">
            <td colspan="7">
              <BaseEmpty
                icon="📋"
                title="暂无使用记录"
                desc="开始使用 API 后，您的使用历史将显示在这里"
              />
            </td>
          </tr>
          <tr v-for="r in filteredRecords" :key="r.id">
            <td><code class="key-code">Key-{{ r.api_key_id }}</code></td>
            <td>{{ r.model_name }}</td>
            <td>{{ r.input_tokens.toLocaleString() }}</td>
            <td>{{ r.output_tokens.toLocaleString() }}</td>
            <td>${{ r.cost.toFixed(4) }}</td>
            <td>{{ r.latency_ms }}ms</td>
            <td>{{ new Date(r.requested_at).toLocaleString('zh-CN') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import MainLayout from '@/components/main/MainLayout.vue'
import BaseFilter from '@/components/common/BaseFilter.vue'
import BaseEmpty from '@/components/common/BaseEmpty.vue'
import { useUsageStore } from '@/stores/usage'
import { useKeyStore } from '@/stores/keys'
import { useFeedbackStore } from '@/stores/feedback'

const usageStore = useUsageStore()
const keyStore = useKeyStore()
const feedback = useFeedbackStore()
const loading = ref(false)
const fetchError = ref<string | null>(null)

const uniqueKeys = computed(() => {
  const keys = new Set(usageStore.records.map((r: any) => r.model_name))
  return Array.from(keys)
})

const filteredRecords = computed(() => usageStore.records)

const stats = computed(() => {
  const recs = filteredRecords.value
  return {
    totalRequests: recs.length,
    totalTokens: recs.reduce((s: number, r: any) => s + r.total_tokens, 0),
    totalInput: recs.reduce((s: number, r: any) => s + r.input_tokens, 0),
    totalOutput: recs.reduce((s: number, r: any) => s + r.output_tokens, 0),
    totalCost: recs.reduce((s: number, r: any) => s + r.cost, 0).toFixed(4),
    avgLatency: recs.length ? Math.round(recs.reduce((s: number, r: any) => s + r.latency_ms, 0) / recs.length) + 'ms' : '0ms',
  }
})

const handleReset = async () => {
  usageStore.setFilterKey('全部密钥')
  usageStore.setDateRange('近 7 天')
  usageStore.setGranularity('按天')
  loading.value = true
  fetchError.value = null
  try {
    await usageStore.fetchUsage()
    feedback.info('已重置筛选条件')
  } catch (e: any) {
    fetchError.value = e.message || '重置失败'
  } finally {
    loading.value = false
  }
}

const handleRefresh = async () => {
  loading.value = true
  fetchError.value = null
  try {
    await usageStore.fetchUsage()
    feedback.info('使用记录已刷新')
  } catch (e: any) {
    fetchError.value = e.message || '刷新失败'
  } finally {
    loading.value = false
  }
}

const handleExport = () => {
  if (filteredRecords.value.length === 0) {
    feedback.warning('暂无数据可导出')
    return
  }
  const csv = [
    ['API密钥', '模型', '输入Token', '输出Token', '费用', '延迟', '时间'].join(','),
    ...filteredRecords.value.map((r: any) => [
      r.api_key_id, r.model_name, r.input_tokens, r.output_tokens,
      r.cost, r.latency_ms, r.requested_at,
    ].join(','))
  ].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'usage.csv'
  a.click()
  URL.revokeObjectURL(url)
  feedback.success('CSV 已导出')
}


onMounted(async () => {
  loading.value = true
  fetchError.value = null
  try {
    await Promise.all([keyStore.fetchKeys(), usageStore.fetchUsage()])
  } catch (e: any) {
    fetchError.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stats-grid-4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
}
.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 4px;
}
.stat-sub {
  font-size: 12px;
  color: var(--color-text-muted);
}
.table-card {
  overflow: hidden;
  padding: 0;
}
.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.text-center { text-align: center; }
.p-8 { padding: 32px 0; }
.text-danger { color: var(--color-danger); }
.key-code {
  font-family: monospace;
  font-size: 12px;
  background: var(--color-bg-secondary);
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
