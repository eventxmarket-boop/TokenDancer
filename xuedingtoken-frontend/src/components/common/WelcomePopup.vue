<template>
  <Teleport to="body">
    <div v-if="show" class="popup-overlay" @click.self="close">
      <div class="popup-box card">
        <div class="popup-header">
          <h2>欢迎使用 {{ APP_BRAND_NAME }}</h2>
          <button class="btn btn-ghost" @click="close">✕</button>
        </div>
        <div class="popup-body">
          <p class="popup-red">⚠️ 发货说明：兑换码需在"兑换"页面兑换后使用，并非API Key</p>
          <div class="popup-section">
            <h4>🎁 新人礼包</h4>
            <p>新用户默认享有 $5 体验券<br>1元人民币即可体验</p>
          </div>
          <div class="popup-section">
            <h4>📋 购买须知</h4>
            <p>退款时效：下单后1天内可申请退款<br>计算公式：退款金额 = 实付金额 - 已消耗算力 - 平台服务费(20%)</p>
          </div>
          <div class="popup-section">
            <h4>📞 联系我们</h4>
            <p>客服微信：support123</p>
          </div>
        </div>
        <div class="popup-footer">
          <button class="btn btn-primary w-full" @click="close">我知道了</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { APP_BRAND_NAME } from '@/constants/branding'
const show = ref(false)
const close = () => {
  show.value = false
  sessionStorage.setItem('welcome_shown', '1')
}
onMounted(() => {
  if (!sessionStorage.getItem('welcome_shown')) {
    show.value = true
  }
})
</script>

<style scoped>
.popup-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.6);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.popup-box { width: 480px; max-width: 90vw; }
.popup-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.popup-header h2 { font-size: 18px; }
.popup-body { margin-bottom: 16px; }
.popup-red { color: #EF4444; font-weight: 600; margin-bottom: 12px; }
.popup-section { margin-bottom: 12px; }
.popup-section h4 { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
.popup-section p { font-size: 13px; color: #6B7280; line-height: 1.6; }
.popup-footer { border-top: 1px solid #E5E7EB; padding-top: 16px; }
</style>
