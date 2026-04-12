<template>
  <div class="help-page">
    <ShopNav />
    <div class="container">
      <h1 class="page-title">帮助中心</h1>
      <p class="page-desc">遇到问题？我们准备了以下入口，帮你快速找到答案。</p>

      <div class="help-grid">
        <router-link to="/main/profile" class="help-card">
          <div class="card-icon">👤</div>
          <div class="card-title">账户与安全</div>
          <div class="card-desc">修改密码、账户信息、安全设置</div>
        </router-link>

        <router-link to="/orders" class="help-card">
          <div class="card-icon">📋</div>
          <div class="card-title">充值与订单</div>
          <div class="card-desc">如何购买商品、支付流程、订单状态</div>
        </router-link>

        <router-link to="/main/keys" class="help-card">
          <div class="card-icon">🔑</div>
          <div class="card-title">API Keys</div>
          <div class="card-desc">创建 Key、使用方式、调用限制</div>
        </router-link>

        <router-link to="/docs-center" class="help-card">
          <div class="card-icon">📖</div>
          <div class="card-title">文档中心</div>
          <div class="card-desc">完整使用文档、API 参考、接入指南</div>
        </router-link>

        <router-link to="/faq" class="help-card">
          <div class="card-icon">❓</div>
          <div class="card-title">常见问题</div>
          <div class="card-desc">高频问题快速解答</div>
        </router-link>

        <router-link to="/auth/forgot-password" class="help-card">
          <div class="card-icon">🔒</div>
          <div class="card-title">忘记密码</div>
          <div class="card-desc">通过邮箱找回或重置密码</div>
        </router-link>
      </div>

      <div class="contact-section">
        <h2>没有找到答案？</h2>
        <p>你可以尝试浏览 <router-link to="/faq">常见问题</router-link> 或 <router-link to="/docs-center">文档中心</router-link></p>
        <p>也可以发送邮件至 <a href="mailto:support@demoplat.io">support@demoplat.io</a></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ShopNav from '@/components/shop/ShopNav.vue'
</script>

<style scoped>
.help-page { min-height: 100vh; background: #f5f5f7; }
.container { max-width: 900px; margin: 0 auto; padding: 40px 16px; }
.page-title { font-size: 28px; font-weight: 800; color: #1a1a2e; margin-bottom: 8px; }
.page-desc { font-size: 15px; color: #888; margin-bottom: 36px; }
.help-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; margin-bottom: 48px; }
.help-card { background: #fff; border-radius: 12px; padding: 24px; text-decoration: none; transition: box-shadow 0.2s, transform 0.2s; display: block; }
.help-card:hover { box-shadow: 0 6px 24px rgba(0,0,0,0.1); transform: translateY(-2px); }
.card-icon { font-size: 36px; margin-bottom: 12px; }
.card-title { font-size: 16px; font-weight: 700; color: #1a1a2e; margin-bottom: 6px; }
.card-desc { font-size: 13px; color: #888; line-height: 1.5; }
.contact-section { background: #fff; border-radius: 12px; padding: 28px; text-align: center; }
.contact-section h2 { font-size: 18px; font-weight: 700; color: #1a1a2e; margin-bottom: 12px; }
.contact-section p { font-size: 14px; color: #555; margin-bottom: 8px; }
.contact-section a { color: #aa3bff; text-decoration: none; }
</style>
