<template>
  <div class="page-container">
    <h1 class="page-title">关于我们</h1>
    <div class="about-content">
      <p>{{ APP_BRAND_NAME }} 是一个面向开发者与团队的 AI API 中转、充值与订阅管理平台。</p>
      <p>如有问题，请联系：<strong>{{ SUPPORT_EMAIL }}</strong></p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { APP_BRAND_NAME, SUPPORT_EMAIL } from '@/constants/branding'
</script>

<style scoped>
.page-container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
.page-title { font-size: 24px; font-weight: 700; color: #1a1a2e; margin-bottom: 24px; }
.about-content { font-size: 15px; line-height: 1.8; color: #333; }
.about-content p { margin-bottom: 16px; }
</style>
