<template>
  <nav class="shop-nav">
    <div class="container shop-nav-inner">
      <div class="shop-nav-left">
        <router-link to="/" class="shop-logo">{{ APP_BRAND_NAME }}</router-link>
        <div class="shop-nav-links">
          <router-link to="/" class="nav-link">首页</router-link>
          <router-link to="/products" class="nav-link">商品</router-link>
          <button class="nav-link" @click="showAnnModal = true; loadAnnouncements()">公告</button>
        </div>
      </div>
      <div class="shop-nav-right">
        <router-link to="/cart" class="cart-btn">
          <span class="cart-icon">🛒</span>
          <span v-if="cartCount > 0" class="cart-badge">{{ cartCount }}</span>
        </router-link>
        <router-link to="/auth/login" class="user-btn">👤</router-link>
        <router-link to="/main/dashboard" class="main-station-btn">控制台</router-link>
        <button class="lang-btn">简</button>
      </div>
    </div>
  </nav>

  <!-- 公告弹窗 -->
  <div v-if="showAnnModal" class="modal-mask" @click.self="showAnnModal = false">
    <div class="modal-box ann-modal">
      <h3 class="modal-title">公告</h3>
      <div v-if="announcements.length === 0" class="ann-empty">暂无公告</div>
      <div v-else v-for="a in announcements" :key="a.id" class="ann-item">
        <div class="ann-item-title">{{ a.title }}</div>
        <div class="ann-item-date">{{ fmtDate(a.published_at || a.created_at) }}</div>
        <div class="ann-item-content">{{ a.content?.slice(0, 100) }}…</div>
      </div>
      <div class="modal-footer"><button class="btn-outline" @click="showAnnModal = false">关闭</button></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useCartStore } from '@/stores/cart'
import { contentApi } from '@/api/content'
import { APP_BRAND_NAME } from '@/constants/branding'

const cartStore = useCartStore()
const cartCount = cartStore.totalItems

const announcements = ref<any[]>([])
const showAnnModal = ref(false)

const loadAnnouncements = async () => {
  try { announcements.value = await contentApi.announcements() }
  catch { announcements.value = [] }
}

const fmtDate = (d: string) => d ? new Date(d).toLocaleString('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) : '—'
</script>

<style scoped>
.shop-nav {
  background: var(--color-nav-bg);
  color: var(--color-nav-text);
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 100;
}
.shop-nav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 56px;
  gap: 16px;
  padding-top: 10px;
  padding-bottom: 10px;
}
.shop-nav-left {
  display: flex;
  align-items: center;
  gap: 40px;
}
.shop-logo {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}
.shop-nav-links {
  display: flex;
  gap: 32px;
}
.nav-link {
  color: rgba(255,255,255,0.8);
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s;
}
.nav-link:hover,
.nav-link.router-link-active {
  color: #fff;
}
.shop-nav-right {
  display: flex;
  align-items: center;
  gap: 20px;
}
.cart-btn {
  position: relative;
  font-size: 20px;
  color: rgba(255,255,255,0.8);
  transition: color 0.2s;
}
.cart-btn:hover {
  color: #fff;
}
.cart-badge {
  position: absolute;
  top: -6px;
  right: -10px;
  background: var(--color-primary);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.user-btn {
  font-size: 18px;
  color: rgba(255,255,255,0.8);
  transition: color 0.2s;
}
.user-btn:hover {
  color: #fff;
}
.lang-btn {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  color: rgba(255,255,255,0.8);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.lang-btn:hover {
  background: rgba(255,255,255,0.2);
  color: #fff;
}
.main-station-btn {
  background: var(--color-primary);
  color: #fff;
  padding: 5px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  transition: background 0.2s;
}
.main-station-btn:hover {
  background: var(--color-primary-dark);
  color: #fff;
}
.admin-btn {
  background: #1677ff;
  color: #fff;
}
.admin-btn:hover {
  background: #4096ff;
  color: #fff;
}
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:1000; }
.modal-box { background:#fff; border-radius:12px; padding:28px; }
.ann-modal { width:480px; max-width:90vw; max-height:70vh; overflow-y:auto; }
.ann-empty { text-align:center; padding:40px; color:#888; }
.ann-item { padding:12px 0; border-bottom:1px solid #f0f0f0; }
.ann-item:last-of-type { border-bottom:none; }
.ann-item-title { font-size:14px; font-weight:600; color:#1a1a2e; margin-bottom:4px; }
.ann-item-date { font-size:11px; color:#999; margin-bottom:6px; }
.ann-item-content { font-size:13px; color:#666; }
.modal-footer { display:flex; justify-content:flex-end; margin-top:16px; }
.btn-outline { padding:8px 18px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:8px; cursor:pointer; }

@media (max-width: 860px) {
  .shop-nav-inner {
    flex-direction: column;
    align-items: stretch;
    justify-content: center;
  }
  .shop-nav-left,
  .shop-nav-right {
    width: 100%;
    justify-content: space-between;
  }
  .shop-nav-left {
    gap: 16px;
    flex-wrap: wrap;
  }
  .shop-nav-links {
    gap: 10px;
    flex: 1;
    min-width: 0;
    overflow-x: auto;
    padding-bottom: 4px;
  }
  .nav-link {
    white-space: nowrap;
    min-height: 40px;
    display: inline-flex;
    align-items: center;
  }
  .shop-nav-right {
    gap: 10px;
    flex-wrap: wrap;
  }
  .main-station-btn,
  .lang-btn,
  .user-btn,
  .cart-btn {
    min-height: 40px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}

@media (max-width: 520px) {
  .shop-logo {
    font-size: 18px;
  }
  .shop-nav-left,
  .shop-nav-right {
    flex-direction: row;
    align-items: center;
  }
  .main-station-btn {
    flex: 1;
  }
  .modal-mask {
    padding: 12px;
  }
  .ann-modal {
    width: 100%;
    max-width: none;
    max-height: 82vh;
  }
}
</style>
