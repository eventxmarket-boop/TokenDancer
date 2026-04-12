<template>
  <div class="page-container">
    <h1 class="page-title">📖 帮助与文档</h1>
    <div class="doc-list">
      <div class="doc-section">
        <h2 class="doc-section-title">🤖 API Key 使用说明</h2>
        <div class="doc-content">
          <p>1. 在后台「API中转 → 源Key池」中添加您的模型提供方 API Key。</p>
          <p>2. 系统会对 Key 进行加密存储，不会以明文形式展示。</p>
          <p>3. 在「模型映射」中配置公开模型名与实际 Provider 模型名的对应关系。</p>
          <p>4. 在「路由策略」中配置请求如何分发到不同的 Provider。</p>
        </div>
      </div>
      <div class="doc-section">
        <h2 class="doc-section-title">💻 ClientInstall 使用说明</h2>
        <div class="doc-content">
          <p>1. 安装客户端后，在 Key 管理页面创建您的个人 API Key。</p>
          <p>2. 复制生成的 Key，并在客户端中配置请求代理地址为本平台中转地址。</p>
          <p>3. 客户端将自动通过本平台进行请求路由与计费。</p>
          <p>4. 您可以在使用统计中查看各模型的调用情况与费用明细。</p>
        </div>
      </div>
      <div class="doc-section">
        <h2 class="doc-section-title">💰 充值与兑换说明</h2>
        <div class="doc-content">
          <p>1. 在「商品中心」购买 Token 套餐，或使用兑换码充值。</p>
          <p>2. 兑换码由管理员生成，可在「我的订单」中查看。</p>
          <p>3. 充值后余额将即时到账，可用于所有按量计费场景。</p>
          <p>4. 如有充值问题，请通过公告中公示的方式联系管理员。</p>
        </div>
      </div>
      <div class="doc-section">
        <h2 class="doc-section-title">❓ 常见问题</h2>
        <div class="doc-content">
          <details class="faq-item"><summary>Q: 请求失败怎么解决？</summary><p>A: 请检查 API Key 是否有效，以及余额是否充足。如问题持续，请联系管理员。</p></details>
          <details class="faq-item"><summary>Q: 如何修改密码？</summary><p>A: 当前版本请联系管理员重置密码。</p></details>
          <details class="faq-item"><summary>Q: 兑换码过期了怎么办？</summary><p>A: 兑换码有效期由管理员设置，过期后无法使用，请联系管理员处理。</p></details>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.page-container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
.page-title { font-size: 24px; font-weight: 700; color: #1a1a2e; margin-bottom: 32px; }
.doc-list { display: flex; flex-direction: column; gap: 24px; }
.doc-section { background: #fff; border: 1px solid #f0f0f0; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.doc-section-title { font-size: 16px; font-weight: 700; color: #1a1a2e; margin-bottom: 16px; }
.doc-content p { font-size: 14px; color: #555; line-height: 1.8; margin-bottom: 8px; }
.faq-item { margin-bottom: 8px; }
.faq-item summary { font-size: 14px; font-weight: 600; color: #1a1a2e; cursor: pointer; padding: 6px 0; }
.faq-item p { font-size: 13px; color: #666; margin-top: 6px; padding-left: 16px; }
</style>
