<template>
  <MainLayout title="仪表盘" subtitle="欢迎回来！这是您账户的概览">
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">账户余额</div>
        <div class="stat-value">{{ dashboardStore.data?.balance != null ? '$' + dashboardStore.data.balance.toFixed(2) : '-' }}</div>
        <div class="stat-sub">可用</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">可用余额</div>
        <div class="stat-value">{{ dashboardStore.data?.available_balance != null ? '$' + dashboardStore.data.available_balance.toFixed(2) : '-' }}</div>
        <div class="stat-sub">可用</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">API 密钥</div>
        <div class="stat-value">{{ dashboardStore.data?.api_key_count ?? '-' }}</div>
        <div class="stat-sub">{{ keyStore.keys.filter((k: any) => k.status === 'active').length }} 启用</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">今日请求</div>
        <div class="stat-value">{{ dashboardStore.data?.today_requests ?? '-' }}</div>
        <div class="stat-sub">总计: {{ dashboardStore.data?.total_tokens?.toLocaleString() ?? '-' }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">今日消费</div>
        <div class="stat-value">${{ dashboardStore.data?.today_cost?.toFixed(4) ?? '-' }}</div>
        <div class="stat-sub">总计: ${{ dashboardStore.data?.total_tokens ?? '-' }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">今日 Token</div>
        <div class="stat-value">{{ dashboardStore.data?.today_tokens?.toLocaleString() ?? '-' }}</div>
        <div class="stat-sub">RPM: {{ dashboardStore.data?.rpm ?? '-' }} / TPM: {{ dashboardStore.data?.tpm ?? '-' }}</div>
      </div>
    </div>

    <div class="perf-section">
      <div class="perf-metrics">
        <div class="perf-item">
          <span class="perf-label">RPM</span>
          <span class="perf-value">{{ dashboardStore.data?.rpm ?? '-' }}</span>
        </div>
        <div class="perf-item">
          <span class="perf-label">TPM</span>
          <span class="perf-value">{{ dashboardStore.data?.tpm ?? '-' }}</span>
        </div>
        <div class="perf-item">
          <span class="perf-label">平均响应</span>
          <span class="perf-value">{{ dashboardStore.data?.avg_latency_ms ? dashboardStore.data.avg_latency_ms + 'ms' : '-' }}</span>
        </div>
        <div class="perf-item">
          <span class="perf-label">累计 Token</span>
          <span class="perf-value">{{ dashboardStore.data?.total_tokens?.toLocaleString() ?? '-' }}</span>
        </div>
      </div>
      <div class="perf-controls">
        <select class="select" style="width:auto;min-width:160px" :value="usageStore.dateRange" @change="usageStore.setDateRange(($event.target as HTMLSelectElement).value)">
          <option v-for="opt in ['今天', '近 7 天', '近 30 天', '本月', '上月']" :key="opt">{{ opt }}</option>
        </select>
        <select class="select" style="width:auto;min-width:100px" :value="usageStore.granularity" @change="usageStore.setGranularity(($event.target as HTMLSelectElement).value)">
          <option>按天</option>
          <option>按小时</option>
        </select>
      </div>
    </div>

    <div class="charts-grid">
      <div class="chart-card card">
        <h3 class="chart-title">请求量趋势（近7天）</h3>
        <div class="chart-canvas-wrap">
          <canvas v-if="hasRequestChartData" ref="chartCanvas"></canvas>
          <div v-else class="chart-empty">
            <div class="chart-empty-icon">📈</div>
            <p>暂无数据</p>
            <p class="text-sm text-muted">开始使用 API 后，请求量趋势会显示在这里</p>
          </div>
        </div>
      </div>
      <div class="chart-card card">
        <h3 class="chart-title">Token 使用趋势（近7天）</h3>
        <div class="chart-canvas-wrap">
          <canvas v-if="hasTokenChartData" ref="tokenChartCanvas"></canvas>
          <div v-else class="chart-empty">
            <div class="chart-empty-icon">📊</div>
            <p>暂无数据</p>
            <p class="text-sm text-muted">开始使用 API 后，Token 趋势会显示在这里</p>
          </div>
        </div>
      </div>
    </div>

    <div class="recent-section">
      <h3 class="section-h3">近7天</h3>
      <div class="card">
        <table class="table" v-if="recentRecords.length > 0">
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
            <tr v-for="r in recentRecords" :key="r.id">
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
        <BaseEmpty
          v-else
          icon="📋"
          title="暂无使用记录"
          desc="开始使用API后，您的使用历史将显示在这里"
        />
      </div>
    </div>

    <div class="quick-actions">
      <div class="action-card card" @click="$router.push('/main/keys')">
        <div class="action-icon">🔑</div>
        <h4>创建 API 密钥</h4>
        <p>生成新的 API 密钥</p>
        <button class="btn btn-primary btn-sm mt-4">创建密钥</button>
      </div>
      <div class="action-card card" @click="$router.push('/main/usage')">
        <div class="action-icon">📋</div>
        <h4>查看使用记录</h4>
        <p>查看详细的使用日志</p>
        <button class="btn btn-outline btn-sm mt-4">查看记录</button>
      </div>
      <div class="action-card card" @click="$router.push('/main/redeem')">
        <div class="action-icon">🎁</div>
        <h4>兑换码</h4>
        <p>使用兑换码充值</p>
        <button class="btn btn-outline btn-sm mt-4">立即兑换</button>
      </div>
    </div>

    <div v-if="loading" class="page-loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="error" class="page-error card">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
      <button class="btn btn-outline btn-sm mt-4" @click="reloadAll">重试</button>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import MainLayout from '@/components/main/MainLayout.vue'
import BaseEmpty from '@/components/common/BaseEmpty.vue'
import { useKeyStore } from '@/stores/keys'
import { useUsageStore } from '@/stores/usage'
import { useDashboardStore } from '@/stores/dashboard'
import { Chart } from '@/utils/chart'

const keyStore = useKeyStore()
const usageStore = useUsageStore()
const dashboardStore = useDashboardStore()
const loading = ref(true)
const error = ref<string | null>(null)

const chartCanvas = ref<HTMLCanvasElement | null>(null)
const tokenChartCanvas = ref<HTMLCanvasElement | null>(null)

let requestChart: any = null
let tokenChart: any = null

const recentRecords = computed(() => usageStore.records.slice(0, 5))

const chartLabels = computed(() => {
  const days: string[] = []
  const now = new Date()
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    const s = d.toISOString().slice(0, 10)
    const m = s.match(/(\d{4})-(\d{2})-(\d{2})/)
    days.push(m ? `${parseInt(m[2])}月${parseInt(m[3])}日` : s)
  }
  return days
})

const groupedByDate = computed(() => {
  const map = new Map<string, { requests: number; tokens: number }>()
  for (const record of usageStore.records) {
    const date = record.requested_at.slice(0, 10)
    const existing = map.get(date) || { requests: 0, tokens: 0 }
    existing.requests += 1
    existing.tokens += record.total_tokens
    map.set(date, existing)
  }
  return map
})

const requestData = computed(() => {
  const now = new Date()
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(now)
    d.setDate(d.getDate() - (6 - i))
    const s = d.toISOString().slice(0, 10)
    return groupedByDate.value.get(s)?.requests ?? 0
  })
})

const tokenData = computed(() => {
  const now = new Date()
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(now)
    d.setDate(d.getDate() - (6 - i))
    const s = d.toISOString().slice(0, 10)
    return groupedByDate.value.get(s)?.tokens ?? 0
  })
})

const hasRequestChartData = computed(() => requestData.value.some(value => value > 0))
const hasTokenChartData = computed(() => tokenData.value.some(value => value > 0))

const chartOptions = () => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1e1b4b',
      titleColor: '#e2e8f0',
      bodyColor: '#e2e8f0',
      padding: 12,
      cornerRadius: 8,
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { color: '#9CA3AF', font: { size: 11 } },
      border: { display: false },
    },
    y: {
      grid: { color: '#F3F4F6' },
      ticks: { color: '#9CA3AF', font: { size: 11 } },
      border: { display: false },
      beginAtZero: true,
    },
  },
  elements: {
    line: { tension: 0.4 },
    point: { radius: 3, hoverRadius: 5 },
  },
})

const destroyRequestChart = () => {
  requestChart?.destroy()
  requestChart = null
}

const destroyTokenChart = () => {
  tokenChart?.destroy()
  tokenChart = null
}

const waitForDomUpdate = () => new Promise<void>(resolve => setTimeout(resolve, 0))

const rebuildRequestChart = async () => {
  destroyRequestChart()
  if (!hasRequestChartData.value) return
  await waitForDomUpdate()
  if (!chartCanvas.value) return
  requestChart = new Chart(chartCanvas.value, {
    type: 'line',
    data: {
      labels: chartLabels.value,
      datasets: [{
        label: '请求量',
        data: requestData.value,
        borderColor: '#4F46E5',
        backgroundColor: 'rgba(79,70,229,0.1)',
        fill: true,
      }],
    },
    options: chartOptions() as any,
  })
}

const rebuildTokenChart = async () => {
  destroyTokenChart()
  if (!hasTokenChartData.value) return
  await waitForDomUpdate()
  if (!tokenChartCanvas.value) return
  tokenChart = new Chart(tokenChartCanvas.value, {
    type: 'line',
    data: {
      labels: chartLabels.value,
      datasets: [{
        label: 'Token',
        data: tokenData.value,
        borderColor: '#10B981',
        backgroundColor: 'rgba(16,185,129,0.1)',
        fill: true,
      }],
    },
    options: chartOptions() as any,
  })
}

const reloadAll = async () => {
  loading.value = true
  error.value = null
  try {
    await Promise.all([
      keyStore.fetchKeys(),
      dashboardStore.fetchDashboard(),
      usageStore.fetchUsage(),
    ])
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

watch([chartLabels, requestData, hasRequestChartData], rebuildRequestChart, { flush: 'post' })
watch([chartLabels, tokenData, hasTokenChartData], rebuildTokenChart, { flush: 'post' })

onMounted(async () => {
  await reloadAll()
})

onUnmounted(() => {
  destroyRequestChart()
  destroyTokenChart()
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.perf-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  margin-bottom: 24px;
}
.perf-metrics {
  display: flex;
  gap: 20px;
}
.perf-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.perf-label {
  font-size: 11px;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.perf-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text);
}
.perf-controls {
  display: flex;
  gap: 12px;
}
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}
.chart-card {
  min-height: 320px;
  position: relative;
}
.chart-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--color-text);
}
.chart-canvas-wrap {
  position: relative;
  height: 240px;
}
.chart-empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.chart-empty-icon {
  font-size: 48px;
  opacity: .4;
  margin-bottom: 12px;
}
.chart-empty p {
  font-size: 14px;
  color: var(--color-text-secondary);
}
canvas {
  display: block;
  width: 100%;
  height: 100% !important;
}
.recent-section {
  margin-bottom: 24px;
}
.section-h3 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--color-text);
}
.quick-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}
.action-card {
  cursor: pointer;
  transition: all 0.2s;
}
.action-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}
.action-icon {
  font-size: 28px;
  margin-bottom: 10px;
}
.action-card h4 {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 6px;
  color: var(--color-text);
}
.action-card p {
  font-size: 13px;
  color: var(--color-text-secondary);
}
.page-loading {
  text-align: center;
  padding: 64px 0;
  color: var(--color-text-secondary);
}
.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }
.page-error {
  text-align: center;
  padding: 64px 0;
}
.error-icon { font-size: 48px; opacity: 0.5; margin-bottom: 12px; }
.key-code {
  font-family: monospace;
  font-size: 12px;
  background: var(--color-bg-secondary);
  padding: 2px 6px;
  border-radius: 4px;
}

@media (max-width: 900px) {
  .stats-grid,
  .charts-grid,
  .quick-actions {
    grid-template-columns: 1fr;
  }
  .perf-section,
  .perf-metrics,
  .perf-controls {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 640px) {
  .chart-card {
    min-height: 280px;
  }
  .chart-canvas-wrap {
    height: 220px;
  }
  .recent-section .table {
    min-width: 720px;
  }
}
</style>
