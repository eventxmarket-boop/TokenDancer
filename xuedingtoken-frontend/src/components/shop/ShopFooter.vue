<template>
  <footer class="shop-footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <div class="footer-logo">DemoPlatform</div>
          <p class="footer-tagline">让每一个人都能<br>享受到这个世界上最顶级模型的智能</p>
        </div>
        <div class="footer-col">
          <div class="footer-col-title">快速链接</div>
          <router-link to="/" class="footer-link">首页</router-link>
          <router-link to="/products" class="footer-link">商品中心</router-link>
          <router-link to="/announcements" class="footer-link">公告资讯</router-link>
          <router-link to="/about" class="footer-link">关于</router-link>
        </div>
        <div class="footer-col">
          <div class="footer-col-title">联系我们</div>
          <p class="footer-contact">邮箱: support@demo-platform.com</p>
        </div>
        <div class="footer-col">
          <div class="footer-col-title">法律信息</div>
          <router-link to="/privacy" class="footer-link">隐私政策</router-link>
          <router-link to="/terms" class="footer-link">服务条款</router-link>
        </div>
      </div>
      <div class="footer-bottom">
        <p class="copyright">© 2026 DemoPlatform. All rights reserved.</p>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.shop-footer {
  background: var(--color-bg-secondary);
  border-top: 1px solid var(--color-border);
  padding: 48px 0 24px;
  margin-top: 80px;
}
.footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 48px;
  margin-bottom: 40px;
}
.footer-logo {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 12px;
}
.footer-tagline {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.7;
}
.footer-col-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 16px;
}
.footer-link {
  display: block;
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
  transition: color 0.2s;
}
.footer-link:hover {
  color: var(--color-primary);
}
.footer-contact {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}
.footer-bottom {
  border-top: 1px solid var(--color-border);
  padding-top: 24px;
  text-align: center;
}
.copyright {
  font-size: 13px;
  color: var(--color-text-muted);
}
</style>
