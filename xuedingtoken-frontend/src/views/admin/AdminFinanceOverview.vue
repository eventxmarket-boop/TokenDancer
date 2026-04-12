<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">财务总览</h1>
      <button class="btn-outline-sm" @click="fetchOverview">🔄 刷新</button>
    </div>

    <!-- KPI 卡片 -->
    <div v-if="loading" class="kpi-loading">加载中…</div>
    <div v-else-if="error" class="kpi-error">
      <span class="td-error">{{ error }}</span>
      <button class="btn-outline-sm" @click="fetchOverview">重试</button>
    </div>
    <div v-else class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">注册用户数</div>
        <div class="kpi-value">{{ overview.user_count ?? 0 }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">平台总余额</div>
        <div class="kpi-value kpi-money">¥{{ (overview.total_balance ?? 0).toFixed(4) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">账本记录数</div>
        <div class="kpi-value">{{ overview.ledger_count ?? 0 }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Usage 记录数</div>
        <div class="kpi-value">{{ overview.usage_count ?? 0 }}</div>
      </div>
    </div>

    <!-- 最近账本变动 -->
    <div class="section-gap">
      <div class="section-header">
        <h2 class="section-title">最近账本变动</h2>
        <router-link to="/admin/finance/ledger" class="link-more">查看更多 →</router-link>
      </div>

      <AdminSectionCard>
        <div class="table-wrap">
          <table class="admin-table">
            <thead><tr>
              <th>ID</th><th>用户</th><th>类型</th><th>金额</th><th>变动前</th><th>变动后</th><th>时间</th>
            </tr></thead>
            <tbody>
              <tr v-if="ledgerLoading"><td colspan="7" class="td-center td-pad">加载中…</td></tr>
              <tr v-else-if="ledgerError"><td colspan="7" class="td-center td-pad td-error">{{ ledgerError }}</td></tr>
              <tr v-else-if="!recentLedger.length"><td colspan="7" class="td-center td-pad">暂无记录</td></tr>
              <tr v-else v-for="r in recentLedger" :key="r.id" class="tr-body">
                <td>{{ r.id }}</td>
                <td>{{ r.user_email || '用户#' + r.user_id }}</td>
                <td><span class="op-badge" :class="'op-' + r.operation">{{ r.operation }}</span></td>
                <td :class="r.amount >= 0 ? 'td-positive' : 'td-negative'">
                  {{ r.amount >= 0 ? '+' : '' }}{{ r.amount.toFixed(4) }}
                </td>
                <td>{{ r.balance_before.toFixed(4) }}</td>
                <td>{{ r.balance_after.toFixed(4) }}</td>
                <td>{{ fmtDate(r.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </AdminSectionCard>
    </div>

    <!-- 最近 Usage -->
    <div class="section-gap">
      <div class="section-header">
        <h2 class="section-title">最近 Usage</h2>
        <router-link to="/admin/finance/usage" class="link-more">查看更多 →</router-link>
      </div>

      <AdminSectionCard>
        <div class="table-wrap">
          <table class="admin-table">
            <thead><tr>
              <th>ID</th><th>用户</th><th>模型</th><th>输入</th><th>输出</th><th>总计</th><th>费用</th><th>延迟ms</th><th>时间</th>
            </tr></thead>
            <tbody>
              <tr v-if="usageLoading"><td colspan="9" class="td-center td-pad">加载中…</td></tr>
              <tr v-else-if="usageError"><td colspan="9" class="td-center td-pad td-error">{{ usageError }}</td></tr>
              <tr v-else-if="!recentUsage.length"><td colspan="9" class="td-center td-pad">暂无记录</td></tr>
              <tr v-else v-for="r in recentUsage" :key="r.id" class="tr-body">
                <td>{{ r.id }}</td>
                <td>用户#{{ r.user_id }}</td>
                <td><code class="model-name">{{ r.model_name }}</code></td>
                <td>{{ r.input_tokens }}</td>
                <td>{{ r.output_tokens }}</td>
                <td>{{ r.total_tokens }}</td>
                <td class="td-money">${{ r.cost.toFixed(6) }}</td>
                <td>{{ r.latency_ms }}ms</td>
                <td>{{ fmtDate(r.requested_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </AdminSectionCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminFinanceApi } from '@/api/adminFinance'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'

const overview = ref<any>({})
const loading = ref(false)
const error = ref('')

const recentLedger = ref<any[]>([])
const ledgerLoading = ref(false)
const ledgerError = ref('')

const recentUsage = ref<any[]>([])
const usageLoading = ref(false)
const usageError = ref('')

function fmtDate(v: string) {
  if (!v) return '—'
  return new Date(v).toLocaleString('zh-CN')
}

async function fetchOverview() {
  loading.value = true
  error.value = ''
  try {
    const res = await adminFinanceApi.overview()
    overview.value = res || {}
  } catch (e: any) {
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function fetchRecentLedger() {
  ledgerLoading.value = true
  ledgerError.value = ''
  try {
    const res = await adminFinanceApi.ledger({ limit: 10, offset: 0 })
    recentLedger.value = res?.records || []
  } catch (e: any) {
    ledgerError.value = e?.message || '加载失败'
  } finally {
    ledgerLoading.value = false
  }
}

async function fetchRecentUsage() {
  usageLoading.value = true
  usageError.value = ''
  try {
    const res = await adminFinanceApi.usage({ limit: 10, offset: 0 })
    recentUsage.value = res?.records || []
  } catch (e: any) {
    usageError.value = e?.message || '加载失败'
  } finally {
    usageLoading.value = false
  }
}

onMounted(() => {
  fetchOverview()
  fetchRecentLedger()
  fetchRecentUsage()
})
</script>

<style scoped>
.kpi-loading, .kpi-error {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px;
  color: #666;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}
.kpi-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.kpi-label {
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
  font-weight: 500;
}
.kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: #222;
}
.kpi-money { color: #1677ff; }
.section-gap { margin-top: 28px; }
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #222;
  margin: 0;
}
.link-more {
  font-size: 13px;
  color: #1677ff;
  text-decoration: none;
}
.link-more:hover { text-decoration: underline; }
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
.op-default { background: #f5f5f5; color: #666; }
.td-positive { color: #52c41a; }
.td-negative { color: #ff4d4f; }
.model-name {
  font-size: 12px;
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
}
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
</style>
