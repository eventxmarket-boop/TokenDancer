<template>
  <div class="product-detail-page">
    <ShopNav />

    <div class="container page-content" v-if="product">
      <!-- Breadcrumb -->
      <nav class="breadcrumb">
        <router-link to="/">首页</router-link>
        <span>/</span>
        <router-link to="/products">商品中心</router-link>
        <span>/</span>
        <span>{{ product.name }}</span>
      </nav>

      <div class="detail-layout">
        <!-- Left: Image -->
        <div class="detail-image">
          <div class="product-image-placeholder" :style="{ background: imgColor }">
            <span>商品图片</span>
          </div>
        </div>

        <!-- Right: Info -->
        <div class="detail-info">
          <div class="info-top">
            <span class="badge badge-primary">{{ product.category }}</span>
            <span v-if="product.tag" class="badge badge-warning">{{ product.tag }}</span>
            <span :class="['badge', product.product_type === 'subscription' ? 'badge-subscription' : product.product_type === 'token_pack' ? 'badge-token' : 'badge-balance']">
              {{ productTypeLabel(product.product_type) }}
            </span>
          </div>
          <h1 class="product-title">{{ product.name }}</h1>

          <div class="stock-status">
            <span class="badge badge-success" v-if="product.stock > 0">有库存</span>
            <span v-if="product.stock > 0" class="stock-count">剩余 {{ product.stock }} 件</span>
          </div>

          <div class="price-section">
            <span class="price-yen">¥</span>
            <span class="price-main">{{ product.price }}</span>
            <span class="price-unit">/{{ product.price_unit ?? '次' }}</span>
          </div>

          <div class="spec-section">
            <label class="label">选择规格</label>
            <div class="spec-selected">
              <span>默认规格</span>
              <span class="stock-inline">剩余 {{ product.stock }} 件</span>
            </div>
          </div>

          <div class="quantity-section">
            <label class="label">购买数量</label>
            <QuantityStepper v-model="qty" />
          </div>

          <div class="coupon-section">
            <label class="label">优惠码</label>
            <div class="coupon-input">
              <input class="input" placeholder="请输入优惠码" v-model="couponCode" />
              <button class="btn btn-outline btn-sm" @click="applyCoupon">使用</button>
            </div>
          </div>

          <div class="email-section">
            <label class="label">游客邮箱（用于查询订单）</label>
            <input class="input" type="email" placeholder="请输入邮箱" v-model="email" />
          </div>

          <!-- Payment -->
          <div class="payment-section">
            <p class="payment-hint">请选择支付方式</p>
            <button class="btn btn-outline payment-btn">💳 支付宝</button>
          </div>

          <div class="action-buttons">
            <button class="btn btn-outline btn-lg" @click="addToCart">加入购物车</button>
            <button class="btn btn-primary btn-lg" @click="buyNow">立即支付</button>
          </div>
        </div>
      </div>

      <!-- Description collapse/expand -->
      <div class="detail-tabs">
        <div class="tabs-header">
          <button class="tab-btn" :class="{ active: activeTab === 'desc' }" @click="activeTab = 'desc'">商品描述</button>
          <button class="tab-btn" :class="{ active: activeTab === 'guide' }" @click="activeTab = 'guide'">新手引导</button>
          <button class="tab-btn" :class="{ active: activeTab === 'howto' }" @click="activeTab = 'howto'">使用方法</button>
        </div>

        <!-- Collapsible detail content -->
        <div class="tabs-body card">
          <div v-if="!descExpanded && activeTab === 'desc'" class="desc-preview">
            <p>这是商品的简要描述...</p>
            <button class="btn btn-ghost btn-sm mt-2" @click="descExpanded = true">查看详情 ∨</button>
          </div>
          <div v-else-if="activeTab === 'desc'" class="tab-content">
            <p>这是商品的详细描述区域。包含产品的功能、特点、使用说明等信息。</p>
            <div v-if="product.models" class="models-list">
              <h3>支持模型</h3>
              <div class="model-tags">
                <span v-for="m in product.models" :key="m" class="badge badge-primary model-tag">{{ m }}</span>
              </div>
            </div>
          </div>
          <!-- Guide -->
          <div v-if="activeTab === 'guide'" class="tab-content">
            <h3>第一次来？先看这里</h3>
            <div class="guide-steps-mini">
              <div class="guide-step-item">
                <span class="step-n">1</span>
                <span>主站注册 — 在主站平台创建账号</span>
              </div>
              <div class="guide-step-item">
                <span class="step-n">2</span>
                <span>商店下单 — 购买算力套餐或余额</span>
              </div>
              <div class="guide-step-item">
                <span class="step-n">3</span>
                <span>主站兑换 — 将购买的产品在主站兑换使用</span>
              </div>
            </div>
          </div>
          <!-- How to -->
          <div v-if="activeTab === 'howto'" class="tab-content">
            <h3>下单之后使用方法</h3>
            <div class="howto-steps">
              <div class="howto-step">
                <span class="step-n">1</span>
                <span>完成支付后，系统自动发货</span>
              </div>
              <div class="howto-step">
                <span class="step-n">2</span>
                <span>前往主站完成账号注册/登录</span>
              </div>
              <div class="howto-step">
                <span class="step-n">3</span>
                <span>在主站使用兑换码或自动到账的余额</span>
              </div>
              <div class="howto-step">
                <span class="step-n">4</span>
                <span>开始使用 API 调用顶级 AI 模型</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="back-link">
        <router-link to="/products">← 回到商品列表</router-link>
      </div>
    </div>

    <!-- Product not found -->
    <div class="container page-content" v-else>
      <BaseEmpty
        icon="🔍"
        title="商品未找到"
        desc="该商品不存在或已下架"
        action="返回商品列表"
        @action="$router.push('/products')"
      />
    </div>

    <ShopFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ShopNav from '@/components/shop/ShopNav.vue'
import ShopFooter from '@/components/shop/ShopFooter.vue'
import QuantityStepper from '@/components/common/QuantityStepper.vue'
import BaseEmpty from '@/components/common/BaseEmpty.vue'
import { productsApi } from '@/api/products'
import { useCartStore } from '@/stores/cart'
import { useFeedbackStore } from '@/stores/feedback'

const route = useRoute()
const productId = Number(route.params.id)
const cartStore = useCartStore()
const feedback = useFeedbackStore()

interface Product {
  id: number
  name: string
  slug: string
  category: string
  tag: string | null
  price_cny: number
  stock: number
  delivery_type: string
  is_active: boolean
  sort_order: number
  description?: string | null
  price_usd_value?: number
  // mapped for display
  price: number
  price_unit: string
  models?: string[]
  autoDeliver?: boolean
}

const product = ref<Product | null>(null)
const colors = ['#EDE9FE', '#DBEAFE', '#D1FAE5', '#FEF3C7', '#FCE7F3', '#E0E7FF']
const imgColor = computed(() => colors[productId % colors.length])
const productTypeLabel = (t: string) => ({ balance_topup:'余额充值', subscription:'订阅套餐', token_pack:'Token包' }[t] || t)

const qty = ref(1)
const couponCode = ref('')
const email = ref('')
const activeTab = ref('desc')
const descExpanded = ref(false)

const addToCart = async () => {
  if (!product.value) return
  try {
    await cartStore.addItem(product.value.id, qty.value)
    feedback.success('已加入购物车')
  } catch (e: any) {
    feedback.error(e.message)
  }
}

const buyNow = async () => {
  if (!product.value) return
  try {
    await cartStore.addItem(product.value.id, qty.value)
    feedback.success('已加入购物车，正在跳转...')
    setTimeout(() => {
      window.location.href = '/cart'
    }, 800)
  } catch (e: any) {
    feedback.error(e.message)
  }
}

const applyCoupon = async () => {
  if (!couponCode.value.trim()) {
    feedback.warning('请输入优惠码')
    return
  }
  try {
    await cartStore.setCoupon(couponCode.value.trim())
    feedback.success('优惠码已应用')
  } catch (e: any) {
    feedback.error(e.message || '优惠码无效')
  }
}

onMounted(async () => {
  try {
    const raw = await productsApi.get(productId)
    product.value = {
      ...raw,
      price: raw.price_cny,
      price_unit: raw.delivery_type === 'auto' ? '次' : '份',
    }
  } catch (e) {
    product.value = null
  }
})
</script>

<style scoped>
.page-content {
  padding-top: 28px;
  padding-bottom: 32px;
}
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #9CA3AF;
  margin-bottom: 28px;
}
.breadcrumb a:hover { color: var(--color-primary); }
.breadcrumb span:last-child { color: var(--color-text); font-weight: 500; }

.detail-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  margin-bottom: 40px;
}
.product-image-placeholder {
  width: 100%;
  height: 360px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(0,0,0,0.2);
  font-size: 18px;
  font-weight: 600;
}
.info-top {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.product-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 16px;
  line-height: 1.3;
}
.stock-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}
.stock-count {
  font-size: 13px;
  color: var(--color-text-secondary);
}
.price-section {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 24px;
}
.price-yen { font-size: 20px; font-weight: 700; color: var(--color-danger); }
.price-main { font-size: 30px; font-weight: 700; color: var(--color-danger); }
.price-unit { font-size: 14px; color: var(--color-text-muted); }
.spec-section, .quantity-section, .coupon-section, .email-section { margin-bottom: 16px; }
.spec-selected {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
}
.stock-inline { font-size: 13px; color: var(--color-text-secondary); flex: 1; }
.coupon-input { display: flex; gap: 8px; }
.coupon-input .input { max-width: 240px; }
.payment-section {
  border: 1px solid #E5E7EB;
  padding: 16px;
  border-radius: var(--radius-md);
  margin-bottom: 16px;
}
.payment-hint { font-size: 14px; color: var(--color-text-secondary); margin-bottom: 12px; }
.payment-btn { display: flex; align-items: center; gap: 8px; font-size: 15px; padding: 10px 20px; margin-bottom: 0; }
.action-buttons { display: flex; gap: 12px; margin-top: 8px; }
.action-buttons .btn { flex: 1; height: 44px; }

/* Tabs */
.detail-tabs { margin-bottom: 32px; }
.tabs-header {
  display: flex;
  gap: 0;
  border-bottom: 2px solid var(--color-border);
  margin-bottom: 24px;
}
.tab-btn {
  padding: 12px 24px;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-secondary);
  border: none;
  background: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}
.tab-btn.active { color: var(--color-primary); border-bottom-color: var(--color-primary); }
.tab-btn:hover:not(.active) { color: var(--color-text); }
.tabs-body { min-height: 200px; }
.tab-content p { font-size: 15px; color: var(--color-text-secondary); line-height: 1.8; }
.tab-content h3 { font-size: 16px; font-weight: 600; margin-bottom: 16px; color: var(--color-text); }
.models-list { margin-top: 20px; }
.model-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.model-tag { font-size: 14px; padding: 4px 12px; }
.guide-steps-mini, .howto-steps { display: flex; flex-direction: column; gap: 12px; }
.guide-step-item, .howto-step { display: flex; align-items: center; gap: 12px; font-size: 14px; color: var(--color-text-secondary); }
.step-n {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--color-primary); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 600; flex-shrink: 0;
}
.desc-preview { padding: 8px 0; }
.back-link { text-align: center; margin-top: 24px; }
.back-link a { color: var(--color-primary); font-size: 14px; font-weight: 500; }
.back-link a:hover { text-decoration: underline; }
.badge-subscription { background: #f0f5ff; color: #597ef7; }
.badge-token { background: #fff7e6; color: #fa8c16; }
.badge-balance { background: #f6ffed; color: #52c41a; }
</style>
