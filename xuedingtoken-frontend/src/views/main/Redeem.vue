<template>
  <MainLayout title="兑换码" subtitle="输入兑换码以充值余额或增加并发数">
    <!-- Balance card -->
    <div class="balance-card card">
      <div class="balance-main">
        <div class="balance-label">当前余额</div>
        <div class="balance-value">${{ dashboardStore.data?.balance?.toFixed(2) ?? '-.--' }}</div>
      </div>
      <div class="balance-info">
        <span class="badge badge-primary">使用兑换码增加余额或并发数</span>
      </div>
    </div>

    <!-- Redeem form -->
    <div class="redeem-section card">
      <h3 class="section-h3">兑换码兑换</h3>
      <div class="redeem-form">
        <div class="redeem-input-wrap" :class="{ shake: shaking }">
          <span class="redeem-icon">🎁</span>
          <input
            class="input redeem-input"
            placeholder="请输入兑换码"
            v-model="code"
            @keydown.enter="handleRedeem"
          />
        </div>
        <p class="redeem-hint">兑换码区分大小写</p>
        <button
          class="btn btn-primary redeem-btn"
          :disabled="!code.trim() || loading"
          @click="handleRedeem"
        >
          <span v-if="loading" class="loading-dots">兑换中...</span>
          <span v-else>兑换</span>
        </button>
      </div>
    </div>

    <!-- About redeem codes -->
    <div class="about-section card">
      <h3 class="section-h3">关于兑换码</h3>
      <ul class="about-list">
        <li>每个兑换码只能使用一次</li>
        <li>兑换码可以增加余额、并发数或试用权限</li>
        <li>余额和并发数即时更新</li>
      </ul>
    </div>

    <!-- Recent activity -->
    <div class="activity-section">
      <h3 class="section-h3">兑换历史</h3>
      <div class="card" style="padding:0;overflow:hidden" v-if="redeemStore.history.length > 0">
        <table class="table">
          <thead>
            <tr>
              <th>兑换码</th>
              <th>状态</th>
              <th>金额</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(record, idx) in redeemStore.history" :key="idx">
              <td><code class="key-code">{{ record.code }}</code></td>
              <td>
                <span class="badge" :class="record.status === '成功' ? 'badge-success' : 'badge-danger'">
                  {{ record.status }}
                </span>
              </td>
              <td class="amount-cell">${{ record.balance_delta.toFixed(2) }}</td>
              <td class="time-cell">{{ new Date(record.created_at).toLocaleString('zh-CN') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="card">
        <BaseEmpty
          icon="📋"
          title="暂无活动记录"
          desc="您的兑换历史将显示在这里"
        />
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import MainLayout from '@/components/main/MainLayout.vue'
import BaseEmpty from '@/components/common/BaseEmpty.vue'
import { useRedeemStore } from '@/stores/redeem'
import { useDashboardStore } from '@/stores/dashboard'
import { useFeedbackStore } from '@/stores/feedback'

const redeemStore = useRedeemStore()
const dashboardStore = useDashboardStore()
const feedback = useFeedbackStore()
const code = ref('')
const loading = ref(false)
const shaking = ref(false)

const triggerShake = () => {
  shaking.value = true
  setTimeout(() => shaking.value = false, 600)
}

const handleRedeem = async () => {
  if (!code.value.trim()) {
    triggerShake()
    return
  }
  loading.value = true
  try {
    const result = await redeemStore.redeem(code.value.trim())
    if (result.success) {
      feedback.success(result.message)
      // Refresh dashboard to show new balance
      await dashboardStore.fetchDashboard()
    } else {
      feedback.error(result.message)
    }
  } catch (e: any) {
    feedback.error(e.message)
  } finally {
    loading.value = false
    code.value = ''
  }
}

onMounted(async () => {
  await Promise.all([
    redeemStore.fetchHistory(),
    dashboardStore.fetchDashboard(),
  ])
})
</script>

<style scoped>
.balance-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #1e1b4b, #111827);
  color: #fff;
  border: none;
  padding: 24px;
}
.balance-label {
  font-size: 14px;
  color: rgba(255,255,255,0.7);
  margin-bottom: 4px;
}
.balance-value {
  font-size: 36px;
  font-weight: 700;
  color: #fff;
}
.redeem-section, .about-section {
  margin-bottom: 24px;
}
.section-h3 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 16px;
  color: var(--color-text);
}
.redeem-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.redeem-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.redeem-icon {
  position: absolute;
  left: 14px;
  font-size: 20px;
}
.redeem-input {
  padding-left: 48px;
  height: 44px;
  font-size: 14px;
}
.redeem-hint {
  font-size: 13px;
  color: var(--color-text-secondary);
}
.redeem-btn {
  align-self: flex-start;
  min-width: 120px;
  height: 44px;
  padding: 0 24px;
}
.redeem-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.about-list {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.about-list li {
  font-size: 14px;
  color: var(--color-text-secondary);
  position: relative;
  border-left: 4px solid var(--color-primary);
  padding-left: 12px;
  line-height: 1.5;
}
.activity-section {
  margin-top: 8px;
}
.key-code {
  font-family: monospace;
  font-size: 12px;
  background: var(--color-bg-secondary);
  padding: 2px 6px;
  border-radius: 4px;
}
.amount-cell {
  font-weight: 700;
  color: var(--color-text);
}
.time-cell {
  font-size: 12px;
  color: var(--color-text-muted);
}

/* Shake animation */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-6px); }
  20%, 40%, 60%, 80% { transform: translateX(6px); }
}
.shake {
  animation: shake 0.6s ease-in-out;
}
.shake .redeem-input {
  border-color: var(--color-danger);
}

.loading-dots {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
</style>
