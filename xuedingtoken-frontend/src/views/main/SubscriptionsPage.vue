<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">📦 我的订阅</h1>
      <button class="btn-outline-sm" @click="fetchAll">🔄 刷新</button>
    </div>

    <!-- 活跃订阅 -->
    <div v-if="activeSub" class="active-sub-card">
      <div class="sub-header">
        <div class="sub-plan">{{ activeSub.plan_name }}</div>
        <span :class="['badge', 'badge-success']">生效中</span>
      </div>
      <div class="sub-meta">
        <div class="sub-meta-item">
          <span class="sub-meta-label">生效时间</span>
          <span class="sub-meta-value">{{ fmtDate(activeSub.starts_at) }}</span>
        </div>
        <div class="sub-meta-item">
          <span class="sub-meta-label">到期时间</span>
          <span class="sub-meta-value">{{ fmtDate(activeSub.expires_at) }}</span>
        </div>
      </div>
      <div class="sub-days-left" v-if="daysLeft >= 0">
        剩余 <strong>{{ daysLeft }}</strong> 天
      </div>
    </div>
    <div v-else-if="!loading" class="empty-state-card">
      <div class="empty-icon">📦</div>
      <div class="empty-text">暂无生效中的订阅</div>
      <router-link to="/products" class="btn-buy-small">前往商品中心</router-link>
    </div>

    <!-- 历史订阅列表 -->
    <div v-if="allSubs.length > 0" class="section-title" style="margin-top:32px">📋 历史订阅</div>
    <div v-if="allSubs.length > 0" class="sub-list">
      <div v-for="s in allSubs" :key="s.id" class="sub-row">
        <div class="sub-row-info">
          <span class="sub-row-name">{{ s.plan_name }}</span>
          <span :class="['badge', s.status === 'active' ? 'badge-success' : 'badge-default']">{{ s.status === 'active' ? '生效中' : s.status }}</span>
        </div>
        <div class="sub-row-date">{{ fmtDate(s.expires_at) }} 到期</div>
      </div>
    </div>

    <!-- Token 配额 -->
    <div v-if="tokenGrants.length > 0" class="section-title" style="margin-top:32px">⚡ Token 配额</div>
    <div v-if="tokenGrants.length > 0" class="quota-list">
      <div v-for="g in tokenGrants" :key="g.id" class="quota-card">
        <div class="quota-name">{{ g.product_id ? '套餐配额 #' + g.product_id : '配额' }}</div>
        <div class="quota-bar">
          <div class="quota-used" :style="{ width: Math.min(100, (g.used / g.quota * 100)) + '%' }"></div>
        </div>
        <div class="quota-label">{{ g.used.toLocaleString() }} / {{ g.quota.toLocaleString() }} tokens</div>
        <div class="quota-status">
          <span :class="['badge', g.status === 'active' ? 'badge-success' : 'badge-default']">{{ g.status }}</span>
        </div>
      </div>
    </div>

    <div class="subscription-notice">
      <p>💡 订阅权益模块正在持续完善中，更多功能即将上线。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { subscriptionsApi } from '@/api/subscriptions'

const allSubs = ref<any[]>([])
const activeSub = ref<any | null>(null)
const tokenGrants = ref<any[]>([])
const loading = ref(true)

const fetchAll = async () => {
  loading.value = true
  try {
    const [subs, active, grants] = await Promise.all([
      subscriptionsApi.list(),
      subscriptionsApi.active().catch(() => null),
      subscriptionsApi.tokenGrants().catch(() => []),
    ])
    allSubs.value = subs || []
    activeSub.value = active || null
    tokenGrants.value = grants || []
  } finally {
    loading.value = false
  }
}

const daysLeft = computed(() => {
  if (!activeSub.value?.expires_at) return -1
  const now = Date.now()
  const exp = new Date(activeSub.value.expires_at).getTime()
  return Math.max(0, Math.ceil((exp - now) / 86400000))
})

const fmtDate = (d: string) => d ? new Date(d).toLocaleString('zh-CN', { month:'2-digit', day:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' }) : '—'

onMounted(fetchAll)
</script>

<style scoped>
.page-container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
.page-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:24px; }
.page-title { font-size:24px; font-weight:700; color:#1a1a2e; }
.active-sub-card { background:linear-gradient(135deg,#aa3bff,#7c5bf5); color:#fff; border-radius:14px; padding:24px; margin-bottom:20px; }
.sub-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.sub-plan { font-size:20px; font-weight:700; }
.badge { font-size:11px; padding:2px 10px; border-radius:10px; font-weight:600; }
.badge-success { background:rgba(255,255,255,0.25); color:#fff; }
.badge-default { background:rgba(255,255,255,0.15); color:rgba(255,255,255,0.7); }
.sub-meta { display:flex; gap:32px; margin-bottom:12px; }
.sub-meta-item { display:flex; flex-direction:column; gap:2px; }
.sub-meta-label { font-size:11px; opacity:0.8; }
.sub-meta-value { font-size:14px; font-weight:600; }
.sub-days-left { font-size:13px; opacity:0.9; }
.empty-state-card { background:#fff; border:1px solid #f0f0f0; border-radius:14px; padding:40px; text-align:center; margin-bottom:20px; }
.empty-icon { font-size:48px; margin-bottom:12px; }
.empty-text { font-size:15px; color:#888; margin-bottom:20px; }
.btn-buy-small { display:inline-block; background:#aa3bff; color:#fff; text-decoration:none; padding:8px 20px; border-radius:8px; font-size:13px; }
.section-title { font-size:16px; font-weight:700; color:#1a1a2e; margin-bottom:12px; }
.sub-list { display:flex; flex-direction:column; gap:10px; margin-bottom:20px; }
.sub-row { background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:14px 16px; display:flex; justify-content:space-between; align-items:center; }
.sub-row-info { display:flex; align-items:center; gap:10px; }
.sub-row-name { font-size:14px; font-weight:600; color:#1a1a2e; }
.sub-row-date { font-size:12px; color:#999; }
.quota-list { display:flex; flex-direction:column; gap:12px; margin-bottom:20px; }
.quota-card { background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:16px; }
.quota-name { font-size:14px; font-weight:600; color:#1a1a2e; margin-bottom:10px; }
.quota-bar { height:8px; background:#f0f0f0; border-radius:4px; overflow:hidden; margin-bottom:6px; }
.quota-used { height:100%; background:linear-gradient(90deg,#aa3bff,#7c5bf5); border-radius:4px; }
.quota-label { font-size:12px; color:#666; margin-bottom:8px; }
.subscription-notice { background:#fafafa; border:1px solid #f0f0f0; border-radius:10px; padding:16px 20px; text-align:center; margin-top:24px; }
.subscription-notice p { font-size:13px; color:#888; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
</style>
