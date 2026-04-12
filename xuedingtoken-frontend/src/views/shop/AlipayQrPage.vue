<template>
  <div class="alipay-qr-page">
    <ShopNav />
    <div class="qr-wrapper">
      <div v-if="loading">加载中...</div>
      <div v-else-if="error" class="status-panel error">{{ error }}</div>
      <div v-else class="qr-card">
        <h2>{{ cfg.alipay_display_name }}</h2>
        <p class="order-id">订单号：{{ orderId }}</p>
        <p class="amount">应付金额：<strong>¥{{ orderAmount }}</strong></p>
        <div class="qr-container">
          <img
            :src="cfg.alipay_qr_image_url"
            alt="收款码"
            class="qr-image"
            @error="qrError = true"
          />
          <p v-if="qrError" class="qr-error">收款码未配置，请联系管理员</p>
          <p v-else class="qr-hint">{{ cfg.alipay_note }}</p>
        </div>

        <div class="mode-notice">
          <p>请使用支付宝按订单金额完成付款。</p>
          <p>付款金额需与订单应付金额保持一致：¥{{ orderAmount }}</p>
          <p>建议付款备注填写订单号：{{ orderId }}</p>
        </div>

        <div class="status-panel">
          <p class="status-title">支付状态</p>
          <p class="status-value">{{ statusText }}</p>
          <p class="instruction">支付完成后系统会通过正式 webhook 自动同步订单状态与权益，无需手工确认。</p>
        </div>

        <div class="action-row">
          <button class="btn-secondary" :disabled="polling" @click="refreshOrderStatus">{{ polling ? '刷新中...' : '刷新支付状态' }}</button>
          <button class="btn-secondary" @click="router.push('/orders')">返回订单列表</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { publicPaymentConfigApi } from '@/api/paymentConfig'
import { ordersApi } from '@/api/orders'
import ShopNav from '@/components/shop/ShopNav.vue'

const route = useRoute()
const router = useRouter()
const orderId = Number(route.params.orderId || route.query.order_id || 0)
const orderAmount = ref('0.00')
const loading = ref(true)
const error = ref('')
const qrError = ref(false)
const polling = ref(false)
const orderStatus = ref('pending')
const cfg = ref<any>({})
let pollTimer: number | null = null

const statusText = computed(() => ({
  pending: '待支付',
  processing: '支付处理中',
  paid: '已支付',
  failed: '支付失败',
  cancelled: '已取消',
}[orderStatus.value] || orderStatus.value))

async function loadOrder() {
  if (!orderId) {
    throw new Error('订单参数缺失')
  }
  const order = await ordersApi.get(orderId)
  orderAmount.value = typeof order.total_amount === 'number' ? order.total_amount.toFixed(2) : order.total_amount
  orderStatus.value = order.status
  if (order.status === 'paid') {
    stopPolling()
    setTimeout(() => {
      router.replace('/orders?status=paid')
    }, 1200)
  }
}

async function refreshOrderStatus() {
  polling.value = true
  try {
    await loadOrder()
  } catch (e: any) {
    error.value = e?.message || e?.detail || '查询订单状态失败'
  } finally {
    polling.value = false
  }
}

function startPolling() {
  stopPolling()
  pollTimer = window.setInterval(() => {
    refreshOrderStatus()
  }, 3000)
}

function stopPolling() {
  if (pollTimer != null) {
    window.clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    cfg.value = await publicPaymentConfigApi.get()
    await loadOrder()
    if (orderStatus.value !== 'paid') {
      startPolling()
    }
  } catch (e: any) {
    error.value = e?.message || e?.detail || '加载失败，请确认后端服务已启动'
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.alipay-qr-page { min-height: 100vh; background: #f5f5f7; }
.qr-wrapper { display: flex; justify-content: center; align-items: center; padding: 40px 16px; }
.qr-card { background: #fff; border-radius: 16px; padding: 36px; max-width: 440px; width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,.08); text-align: center; }
.qr-card h2 { margin-bottom: 16px; font-size: 20px; }
.order-id { color: #888; font-size: 14px; margin: 4px 0; }
.amount { color: #333; font-size: 15px; margin: 4px 0 8px; }
.amount strong { font-size: 18px; color: #1677ff; }
.qr-container { margin: 24px 0; }
.qr-image { width: 240px; height: 240px; border: 1px solid #eee; border-radius: 8px; object-fit: contain; }
.qr-hint { color: #888; font-size: 13px; margin-top: 10px; line-height: 1.5; }
.qr-error { color: #ff4d4f; font-size: 14px; margin-top: 10px; }
.mode-notice { background: #f6ffed; border: 1px solid #b7eb8f; border-radius: 8px; padding: 12px; margin: 12px 0; text-align: left; font-size: 13px; color: #389e0d; }
.mode-notice p { margin: 4px 0; }
.status-panel { background: #fafafa; border: 1px solid #f0f0f0; border-radius: 12px; padding: 14px; margin-top: 16px; text-align: left; }
.status-panel.error { color: #cf1322; background: #fff1f0; border-color: #ffccc7; }
.status-title { margin: 0 0 6px; font-size: 13px; color: #666; }
.status-value { margin: 0 0 8px; font-size: 16px; color: #1f1f1f; font-weight: 600; }
.instruction { color: #666; font-size: 13px; margin: 0; line-height: 1.6; }
.action-row { display: flex; gap: 12px; margin-top: 16px; }
.btn-secondary { flex: 1; background: #fff; color: #666; border: 1px solid #ddd; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-secondary:disabled { opacity: 0.6; cursor: not-allowed; }
@media (max-width: 640px) {
  .qr-card { padding: 24px; }
  .action-row { flex-direction: column; }
}
</style>
