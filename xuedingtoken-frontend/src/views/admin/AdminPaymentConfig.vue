<template>
  <div class="page">
    <div class="header-row">
      <div>
        <h2>支付配置</h2>
        <p class="subtext">维护正式支付方式、支付展示信息和异常补偿入口。订单支付成功后应由 webhook 自动完成落单与发权益。</p>
      </div>
      <div class="header-actions">
        <RouterLink class="link-btn" to="/admin/system/payment-events">查看 webhook 日志</RouterLink>
        <RouterLink class="link-btn" to="/admin/orders">查看支付订单</RouterLink>
      </div>
    </div>

    <div v-if="loading">加载中...</div>
    <div v-else-if="error" class="error-box">{{ error }} <button @click="load">重试</button></div>
    <form v-else class="config-form" @submit.prevent="save">
      <section class="section-card">
        <h3>正式支付配置</h3>
        <label>支付模式
          <select v-model="cfg.payment_mode">
            <option value="alipay_qr">alipay_qr</option>
            <option value="stripe">stripe</option>
          </select>
        </label>
        <label>显示名称 <input v-model="cfg.alipay_display_name" /></label>
        <label>收款码图片 URL <input v-model="cfg.alipay_qr_image_url" placeholder="https://..." /></label>
        <label>收款页跳转链接 <input v-model="cfg.alipay_qr_target_url" placeholder="可选，用于外部支付落地页" /></label>
        <label>支付说明 <textarea v-model="cfg.alipay_note"></textarea></label>
      </section>

      <section class="section-card">
        <h3>支付方式控制</h3>
        <label>支付功能启用
          <select v-model="cfg.is_enabled">
            <option :value="true">开启</option>
            <option :value="false">关闭</option>
          </select>
        </label>
        <label>启用支付方式（逗号分隔，如：alipay_qr,stripe）
          <input v-model="cfg.enabled_payment_methods" placeholder="alipay_qr,stripe" style="font-family:monospace;" />
        </label>
        <label>默认支付方式 <input v-model="cfg.default_payment_method" placeholder="alipay_qr" /></label>
        <label>币种 <input v-model="cfg.default_currency" placeholder="CNY" /></label>
      </section>

      <section class="section-card ops-card">
        <h3>异常补偿</h3>
        <p class="ops-hint">仅用于 webhook 已收到、但订单仍未完成发权益的异常情况。系统会校验有效支付凭据后再执行补偿，不会提供模拟支付成功入口。</p>
        <div class="repair-row">
          <input v-model="repairOrderId" type="number" min="1" placeholder="输入订单 ID" />
          <button type="button" class="btn-outline" :disabled="repairing || !repairOrderId" @click="repairOrder">
            {{ repairing ? '处理中...' : '执行异常补偿' }}
          </button>
        </div>
        <p v-if="repairMessage" class="repair-msg">{{ repairMessage }}</p>
      </section>

      <div class="footer-row">
        <button type="submit" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
        <span v-if="msg" class="msg">{{ msg }}</span>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { adminPaymentConfigApi } from '@/api/adminPayment'

type PaymentConfigForm = {
  payment_mode: string
  default_currency: string
  is_enabled: boolean
  alipay_display_name: string
  alipay_qr_image_url: string
  alipay_qr_target_url: string
  alipay_note: string
  enabled_payment_methods: string
  default_payment_method: string
  alipay_qr_mode: string
}

const defaultConfig = (): PaymentConfigForm => ({
  payment_mode: 'alipay_qr',
  default_currency: 'CNY',
  is_enabled: true,
  alipay_display_name: '',
  alipay_qr_image_url: '',
  alipay_qr_target_url: '',
  alipay_note: '',
  enabled_payment_methods: 'alipay_qr',
  default_payment_method: 'alipay_qr',
  alipay_qr_mode: 'universal_static',
})

const loading = ref(true)
const error = ref('')
const saving = ref(false)
const msg = ref('')
const repairOrderId = ref('')
const repairing = ref(false)
const repairMessage = ref('')
const cfg = ref<PaymentConfigForm>(defaultConfig())

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await adminPaymentConfigApi.get()
    let methods = data.enabled_payment_methods
    if (typeof methods === 'string') {
      methods = methods.split(',').map((m: string) => m.trim()).filter(Boolean)
    } else if (!Array.isArray(methods)) {
      methods = ['alipay_qr']
    }
    cfg.value = {
      ...defaultConfig(),
      ...data,
      enabled_payment_methods: methods.join(','),
      payment_mode: data.payment_mode || 'alipay_qr',
      alipay_qr_mode: 'universal_static',
      alipay_note: data.alipay_note || '',
      is_enabled: data.is_enabled !== false,
    }
  } catch (e: any) {
    error.value = e?.message || e?.detail || '加载失败，请检查后端服务'
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  error.value = ''
  msg.value = ''
  try {
    const payload: Record<string, any> = { ...cfg.value, alipay_qr_mode: 'universal_static' }
    if (Array.isArray(payload.enabled_payment_methods)) {
      payload.enabled_payment_methods = payload.enabled_payment_methods.join(',')
    }
    await adminPaymentConfigApi.update(payload)
    msg.value = '保存成功'
    setTimeout(() => { msg.value = '' }, 3000)
    await load()
  } catch (e: any) {
    error.value = e?.message || e?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

async function repairOrder() {
  if (!repairOrderId.value || repairing.value) return
  repairing.value = true
  repairMessage.value = ''
  try {
    const res = await adminPaymentConfigApi.repairOrder(Number(repairOrderId.value))
    repairMessage.value = res.message || '异常补偿已完成'
  } catch (e: any) {
    repairMessage.value = e?.message || e?.detail || '异常补偿失败'
  } finally {
    repairing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: 20px; }
.header-row { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.header-row h2 { margin: 0 0 8px; }
.subtext { margin: 0; color: #666; font-size: 14px; max-width: 760px; line-height: 1.6; }
.header-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.link-btn { background: #fff; color: #1677ff; border: 1px solid #91caff; padding: 8px 14px; border-radius: 8px; text-decoration: none; }
.config-form { display: grid; gap: 16px; }
.section-card { background: #fff; border: 1px solid #edf0f3; border-radius: 14px; padding: 20px; display: grid; gap: 12px; }
.section-card h3 { margin: 0 0 4px; font-size: 16px; }
.config-form label { display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #333; }
input, textarea, select { border: 1px solid #d9d9d9; border-radius: 8px; padding: 10px 12px; font-size: 14px; width: 100%; box-sizing: border-box; background: #fff; }
textarea { min-height: 96px; resize: vertical; }
.footer-row { display: flex; align-items: center; gap: 12px; }
button[type=submit], .btn-outline { background: #1677ff; color: #fff; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; }
button:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-outline { background: #fff; color: #1677ff; border: 1px solid #91caff; }
.msg { color: #389e0d; }
.error-box { background: #fff1f0; color: #cf1322; padding: 14px 16px; border-radius: 12px; }
.ops-hint { margin: 0; color: #666; font-size: 13px; line-height: 1.6; }
.repair-row { display: flex; gap: 12px; align-items: center; }
.repair-msg { margin: 0; color: #333; font-size: 13px; }
@media (max-width: 768px) {
  .header-row { flex-direction: column; }
  .repair-row { flex-direction: column; align-items: stretch; }
}
</style>
