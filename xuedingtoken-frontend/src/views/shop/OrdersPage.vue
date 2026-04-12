<template>
  <div class="orders-page">
    <ShopNav />
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">📋 我的订单</h1>
        <button class="btn-refresh" @click="fetchOrders">🔄 刷新</button>
      </div>

      <div v-if="loading" class="state-page">加载中…</div>
      <div v-else-if="error" class="state-page error">{{ error }}</div>
      <div v-else-if="orders.length === 0" class="state-page">
        <div class="empty-icon">📋</div>
        <div>暂无订单</div>
        <router-link to="/products" class="btn-shop">前往商品中心</router-link>
      </div>
      <div v-else class="order-list">
        <div v-for="o in orders" :key="o.id" class="order-card">
          <div class="order-header">
            <div class="order-no">{{ o.order_no }}</div>
            <span :class="['badge', 'badge-' + o.status]">{{ statusText(o.status) }}</span>
          </div>
          <div class="order-meta">
            <span>¥{{ typeof o.total_amount === 'number' ? o.total_amount.toFixed(2) : o.total_amount }}</span>
            <span class="order-date">{{ fmtDate(o.created_at) }}</span>
          </div>
          <div class="order-actions">
            <router-link :to="'/checkout/' + o.id" class="btn-detail">查看详情</router-link>
            <router-link v-if="o.status === 'pending'" :to="'/checkout/' + o.id" class="btn-pay">去支付</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ordersApi } from '@/api/orders'
import ShopNav from '@/components/shop/ShopNav.vue'

const orders = ref<any[]>([])
const loading = ref(false)
const error = ref('')

const fetchOrders = async () => {
  loading.value = true; error.value = ''
  try { orders.value = await ordersApi.list() }
  catch (e: any) { error.value = e.message }
  finally { loading.value = false }
}

const statusText = (s: string) => ({ pending:'待支付', paid:'已支付', cancelled:'已取消', processing:'支付中', failed:'失败' }[s] || s)
const fmtDate = (d: string) => d ? new Date(d).toLocaleString('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) : '—'

onMounted(fetchOrders)
</script>

<style scoped>
.orders-page { min-height: 100vh; background: #f5f5f7; }
.container { max-width: 800px; margin: 0 auto; padding: 32px 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 700; color: #1a1a2e; }
.btn-refresh { font-size: 13px; padding: 6px 14px; background: #fff; color: #666; border: 1px solid #d9d9d9; border-radius: 6px; cursor: pointer; }
.state-page { text-align: center; padding: 80px; color: #888; }
.state-page.error { color: #ff4d4f; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.btn-shop { display: inline-block; margin-top: 16px; color: #aa3bff; text-decoration: none; font-size: 14px; }
.order-list { display: flex; flex-direction: column; gap: 14px; }
.order-card { background: #fff; border-radius: 12px; padding: 16px 20px; }
.order-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.order-no { font-family: monospace; font-size: 13px; font-weight: 600; color: #1a1a2e; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600; }
.badge-pending { background: #fffbe6; color: #ad6800; }
.badge-paid { background: #f6ffed; color: #389e0d; }
.badge-cancelled { background: #fff1f0; color: #cf1322; }
.order-meta { display: flex; justify-content: space-between; font-size: 14px; color: #555; margin-bottom: 12px; }
.order-date { font-size: 12px; color: #999; }
.order-actions { display: flex; gap: 10px; }
.btn-detail, .btn-pay { padding: 6px 14px; border-radius: 6px; font-size: 13px; text-decoration: none; }
.btn-detail { background: #fff; color: #666; border: 1px solid #d9d9d9; }
.btn-pay { background: #aa3bff; color: #fff; border: none; }
</style>
