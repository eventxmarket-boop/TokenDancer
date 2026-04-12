<template>
  <div class="faq-page">
    <ShopNav />
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">常见问题</h1>
        <p class="page-desc">以下是用户最常问到的问题，点击展开查看答案。</p>
      </div>

      <div class="faq-sections">
        <div v-for="section in faqData" :key="section.title" class="faq-section">
          <h2 class="section-title">{{ section.title }}</h2>
          <div class="faq-list">
            <div v-for="(item, idx) in section.items" :key="idx" class="faq-item">
              <button class="faq-q" @click="toggle(idx)">
                <span>{{ item.q }}</span>
                <span class="faq-arrow" :class="{ open: openIdx === idx }">▼</span>
              </button>
              <div v-if="openIdx === idx" class="faq-a">{{ item.a }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="faq-contact">
        <p>没找到答案？</p>
        <router-link to="/help" class="btn-outline-sm">前往帮助中心</router-link>
        <a href="mailto:support@demoplat.io" class="btn-outline-sm">联系支持</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ShopNav from '@/components/shop/ShopNav.vue'

const openIdx = ref<number | null>(null)
const toggle = (i: number) => { openIdx.value = openIdx.value === i ? null : i }

const faqData = [
  {
    title: '账户与安全',
    items: [
      { q: '如何修改密码？', a: '登录后进入"账户中心"，点击"安全设置"中的"修改密码"即可。' },
      { q: '忘记密码怎么办？', a: '点击登录页的"忘记密码"，输入注册邮箱，我们会发送重置指引。' },
      { q: '如何联系支持？', a: '发送邮件至 support@demoplat.io，或前往"帮助中心"了解更多。' },
    ]
  },
  {
    title: '充值与购买',
    items: [
      { q: '如何购买商品？', a: '在"商品中心"选择商品，点击购买并加入购物车，然后结算下单。' },
      { q: '支付成功后多久到账？', a: '支付成功后，权益（余额/订阅/Token配额）通常在数秒内自动到账。' },
      { q: '支持哪些支付方式？', a: '当前支持 Stripe（银行卡）、支付宝、微信支付。' },
      { q: '订单可以取消吗？', a: '已支付的订单无法自行取消，请联系管理员处理。' },
    ]
  },
  {
    title: '订阅与权益',
    items: [
      { q: '如何查看我的订阅？', a: '登录后进入"我的订阅"页面，可以查看当前生效的订阅及历史记录。' },
      { q: 'Token 包是什么？', a: 'Token 包是预付费的 API 调用配额，购买后可在用量中心查看剩余额度。' },
      { q: '余额可以提现吗？', a: '目前余额不支持提现，仅用于后续消费。' },
    ]
  },
  {
    title: 'API Keys',
    items: [
      { q: '如何创建 API Key？', a: '在"控制台 → API Keys"页面，点击"新建 Key"即可。' },
      { q: 'API Key 泄露了怎么办？', a: '请立即在 API Keys 页面删除该 Key，并创建新的 Key。' },
    ]
  },
  {
    title: '其他',
    items: [
      { q: '如何获取发票？', a: '如有发票需求，请联系 support@demoplat.io。' },
      { q: '服务条款和隐私政策在哪里？', a: '可以在页面底部的"服务条款"和"隐私政策"链接查看。' },
    ]
  }
]
</script>

<style scoped>
.faq-page { min-height: 100vh; background: #f5f5f7; }
.container { max-width: 760px; margin: 0 auto; padding: 40px 16px; }
.page-header { margin-bottom: 36px; }
.page-title { font-size: 28px; font-weight: 800; color: #1a1a2e; margin-bottom: 8px; }
.page-desc { font-size: 15px; color: #888; }
.faq-sections { display: flex; flex-direction: column; gap: 28px; margin-bottom: 40px; }
.faq-section { background: #fff; border-radius: 12px; padding: 24px; }
.section-title { font-size: 16px; font-weight: 700; color: #1a1a2e; margin-bottom: 16px; }
.faq-list { display: flex; flex-direction: column; gap: 4px; }
.faq-item { border-radius: 8px; overflow: hidden; }
.faq-q { width: 100%; display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #f9f9fb; border: none; cursor: pointer; font-size: 14px; font-weight: 600; color: #333; text-align: left; gap: 12px; transition: background 0.2s; }
.faq-q:hover { background: #f0f0f5; }
.faq-arrow { font-size: 10px; color: #aaa; transition: transform 0.2s; flex-shrink: 0; }
.faq-arrow.open { transform: rotate(180deg); }
.faq-a { padding: 12px 16px; font-size: 14px; color: #555; line-height: 1.7; background: #fff; border-top: 1px solid #f0f0f0; }
.faq-contact { text-align: center; font-size: 14px; color: #888; display: flex; gap: 12px; justify-content: center; align-items: center; flex-wrap: wrap; }
.faq-contact p { width: 100%; margin-bottom: 4px; }
.btn-outline-sm { padding: 6px 14px; border: 1px solid #aa3bff; color: #aa3bff; border-radius: 6px; text-decoration: none; font-size: 13px; }
</style>
