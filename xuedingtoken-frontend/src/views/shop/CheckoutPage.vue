<template>
  <div class="checkout-page">
    <ShopNav />

    <div class="container" v-if="order">
      <div :class="['status-banner', 'status-' + order.status]">
        <span class="status-icon">{{ statusIcon(order.status) }}</span>
        <span class="status-text">{{ statusText(order.status) }}</span>
      </div>

      <div class="checkout-layout">
        <div class="checkout-main">
          <h2 class="section-title">📋 订单信息</h2>
          <div class="order-info-card">
            <div class="info-row"><span class="info-label">订单号</span><code class="order-no">{{ order.order_no }}</code></div>
            <div class="info-row"><span class="info-label">创建时间</span><span>{{ fmtDate(order.created_at) }}</span></div>
            <div class="info-row"><span class="info-label">订单状态</span><span :class="['status-badge', 'badge-' + order.status]">{{ statusText(order.status) }}</span></div>
          </div>

          <h2 class="section-title">🛒 订单明细</h2>
          <div class="items-list">
            <div v-for="item in order.items" :key="item.id" class="item-row">
              <div class="item-name">{{ item.product_name }}</div>
              <div class="item-type">{{ productTypeLabel(item.product_type) }}</div>
              <div class="item-qty">x{{ item.quantity }}</div>
              <div class="item-price">¥{{ typeof item.subtotal === 'number' ? item.subtotal.toFixed(2) : item.subtotal }}</div>
            </div>
          </div>

          <div v-if="order.status === 'paid'" class="fulfillment-notice">
            <div class="fulfillment-icon">✅</div>
            <div class="fulfillment-text">
              <strong>支付成功！</strong>
              <span v-if="hasBalanceTopup"> 余额已充值到您的账户。</span>
              <span v-if="hasSubscription"> 订阅已生效，有效期已更新。</span>
              <span v-if="hasTokenPack"> Token 配额已发放。</span>
              <span v-if="!hasBalanceTopup && !hasSubscription && !hasTokenPack"> 权益已发放。</span>
              <br><router-link to="/main/billing" class="fulfillment-link">前往账单中心 →</router-link>
              <span v-if="hasSubscription"> · <router-link to="/main/subscriptions" class="fulfillment-link">查看订阅 →</router-link></span>
            </div>
          </div>

          <div v-if="order.status === 'processing'" class="processing-notice">
            <div class="processing-icon">🔄</div>
            <div>
              支付处理中，系统正在等待正式支付结果回调…
              <button class="btn-refresh-inline" @click="fetchOrder">🔄 刷新状态</button>
            </div>
          </div>

          <div v-if="order.status === 'pending'" class="pay-section">
            <h2 class="section-title">💳 选择支付方式</h2>
            <template v-if="paymentConfig">
              <div class="pay-options">
                <div
                  v-for="method in paymentConfig.enabled_payment_methods"
                  :key="method"
                  class="pay-option"
                  :class="{ selected: selectedMethod === method }"
                  @click="selectedMethod = method"
                >
                  <input type="radio" :value="method" v-model="selectedMethod" />
                  <span v-if="method === 'alipay_qr'">💙 {{ paymentConfig.alipay_display_name }}</span>
                  <span v-else-if="method === 'stripe'">💳 Stripe</span>
                  <span v-else-if="method === 'wxpay_qr'">🅿️ 微信支付</span>
                  <span v-else>{{ method }}</span>
                </div>
              </div>
            </template>
            <div v-else class="pay-options">
              <div class="pay-option selected">
                <input type="radio" value="alipay_qr" v-model="selectedMethod" />
                💙 支付宝扫码支付
              </div>
            </div>
            <button class="btn-pay" :disabled="paying" @click="handlePay">
              {{ paying ? '支付处理中…' : '确认支付 ¥' + orderTotal }}
            </button>
            <p class="pay-hint">支付成功后，订单状态和权益将由正式 webhook 自动同步。</p>
            <p v-if="payError" class="pay-error">{{ payError }}</p>
          </div>

          <div v-if="order.status === 'cancelled'" class="cancel-notice">
            <div class="cancel-icon">❌</div>
            <div>此订单已取消，如需继续购买请返回购物车重新下单。</div>
            <router-link to="/cart" class="btn-back">返回购物车</router-link>
          </div>
        </div>

        <div class="checkout-summary">
          <h2 class="section-title">💰 金额汇总</h2>
          <div class="summary-card">
            <div class="summary-row">
              <span>商品总价</span>
              <span>¥{{ orderTotal }}</span>
            </div>
            <div class="summary-row total">
              <span>合计</span>
              <span>¥{{ orderTotal }}</span>
            </div>
          </div>
          <button class="btn-refresh" @click="fetchOrder">🔄 刷新订单状态</button>
          <router-link to="/orders" class="btn-orders">📋 查看全部订单</router-link>
        </div>
      </div>
    </div>

    <div v-else-if="loading" class="state-page">加载中…</div>
    <div v-else-if="errorMsg" class="state-page error">{{ errorMsg }}</div>
    <div v-else class="state-page">订单不存在</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ordersApi } from '@/api/orders'
import { paymentsApi } from '@/api/payments'
import { publicPaymentConfigApi } from '@/api/paymentConfig'
import { useFeedbackStore } from '@/stores/feedback'
import ShopNav from '@/components/shop/ShopNav.vue'

const route = useRoute()
const router = useRouter()
const feedback = useFeedbackStore()
const order = ref<any>(null)
const loading = ref(true)
const errorMsg = ref('')
const paying = ref(false)
const payError = ref('')
const selectedMethod = ref('alipay_qr')
const paymentConfig = ref<any>(null)

async function loadPaymentConfig() {
  try {
    const cfg: any = await publicPaymentConfigApi.get()
    paymentConfig.value = cfg
    selectedMethod.value = cfg.default_payment_method || 'alipay_qr'
  } catch {
    paymentConfig.value = null
  }
}

const orderTotal = computed(() => {
  if (!order.value) return '0.00'
  return typeof order.value.total_amount === 'number'
    ? order.value.total_amount.toFixed(2)
    : order.value.total_amount
})

const hasBalanceTopup = computed(() => order.value?.items?.some((i: any) => i.product_type === 'balance_topup') || false)
const hasSubscription = computed(() => order.value?.items?.some((i: any) => i.product_type === 'subscription') || false)
const hasTokenPack = computed(() => order.value?.items?.some((i: any) => i.product_type === 'token_pack') || false)

const productTypeLabel = (t: string) => ({ balance_topup: '余额充值', subscription: '订阅套餐', token_pack: 'Token包' }[t] || t)
const statusIcon = (s: string) => ({ pending: '⏳', paid: '✅', cancelled: '❌', processing: '🔄', failed: '⚠️' }[s] || '❓')
const statusText = (s: string) => ({ pending: '待支付', paid: '已支付', cancelled: '已取消', processing: '支付处理中', failed: '支付失败' }[s] || s)
const fmtDate = (d: string) => d ? new Date(d).toLocaleString('zh-CN') : '—'

const fetchOrder = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const id = Number(route.params.orderId)
    order.value = await ordersApi.get(id)
  } catch (e: any) {
    errorMsg.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const pollOrderPaid = async (orderId: number, intervalMs = 2000, maxMs = 30000) => {
  const start = Date.now()
  while (Date.now() - start < maxMs) {
    await new Promise((resolve) => setTimeout(resolve, intervalMs))
    try {
      const current = await ordersApi.get(orderId)
      order.value = current
      if (current.status === 'paid') return true
      if (current.status === 'cancelled' || current.status === 'failed') return false
    } catch {
      return false
    }
  }
  return false
}

const handlePay = async () => {
  if (paying.value || !order.value) return
  paying.value = true
  payError.value = ''
  try {
    const payment = await paymentsApi.create(order.value.id, selectedMethod.value || 'alipay_qr')
    feedback.success('支付页面已生成，正在跳转…')

    if (payment.payment_url && selectedMethod.value === 'alipay_qr') {
      router.push(payment.payment_url)
      return
    }

    const paid = await pollOrderPaid(order.value.id)
    if (paid) {
      feedback.success('支付成功，权益已自动发放。')
      await fetchOrder()
    } else {
      payError.value = '支付结果尚未同步，请稍后刷新订单状态'
      await fetchOrder()
    }
  } catch (e: any) {
    payError.value = e?.detail || e?.message || '支付失败，请重试'
    await fetchOrder()
  } finally {
    paying.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchOrder(), loadPaymentConfig()])
})
</script>

<style scoped>
.checkout-page { min-height: 100vh; background: #f5f5f7; }
.container { max-width: 960px; margin: 0 auto; padding: 32px 16px; }
.status-banner { display: flex; align-items: center; gap: 10px; padding: 14px 20px; border-radius: 12px; margin-bottom: 24px; font-size: 15px; font-weight: 600; }
.status-pending { background: #fffbe6; color: #ad6800; border: 1px solid #ffe58f; }
.status-paid { background: #f6ffed; color: #389e0d; border: 1px solid #b7eb8f; }
.status-cancelled { background: #fff1f0; color: #cf1322; border: 1px solid #ffccc7; }
.status-processing { background: #f0f5ff; color: #597ef7; border: 1px solid #adc6ff; }
.status-failed { background: #fff1f0; color: #cf1322; border: 1px solid #ffccc7; }
.checkout-layout { display: grid; grid-template-columns: 1fr 300px; gap: 24px; }
.section-title { font-size: 16px; font-weight: 700; color: #1a1a2e; margin-bottom: 12px; }
.order-info-card, .items-list, .summary-card { background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }
.info-row:last-child { border-bottom: none; }
.info-label { color: #888; }
.order-no { font-family: monospace; font-size: 13px; }
.item-row { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.item-row:last-child { border-bottom: none; }
.item-name { flex: 1; font-size: 14px; }
.item-type { font-size: 11px; background: #f0f0f0; color: #888; padding: 2px 6px; border-radius: 4px; margin: 0 8px; }
.item-qty { font-size: 13px; color: #888; margin: 0 16px; }
.item-price { font-size: 14px; font-weight: 600; }
.pay-section { background: #fff; border-radius: 12px; padding: 20px; margin-top: 16px; }
.pay-options { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.pay-option { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border: 1px solid #e5e4e7; border-radius: 8px; cursor: pointer; font-size: 14px; }
.pay-option.selected { border-color: #aa3bff; background: #fafafa; }
.btn-pay { width: 100%; padding: 14px; background: #aa3bff; color: #fff; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; }
.btn-pay:disabled { opacity: 0.6; cursor: not-allowed; }
.pay-hint { color: #666; font-size: 13px; margin-top: 10px; }
.pay-error { color: #ff4d4f; font-size: 13px; margin-top: 8px; text-align: center; }
.fulfillment-notice { background: #f6ffed; border: 1px solid #b7eb8f; border-radius: 12px; padding: 16px 20px; margin-top: 16px; display: flex; gap: 12px; align-items: flex-start; }
.fulfillment-icon { font-size: 24px; }
.fulfillment-text { font-size: 14px; color: #333; line-height: 1.8; }
.fulfillment-link { color: #1677ff; text-decoration: none; }
.processing-notice, .cancel-notice { background: #fff; border-radius: 12px; padding: 20px; margin-top: 16px; display: flex; gap: 12px; align-items: center; }
.processing-icon, .cancel-icon { font-size: 22px; }
.btn-refresh-inline, .btn-refresh, .btn-orders, .btn-back { margin-top: 12px; border: 1px solid #ddd; border-radius: 8px; padding: 10px 14px; background: #fff; color: #333; cursor: pointer; text-decoration: none; display: inline-flex; justify-content: center; }
.checkout-summary { position: sticky; top: 24px; align-self: start; }
.summary-row { display: flex; justify-content: space-between; padding: 10px 0; color: #555; }
.summary-row.total { border-top: 1px solid #f0f0f0; font-weight: 700; color: #111; }
.state-page { min-height: 40vh; display: flex; justify-content: center; align-items: center; font-size: 15px; color: #666; }
.state-page.error { color: #cf1322; }
@media (max-width: 900px) {
  .checkout-layout { grid-template-columns: 1fr; }
  .checkout-summary { position: static; }
}
</style>
