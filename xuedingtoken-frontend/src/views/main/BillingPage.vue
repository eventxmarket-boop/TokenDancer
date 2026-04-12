<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">💳 账户充值</h1>
      <button class="btn-outline-sm" @click="fetchAll">🔄 刷新</button>
    </div>

    <div class="balance-grid">
      <div class="balance-card">
        <div class="balance-info">
          <div class="balance-label">账户余额</div>
          <div class="balance-amount">¥{{ summary.balance?.toFixed(2) ?? '—' }}</div>
          <div class="balance-sub" v-if="summary.available_balance !== undefined">
            可用余额 ¥{{ summary.available_balance?.toFixed(2) }}
          </div>
        </div>
        <router-link to="/products" class="btn-buy">前往充值</router-link>
      </div>

      <div class="token-summary-card">
        <div class="token-summary-title">Token Grant 概览</div>
        <div class="token-summary-grid">
          <div class="token-summary-item">
            <span class="token-summary-label">活跃配额</span>
            <strong class="token-summary-value">{{ activeGrantCount }}</strong>
          </div>
          <div class="token-summary-item">
            <span class="token-summary-label">剩余 Token</span>
            <strong class="token-summary-value">{{ remainingGrantTokens.toLocaleString() }}</strong>
          </div>
          <div class="token-summary-item">
            <span class="token-summary-label">即将到期</span>
            <strong class="token-summary-value">{{ expiringSoonGrantCount }}</strong>
          </div>
        </div>
      </div>
    </div>

    <div class="section-title">💡 充值方式</div>
    <div class="billing-options">
      <div class="billing-card">
        <div class="billing-icon">🛒</div>
        <div class="billing-title">商城充值</div>
        <div class="billing-desc">前往商品中心购买 Token 套餐</div>
        <router-link to="/products" class="billing-btn">立即购买</router-link>
      </div>
      <div class="billing-card">
        <div class="billing-icon">🎫</div>
        <div class="billing-title">兑换码</div>
        <div class="billing-desc">使用兑换码充值，直接到账</div>
        <router-link to="/main/redeem" class="billing-btn">兑换码充值</router-link>
      </div>
    </div>

    <div class="section-title">📦 Token Grant</div>
    <div v-if="loading" class="state-msg">加载中…</div>
    <div v-else-if="tokenGrants.length === 0" class="state-msg">暂无 Token Grant</div>
    <div v-else class="grant-list">
      <div v-for="grant in tokenGrants" :key="grant.id" class="grant-card">
        <div class="grant-top">
          <div>
            <div class="grant-title">Grant #{{ grant.id }}</div>
            <div class="grant-meta">来源订单：{{ grant.source_order_id || '—' }}</div>
          </div>
          <span :class="['grant-status', `grant-${grant.status}`]">{{ grant.status }}</span>
        </div>
        <div class="grant-progress-row">
          <div class="grant-progress-bar">
            <div class="grant-progress-fill" :style="{ width: grantUsagePercent(grant) + '%' }"></div>
          </div>
          <span class="grant-progress-text">{{ grant.used.toLocaleString() }} / {{ grant.quota.toLocaleString() }}</span>
        </div>
        <div class="grant-bottom">
          <span>剩余 {{ grantRemaining(grant).toLocaleString() }} tokens</span>
          <span>{{ grant.expires_at ? `到期：${fmtDate(grant.expires_at)}` : '永久有效' }}</span>
        </div>
      </div>
    </div>

    <div class="section-title">📋 账户流水</div>
    <div v-if="loading" class="state-msg">加载中…</div>
    <div v-else-if="ledger.length === 0" class="state-msg">暂无流水记录</div>
    <div v-else class="ledger-list">
      <div v-for="entry in ledger" :key="entry.id" class="ledger-row">
        <div class="ledger-left">
          <span class="ledger-type-icon">{{ typeIcon(entry.operation || entry.type) }}</span>
          <div class="ledger-info">
            <span class="ledger-type">{{ typeLabel(entry.operation || entry.type) }}</span>
            <span class="ledger-remark">{{ entry.remark || '—' }}</span>
          </div>
        </div>
        <div class="ledger-right">
          <span :class="['ledger-amount', entry.amount >= 0 ? 'amount-pos' : 'amount-neg']">
            {{ entry.amount >= 0 ? '+' : '' }}{{ entry.amount.toFixed(2) }}
          </span>
          <span class="ledger-date">{{ fmtDate(entry.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { billingApi, subscriptionsApi } from '@/api/subscriptions'

const summary = ref<any>({})
const ledger = ref<any[]>([])
const tokenGrants = ref<any[]>([])
const loading = ref(true)

const activeGrantCount = computed(() => tokenGrants.value.filter(item => item.status === 'active').length)
const remainingGrantTokens = computed(() => tokenGrants.value.reduce((sum, item) => sum + grantRemaining(item), 0))
const expiringSoonGrantCount = computed(() => tokenGrants.value.filter(item => {
  if (!item.expires_at || item.status !== 'active') return false
  return new Date(item.expires_at).getTime() - Date.now() <= 7 * 24 * 3600 * 1000
}).length)

const fetchAll = async () => {
  loading.value = true
  try {
    const [summaryData, ledgerData, grants] = await Promise.all([
      billingApi.summary().catch(() => ({})),
      billingApi.ledger().catch(() => []),
      subscriptionsApi.tokenGrants().catch(() => []),
    ])
    summary.value = summaryData
    ledger.value = ledgerData
    tokenGrants.value = grants
  } finally {
    loading.value = false
  }
}

const grantRemaining = (grant: any) => Math.max(0, Number(grant.quota || 0) - Number(grant.used || 0))
const grantUsagePercent = (grant: any) => {
  const quota = Number(grant.quota || 0)
  if (!quota) return 0
  return Math.min(100, Math.round((Number(grant.used || 0) / quota) * 100))
}

const typeIcon = (type: string) => ({
  redeem_credit: '🎁',
  usage_debit: '📉',
  order_credit: '🛒',
  manual_adjust: '✏️',
  subscription_grant: '📦',
}[type] || '💰')

const typeLabel = (type: string) => ({
  redeem_credit: '兑换充值',
  usage_debit: '消费扣费',
  order_credit: '订单充值',
  manual_adjust: '手动调整',
  subscription_grant: '订阅赠送',
}[type] || type)

const fmtDate = (value: string) => value ? new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'

onMounted(fetchAll)
</script>

<style scoped>
.page-container { max-width: 960px; margin: 0 auto; padding: 40px 20px; }
.page-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; }
.page-title { font-size:24px; font-weight:700; color:#1a1a2e; }
.balance-grid { display:grid; grid-template-columns:1.3fr 1fr; gap:16px; margin-bottom:32px; }
.balance-card { background:linear-gradient(135deg,#1f7a5c,#2f9e6f); color:#fff; border-radius:14px; padding:24px; display:flex; align-items:center; justify-content:space-between; }
.balance-label { font-size:14px; opacity:0.9; margin-bottom:4px; }
.balance-amount { font-size:36px; font-weight:700; }
.balance-sub { font-size:13px; opacity:0.82; margin-top:4px; }
.btn-buy { background:rgba(255,255,255,0.16); color:#fff; border:1px solid rgba(255,255,255,0.3); padding:8px 20px; border-radius:8px; text-decoration:none; font-size:14px; }
.token-summary-card { background:#fff; border:1px solid #eef1f4; border-radius:14px; padding:22px; }
.token-summary-title { font-size:14px; font-weight:700; color:#1a1a2e; margin-bottom:14px; }
.token-summary-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; }
.token-summary-item { padding:12px; background:#f8fafc; border-radius:10px; }
.token-summary-label { display:block; font-size:12px; color:#6b7280; margin-bottom:6px; }
.token-summary-value { font-size:18px; color:#111827; }
.section-title { font-size:16px; font-weight:700; color:#1a1a2e; margin-bottom:16px; }
.billing-options { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:32px; }
.billing-card { background:#fff; border:1px solid #f0f0f0; border-radius:12px; padding:20px; text-align:center; }
.billing-icon { font-size:32px; margin-bottom:12px; }
.billing-title { font-size:15px; font-weight:700; color:#1a1a2e; margin-bottom:6px; }
.billing-desc { font-size:12px; color:#888; margin-bottom:16px; }
.billing-btn { display:inline-block; background:#1f7a5c; color:#fff; border:none; padding:8px 20px; border-radius:8px; text-decoration:none; font-size:13px; }
.state-msg { text-align:center; padding:40px; color:#888; }
.grant-list { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:32px; }
.grant-card { background:#fff; border:1px solid #eef1f4; border-radius:12px; padding:16px; }
.grant-top, .grant-bottom { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.grant-title { font-size:15px; font-weight:700; color:#1a1a2e; }
.grant-meta { font-size:12px; color:#6b7280; margin-top:4px; }
.grant-status { font-size:11px; font-weight:700; padding:3px 8px; border-radius:999px; text-transform:uppercase; }
.grant-active { background:#ecfdf3; color:#047857; }
.grant-exhausted { background:#fff1f2; color:#be123c; }
.grant-progress-row { display:flex; align-items:center; gap:10px; margin:14px 0 10px; }
.grant-progress-bar { flex:1; height:8px; background:#eef2f7; border-radius:999px; overflow:hidden; }
.grant-progress-fill { height:100%; background:linear-gradient(90deg,#1f7a5c,#4cc38a); }
.grant-progress-text { font-size:12px; color:#6b7280; white-space:nowrap; }
.grant-bottom { font-size:12px; color:#6b7280; }
.ledger-list { display:flex; flex-direction:column; gap:10px; }
.ledger-row { background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:14px 16px; display:flex; justify-content:space-between; align-items:center; }
.ledger-left { display:flex; align-items:center; gap:12px; }
.ledger-type-icon { font-size:20px; }
.ledger-info { display:flex; flex-direction:column; }
.ledger-type { font-size:13px; font-weight:600; color:#1a1a2e; }
.ledger-remark { font-size:11px; color:#999; margin-top:2px; }
.ledger-right { text-align:right; }
.ledger-amount { font-size:14px; font-weight:700; display:block; }
.amount-pos { color:#52c41a; }
.amount-neg { color:#ff4d4f; }
.ledger-date { font-size:11px; color:#bbb; display:block; margin-top:2px; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }

@media (max-width: 900px) {
  .balance-grid,
  .billing-options,
  .grant-list,
  .token-summary-grid {
    grid-template-columns:1fr;
  }
}

@media (max-width: 640px) {
  .page-container {
    padding: 24px 14px;
  }
  .page-title-row,
  .balance-card,
  .grant-top,
  .grant-bottom,
  .ledger-row {
    flex-direction: column;
    align-items: flex-start;
  }
  .balance-card {
    padding: 18px;
  }
  .balance-amount {
    font-size: 30px;
  }
  .btn-buy,
  .btn-outline-sm,
  .billing-btn {
    width: 100%;
    text-align: center;
  }
}
</style>
