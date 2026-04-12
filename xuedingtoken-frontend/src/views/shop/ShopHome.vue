<template>
  <div class="shop-home">
    <!-- Nav -->
    <ShopNav />

    <!-- Hero -->
    <section class="hero">
      <div class="container hero-inner">
        <h1 class="hero-title">
          让每一个人<br>
          <span class="hero-accent">享受到这个世界上最顶级模型的智能</span>
        </h1>
        <div class="hero-actions">
          <button class="btn btn-primary btn-lg" @click="$router.push('/products')">浏览商品</button>
          <a href="/products" class="hero-link">查看全部商品 →</a>
        </div>
      </div>
    </section>

    <!-- New user guide -->
    <section class="guide-section">
      <div class="container">
        <h2 class="section-title">第一次来？先看这里</h2>
        <div class="guide-steps">
          <div class="guide-step">
            <div class="guide-num">{{ guideSteps[0].num }}</div>
            <div class="guide-text">
              <strong>{{ guideSteps[0].title }}</strong>
            </div>
          </div>
          <div class="guide-arrow">→</div>
          <div class="guide-step">
            <div class="guide-num">{{ guideSteps[1].num }}</div>
            <div class="guide-text">
              <strong>{{ guideSteps[1].title }}</strong>
            </div>
          </div>
          <div class="guide-arrow">→</div>
          <div class="guide-step">
            <div class="guide-num">{{ guideSteps[2].num }}</div>
            <div class="guide-text">
              <strong>{{ guideSteps[2].title }}</strong>
            </div>
          </div>
        </div>

        <!-- 展开的详细说明 -->
        <div v-if="showGuide" class="guide-detail">
          <div v-for="step in guideSteps" :key="step.num" class="guide-detail-item">
            <div class="guide-detail-num">{{ step.num }}</div>
            <div class="guide-detail-body">
              <div class="guide-detail-title">{{ step.detail }}</div>
              <p class="guide-detail-desc">{{ step.desc }}</p>
              <router-link v-if="step.link.startsWith('/')" :to="step.link" class="guide-detail-link">
                {{ step.linkText }} →
              </router-link>
              <a v-else :href="step.link" target="_blank" class="guide-detail-link">
                {{ step.linkText }} →
              </a>
            </div>
          </div>
        </div>

        <div class="guide-actions">
          <router-link to="/main/dashboard" class="btn btn-outline">去主站注册</router-link>
          <button class="btn btn-ghost" @click="showGuide = !showGuide">
            {{ showGuide ? '收起说明' : '看详细步骤' }}
          </button>
        </div>
      </div>
    </section>

    <!-- Featured products -->
    <section class="products-section">
      <div class="container">
        <div class="section-header">
          <div>
            <h2 class="section-title">精选商品</h2>
            <p class="section-desc">为您精心挑选的热销商品</p>
          </div>
          <a href="/products" class="btn btn-ghost">查看全部商品 →</a>
        </div>
        <div class="products-grid">
          <ProductCard v-for="p in featuredProducts" :key="p.id" :product="p" />
        </div>
      </div>
    </section>

    <!-- Community QR -->
    <section class="community-section">
      <div class="container">
        <h2 class="section-title text-center">加入官方用户群</h2>
        <p class="section-desc text-center">扫码添加官方人员，邀请您入群</p>
        <div class="qr-sections">
          <div v-for="(qr, i) in qrContents" :key="i" class="qr-card card">
            <img v-if="qr.image_url" :src="qr.image_url" :alt="qr.title" class="qr-img" />
            <div v-else class="qr-placeholder-img">📷</div>
            <div class="qr-title">{{ qr.title }}</div>
            <div class="qr-desc">{{ qr.description }}</div>
            <a v-if="qr.target_url" :href="qr.target_url" target="_blank" class="qr-link">查看 →</a>
          </div>
          <!-- 填充空位 -->
          <div v-for="i in Math.max(0, 3 - qrContents.length)" :key="'empty-'+i" class="qr-card card qr-empty">
            <div class="qr-placeholder-img">📷</div>
            <div class="qr-title">暂无内容</div>
            <div class="qr-desc">请在后台添加内容</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Latest news -->
    <section class="news-section">
      <div class="container">
        <div class="section-header">
          <div>
            <h2 class="section-title">最新动态</h2>
            <p class="section-desc">了解我们的最新公告和更新</p>
          </div>
          <a href="/announcements" class="btn btn-ghost">查看全部 →</a>
        </div>
        <div class="news-grid">
          <div class="news-card card" v-for="n in notices" :key="n.id">
            <div class="news-date">{{ n.date }}</div>
            <h3 class="news-title">{{ n.title }}</h3>
            <p class="news-excerpt">点击查看详情 →</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <ShopFooter />

    <!-- Welcome Popup -->
    <WelcomePopup />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ShopNav from '@/components/shop/ShopNav.vue'
import ShopFooter from '@/components/shop/ShopFooter.vue'
import ProductCard from '@/components/shop/ProductCard.vue'
import WelcomePopup from '@/components/common/WelcomePopup.vue'
import { productsApi } from '@/api/products'
import { contentApi } from '@/api/content'

const featuredProducts = ref<any[]>([])
const showGuide = ref(false)
const qrContents = ref<any[]>([])

onMounted(async () => {
  try {
    const raw = await productsApi.featured()
    featuredProducts.value = raw.slice(0, 4).map((p: any) => ({
      ...p,
      price: p.price_cny,
      price_unit: p.delivery_type === 'auto' ? '次' : '份',
      autoDeliver: p.delivery_type === 'auto',
    }))
  } catch {
    // featured products load silently; grid will just be empty
    featuredProducts.value = []
  }
  try {
    qrContents.value = await contentApi.qrs()
  } catch {
    qrContents.value = []
  }
})

const guideSteps = [
  {
    num: 1,
    title: '主站注册',
    detail: '先去主站注册账号',
    desc: '先在主站注册一个账号。没有主站账号，你买完以后也不知道去哪里兑换和使用。',
    link: 'https://xuedingtoken.com/register',
    linkText: 'xuedingtoken.com/register',
  },
  {
    num: 2,
    title: '商店下单',
    detail: '再来这个商店下单',
    desc: '在这个商店选择商品并付款。付款完成后，你会拿到兑换码。',
    link: '/products',
    linkText: '前往商店',
  },
  {
    num: 3,
    title: '主站兑换',
    detail: '最后回主站兑换并使用',
    desc: '登录主站，打开兑换页，把兑换码粘贴进去。兑换成功后，就在主站里使用 Token。',
    link: '/main/redeem',
    linkText: '前往兑换',
  },
]
</script>

<style scoped>
/* Hero */
.hero {
  background: linear-gradient(120deg, #1e1b4b 0%, #0f172a 100%);
  color: #fff;
  padding: 72px 0;
  text-align: center;
}
.hero-inner {
  max-width: 800px;
}
.hero-title {
  font-size: 38px;
  font-weight: 700;
  line-height: 1.25;
  margin-bottom: 28px;
  color: #fff;
  font-family: 'Playfair Display', serif;
}
.hero-accent {
  color: #818cf8;
}
.hero-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
}
.hero-link {
  color: rgba(255,255,255,0.7);
  font-size: 15px;
  transition: color 0.2s;
}
.hero-link:hover {
  color: #fff;
}

/* Guide */
.guide-section {
  padding: 64px 0;
  background: var(--color-bg-secondary);
}
.guide-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin: 32px 0 28px;
  flex-wrap: wrap;
}
.guide-step {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--color-bg);
  padding: 16px 20px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  min-width: 180px;
}
.guide-num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 15px;
  flex-shrink: 0;
}
.guide-text strong {
  display: block;
  font-size: 14px;
  color: var(--color-text);
  margin-bottom: 2px;
}
.guide-text p {
  font-size: 12px;
  color: var(--color-text-secondary);
}
.guide-arrow {
  font-size: 20px;
  color: var(--color-text-muted);
}
.guide-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 20px;
}

/* 展开的详细说明 */
.guide-detail {
  margin-top: 24px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}
.guide-detail-item {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border);
}
.guide-detail-item:last-child {
  border-bottom: none;
}
.guide-detail-num {
  width: 56px;
  min-width: 56px;
  background: var(--color-bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  color: var(--color-primary);
  border-right: 1px solid var(--color-border);
}
.guide-detail-body {
  padding: 20px 24px;
  flex: 1;
}
.guide-detail-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 8px;
}
.guide-detail-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin-bottom: 10px;
}
.guide-detail-link {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary);
  text-decoration: none;
}
.guide-detail-link:hover {
  text-decoration: underline;
}

/* Products */
.products-section {
  padding: 64px 0;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 28px;
}
.products-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

/* Community */
.community-section {
  padding: 64px 0;
  background: var(--color-bg-secondary);
}
.qr-sections {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  max-width: 600px;
  margin: 32px auto 0;
}
.qr-card {
  text-align: center;
}
.qr-placeholder-img {
  background: #f3f4f6;
  border-radius: var(--radius-md);
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  font-size: 40px;
  margin-bottom: 12px;
}
.qr-img {
  width: 80px;
  height: 80px;
  object-fit: contain;
  margin: 0 auto 10px;
  display: block;
}
.qr-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 4px;
}
.qr-desc {
  font-size: 11px;
  color: #888;
  margin-bottom: 8px;
}
.qr-link {
  font-size: 12px;
  color: var(--color-primary);
  text-decoration: none;
}
.qr-empty {
  opacity: 0.5;
}

/* News */
.news-section {
  padding: 64px 0;
}
.news-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}
.news-card {
  cursor: pointer;
  transition: all 0.2s;
}
.news-card:hover {
  border-color: var(--color-primary);
}
.news-date {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
}
.news-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 8px;
}
.news-excerpt {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* Welcome popup */
.popup-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.welcome-popup {
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  padding: 40px;
  max-width: 520px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
}
.popup-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-bg-secondary);
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}
.popup-close:hover {
  background: var(--color-border);
}
.popup-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 24px;
}
.popup-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--color-border);
}
.popup-section:last-of-type {
  border-bottom: none;
}
.popup-section h3 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--color-text);
}
.popup-section p,
.popup-section li {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.7;
}
.popup-section ul {
  list-style: none;
  padding: 0;
}
.popup-section ul li {
  margin-bottom: 8px;
  padding-left: 12px;
  position: relative;
}
.popup-section ul li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--color-primary);
}
.popup-notice {
  display: flex;
  gap: 12px;
  background: rgba(239,68,68,0.05);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 24px;
}
.notice-icon {
  font-size: 24px;
  flex-shrink: 0;
}
.popup-notice strong {
  color: var(--color-danger);
  font-size: 14px;
  display: block;
  margin-bottom: 4px;
}
.popup-gift {
  background: rgba(245,158,11,0.05);
  border: 1px solid rgba(245,158,11,0.2);
  border-radius: var(--radius-md);
  padding: 16px;
}
.popup-gift h3 {
  color: var(--color-warning);
}
.popup-gift p {
  color: var(--color-text);
  font-size: 14px;
}
.popup-qr-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.popup-qr-placeholder {
  background: #f3f4f6;
  border-radius: var(--radius-md);
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  font-size: 13px;
}
</style>
>
