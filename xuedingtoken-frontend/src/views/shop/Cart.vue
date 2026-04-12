<template>
  <div class="cart-page">
    <ShopNav />

    <div class="container page-content">
      <div class="page-header">
        <h1 class="section-title">购物车</h1>
        <p class="section-desc">确认商品后进入结算</p>
      </div>

      <!-- Steps -->
      <div class="step-bar">
        <div class="step-item">
          <div class="step-circle active">1</div>
          <span class="step-label active">购物车</span>
        </div>
        <div class="step-divider"></div>
        <div class="step-item">
          <div class="step-circle inactive">2</div>
          <span class="step-label">订单结算</span>
        </div>
        <div class="step-divider"></div>
        <div class="step-item">
          <div class="step-circle inactive">3</div>
          <span class="step-label">发起支付</span>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="cartStore.totalItems === 0" class="empty-wrap">
        <BaseEmpty
          icon="🛒"
          title="购物车为空"
          desc="快去挑选心仪的商品吧！"
          action="去逛逛"
          @action="$router.push('/products')"
        />
      </div>

      <!-- Cart items -->
      <div v-else class="cart-layout">
        <div class="cart-items">
          <div class="cart-table-header">
            <span>商品</span>
            <span>单价</span>
            <span>数量</span>
            <span>小计</span>
            <span>操作</span>
          </div>
          <div v-for="item in cartStore.items" :key="item.id" class="cart-item">
            <div class="cart-item-info">
              <div class="cart-item-img" :style="{ background: imgColor(item.product_id) }"></div>
              <div>
                <div class="cart-item-cat">{{ item.category }}</div>
                <div class="cart-item-name">{{ item.product_name }}</div>
              </div>
            </div>
            <div class="cart-item-price">¥{{ item.unit_price }}</div>
            <div class="cart-item-qty">
              <QuantityStepper :modelValue="item.quantity" @update:modelValue="handleUpdateQuantity(item.id, $event)" />
            </div>
            <div class="cart-item-subtotal">¥{{ (item.unit_price * item.quantity).toFixed(2) }}</div>
            <button class="delete-btn" @click="removeItem(item.id)">🗑️</button>
          </div>
        </div>

        <!-- Summary -->
        <div class="cart-summary">
          <h3 class="summary-title">订单摘要</h3>
          <div class="summary-row">
            <span>商品总价</span>
            <span>¥{{ cartStore.subtotal }}</span>
          </div>
          <div class="summary-row">
            <span>运费</span>
            <span>¥0</span>
          </div>
          <div class="summary-row coupon-row" v-if="cartStore.couponCode">
            <span>优惠券抵扣</span>
            <span>-¥{{ cartStore.discount }}</span>
          </div>
          <div class="summary-divider"></div>
          <div class="summary-row total-row">
            <span>应付总额</span>
            <span class="total-price">¥{{ cartStore.total }}</span>
          </div>
          <div class="coupon-input-row">
            <input class="input" placeholder="请输入优惠码" v-model="couponInput" />
            <button class="btn btn-outline btn-sm" @click="applyCoupon">使用</button>
          </div>
          <p v-if="couponMsg" class="coupon-msg">{{ couponMsg }}</p>
          <button class="btn btn-primary w-full btn-lg checkout-btn" :disabled="checkoutLoading" @click="handleCheckout">
            <span v-if="checkoutLoading">下单中...</span>
            <span v-else>去结算</span>
          </button>
        </div>
      </div>
    </div>

    <ShopFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ShopNav from '@/components/shop/ShopNav.vue'
import ShopFooter from '@/components/shop/ShopFooter.vue'
import QuantityStepper from '@/components/common/QuantityStepper.vue'
import BaseEmpty from '@/components/common/BaseEmpty.vue'
import { useCartStore } from '@/stores/cart'
import { useFeedbackStore } from '@/stores/feedback'

const router = useRouter()
const cartStore = useCartStore()
const feedback = useFeedbackStore()
const couponInput = ref('')
const couponMsg = ref('')
const checkoutLoading = ref(false)

const colors = ['#EDE9FE', '#DBEAFE', '#D1FAE5', '#FEF3C7', '#FCE7F3', '#E0E7FF']
const imgColor = (id: number) => colors[id % colors.length]

const removeItem = async (itemId: number) => {
  const ok = await feedback.confirm({
    title: '删除确认',
    message: '确定要删除此商品吗？',
    danger: true,
  })
  if (ok) {
    try {
      await cartStore.deleteItem(itemId)
      feedback.success('商品已删除')
    } catch (e: any) {
      feedback.error(e.message)
    }
  }
}

const handleUpdateQuantity = async (itemId: number, qty: number) => {
  try {
    await cartStore.updateItem(itemId, qty)
  } catch (e: any) {
    feedback.error(e.message)
  }
}

const applyCoupon = async () => {
  if (!couponInput.value.trim()) return
  couponMsg.value = ''
  try {
    await cartStore.setCoupon(couponInput.value.trim())
    const code = couponInput.value.trim().toUpperCase()
    if (code === 'SAVE10') {
      couponMsg.value = '✓ 优惠码已应用：满减10%'
    } else if (code === 'FREE') {
      couponMsg.value = '✓ 优惠码已应用：全额抵扣'
    } else if (cartStore.discount === 0) {
      couponMsg.value = '✕ 优惠码无效'
    } else {
      couponMsg.value = '✓ 优惠码已应用'
    }
  } catch (e: any) {
    couponMsg.value = '✕ ' + e.message
  }
}

const handleCheckout = async () => {
  checkoutLoading.value = true
  try {
    const order = await cartStore.createOrder()
    feedback.success(`订单已创建，跳转支付页面…`)
    router.push('/checkout/' + order.id)
    couponInput.value = ''
    couponMsg.value = ''
  } catch (e: any) {
    feedback.error(e.message || '下单失败')
  } finally {
    checkoutLoading.value = false
  }
}

onMounted(async () => {
  try {
    await cartStore.fetchCart()
  } catch (e: any) {
    // not logged in, cart is empty
  }
})
</script>

<style scoped>
.page-content {
  padding-top: 32px;
  padding-bottom: 32px;
}
.page-header { margin-bottom: 20px; }
.step-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: 32px;
}
.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.step-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
}
.step-circle.active {
  background: var(--color-primary);
  color: #fff;
}
.step-circle.inactive {
  background: #E5E7EB;
  color: var(--color-text-muted);
}
.step-label {
  font-size: 14px;
  font-weight: 500;
}
.step-label.active {
  color: var(--color-primary);
}
.step-label:not(.active) {
  color: var(--color-text-muted);
}
.step-divider {
  width: 100px;
  height: 2px;
  background: #E5E7EB;
  margin: 0 12px;
  margin-bottom: 20px;
}
.empty-wrap { margin-top: 24px; }
.cart-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 32px;
  align-items: flex-start;
}
.cart-table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 60px;
  gap: 16px;
  padding: 12px 16px;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 16px;
}
.cart-item {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 60px;
  gap: 16px;
  align-items: center;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: 12px;
  background: var(--color-bg);
}
.cart-item-info { display: flex; align-items: center; gap: 12px; }
.cart-item-img { width: 56px; height: 56px; border-radius: var(--radius-md); flex-shrink: 0; }
.cart-item-cat { font-size: 11px; color: var(--color-text-muted); margin-bottom: 4px; }
.cart-item-name { font-size: 14px; font-weight: 500; color: var(--color-text); }
.cart-item-price { font-size: 15px; font-weight: 600; color: var(--color-text); }
.cart-item-qty { display: flex; align-items: center; }
.cart-item-subtotal { font-size: 15px; font-weight: 700; color: var(--color-danger); }
.delete-btn { background: none; border: none; font-size: 16px; cursor: pointer; opacity: 0.5; transition: opacity 0.2s; }
.delete-btn:hover { opacity: 1; }

.cart-summary {
  background: #F9FAFB;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 24px;
  position: sticky;
  top: 80px;
}
.summary-title { font-size: 16px; font-weight: 700; margin-bottom: 20px; color: var(--color-text); }
.summary-row { display: flex; justify-content: space-between; font-size: 14px; color: var(--color-text-secondary); margin-bottom: 12px; }
.coupon-row { color: var(--color-success); }
.summary-divider { height: 1px; background: var(--color-border); margin: 16px 0; }
.total-row { font-size: 16px; font-weight: 700; color: var(--color-text); }
.total-price { color: var(--color-danger); font-size: 20px; }
.coupon-input-row { display: flex; gap: 8px; margin: 16px 0; }
.coupon-input-row .input { flex: 1; }
.coupon-msg { font-size: 13px; margin-bottom: 12px; }
.checkout-btn { margin-top: 8px; width: 100%; height: 44px; }
</style>
