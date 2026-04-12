<template>
  <div class="main-layout">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <router-link to="/" class="sidebar-logo">{{ APP_BRAND_NAME }}</router-link>
        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          {{ sidebarCollapsed ? '→' : '←' }}
        </button>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          :class="{ 'router-link-active': isActive(item.to) }"
        >
          <span class="sidebar-icon">{{ item.icon }}</span>
          <span v-if="!sidebarCollapsed">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <button class="sidebar-link dark-mode-btn" @click="theme.toggle()">
          <span class="sidebar-icon">{{ theme.isDark ? '☀️' : '🌙' }}</span>
          <span v-if="!sidebarCollapsed">{{ theme.isDark ? '浅色模式' : '深色模式' }}</span>
        </button>
      </div>
    </aside>

    <div class="main-content">
      <header class="topbar">
        <div class="topbar-left">
          <h1 class="topbar-title">{{ title }}</h1>
          <p class="topbar-sub" v-if="subtitle">{{ subtitle }}</p>
        </div>
        <div class="topbar-right">
          <button class="btn btn-ghost topbar-btn" @click="openAnnouncementsModal()">📢 公告</button>
          <a href="/docs-center" class="btn btn-ghost topbar-btn">📖 文档</a>
          <span class="lang-btn">🇨🇳 中文</span>
          <div class="user-info">
            <span>HU</span>
            <span class="user-name">demo_user</span>
            <span class="dropdown-arrow">▼</span>
          </div>
        </div>
      </header>

      <main class="page-content">
        <slot />
      </main>

      <div v-if="showAnnModal" class="modal-mask" @click.self="showAnnModal = false">
        <div class="modal-box ann-modal">
          <h3 class="modal-title">公告</h3>
          <div v-if="announcements.length === 0" class="ann-empty">暂无公告</div>
          <div v-else v-for="a in announcements" :key="a.id" class="ann-item">
            <div class="ann-item-title">{{ a.title }}</div>
            <div class="ann-item-date">{{ a.published_at || a.created_at }}</div>
            <div class="ann-item-content">{{ a.content?.slice(0, 80) }}…</div>
          </div>
          <div class="modal-footer"><button class="btn-outline" @click="showAnnModal = false">关闭</button></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { contentApi } from '@/api/content'
import { APP_BRAND_NAME } from '@/constants/branding'

defineProps<{
  title: string
  subtitle?: string
}>()

const route = useRoute()
const theme = useThemeStore()
const sidebarCollapsed = ref(false)
const announcements = ref<any[]>([])
const showAnnModal = ref(false)

const navItems = [
  { to: '/main/dashboard', icon: '📊', label: '仪表盘' },
  { to: '/main/keys', icon: '🔑', label: 'API 密钥' },
  { to: '/main/playground', icon: '🧪', label: 'API 测试' },
  { to: '/main/client-install', icon: '🚀', label: '一键部署' },
  { to: '/orders', icon: '📋', label: '我的订单' },
  { to: '/products', icon: '💳', label: '购买套餐' },
  { to: '/main/redeem', icon: '🎁', label: '兑换' },
  { to: '/main/profile', icon: '👤', label: '账户中心' },
  { to: '/', icon: '🛍️', label: '逛商店' },
]

const isActive = (path: string) => route.path === path || route.path.startsWith(path + '/')

const loadAnn = async () => {
  try {
    announcements.value = await contentApi.announcements()
  } catch {
    announcements.value = []
  }
}

const openAnnouncementsModal = () => {
  showAnnModal.value = true
  loadAnn()
}
</script>

<style scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg-secondary);
  overflow-x: hidden;
}

.sidebar {
  width: 240px;
  background: var(--color-bg-dark);
  color: var(--color-nav-text);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 50;
  overflow: hidden;
}
.sidebar.collapsed {
  width: 68px;
}
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.sidebar-logo {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
}
.collapse-btn {
  background: rgba(255,255,255,0.1);
  border: none;
  color: rgba(255,255,255,0.7);
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: pointer;
  flex-shrink: 0;
}
.collapse-btn:hover {
  background: rgba(255,255,255,0.2);
  color: #fff;
}
.sidebar-nav {
  flex: 1;
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.sidebar-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  color: rgba(255,255,255,0.7);
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  white-space: nowrap;
  text-decoration: none;
}
.sidebar-link:hover,
.sidebar-link.router-link-active {
  background: rgba(255,255,255,0.1);
  color: #fff;
}
.sidebar-footer {
  padding: 12px 8px 16px;
  border-top: 1px solid rgba(255,255,255,0.1);
}
.dark-mode-btn {
  width: 100%;
  border: none;
  background: transparent;
  cursor: pointer;
}
.sidebar-icon {
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}
.main-content {
  flex: 1;
  margin-left: 240px;
  min-width: 0;
  transition: margin-left 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 28px;
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
}
.topbar-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
}
.topbar-sub {
  margin-top: 4px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.topbar-btn,
.lang-btn {
  font-size: 13px;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 999px;
  background: var(--color-bg-secondary);
  color: var(--color-text);
}
.user-name {
  font-size: 13px;
  font-weight: 600;
}
.dropdown-arrow {
  font-size: 10px;
  opacity: 0.6;
}
.page-content {
  padding: 28px;
}
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 100;
}
.modal-box {
  width: min(560px, 100%);
  background: var(--color-bg);
  border-radius: var(--radius-xl);
  padding: 24px;
  box-shadow: var(--shadow-xl);
}
.modal-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 16px;
}
.ann-empty {
  color: var(--color-text-secondary);
}
.ann-item + .ann-item {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border);
}
.ann-item-title {
  font-weight: 700;
  margin-bottom: 4px;
}
.ann-item-date,
.ann-item-content {
  color: var(--color-text-secondary);
  font-size: 13px;
}
.modal-footer {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}
.btn-outline {
  border: 1px solid var(--color-border);
  background: transparent;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  cursor: pointer;
}

@media (max-width: 960px) {
  .sidebar {
    position: static;
    width: 100%;
    height: auto;
    min-height: 0;
  }
  .sidebar.collapsed { width: 100%; }
  .sidebar-header {
    padding: 14px 16px;
  }
  .collapse-btn {
    display: none;
  }
  .sidebar-nav {
    flex-direction: row;
    overflow-x: auto;
    padding: 10px 12px;
    gap: 8px;
  }
  .sidebar-link {
    flex-shrink: 0;
    min-height: 42px;
    padding: 10px 14px;
  }
  .sidebar-footer {
    display: none;
  }
  .main-content {
    margin-left: 0;
  }
  .topbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 16px;
  }
  .topbar-right {
    width: 100%;
    flex-wrap: wrap;
    gap: 8px;
  }
  .user-info {
    max-width: 100%;
  }
  .page-content {
    padding: 16px;
  }
}

@media (max-width: 720px) {
  .sidebar-logo {
    font-size: 16px;
  }
  .topbar-title {
    font-size: 20px;
  }
  .topbar-sub {
    font-size: 12px;
  }
  .topbar-btn,
  .lang-btn {
    min-height: 40px;
  }
  .modal-mask {
    padding: 12px;
    align-items: flex-end;
  }
  .modal-box {
    padding: 18px;
    border-radius: 18px 18px 0 0;
    max-height: 86vh;
  }
}
</style>
