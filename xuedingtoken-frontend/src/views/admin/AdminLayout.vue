<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="sidebar-header">
        <h2>⚙️ 学代管理后台</h2>
        <span class="version-badge">{{ APP_VERSION }}</span>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-group">
          <router-link to="/admin/dashboard" class="nav-item" exact-active-class="nav-item-active">
            📊 总览
          </router-link>
        </div>

        <div class="nav-group">
          <div class="nav-group-label">运营管理</div>
          <router-link to="/admin/users" class="nav-item" active-class="nav-item-active">👥 用户管理</router-link>
          <router-link to="/admin/orders" class="nav-item" active-class="nav-item-active">🧾 订单管理</router-link>
          <router-link to="/admin/redeem-codes" class="nav-item" active-class="nav-item-active">🎫 兑换码</router-link>
          <router-link to="/admin/products" class="nav-item" active-class="nav-item-active">📦 商品管理</router-link>
        </div>

        <div class="nav-group">
          <div class="nav-group-label">财务与用量</div>
          <router-link to="/admin/finance/overview" class="nav-item" active-class="nav-item-active">📊 财务总览</router-link>
          <router-link to="/admin/payment-config" class="nav-item sub" active-class="nav-item-active">⚙️ 支付配置</router-link>
          <router-link to="/admin/finance/ledger" class="nav-item sub" active-class="nav-item-active">📒 余额账本</router-link>
          <router-link to="/admin/finance/usage" class="nav-item sub" active-class="nav-item-active">📈 Usage 明细</router-link>
        </div>

        <div class="nav-group">
          <div class="nav-group-label">内容管理</div>
          <router-link to="/admin/content/announcements" class="nav-item" active-class="nav-item-active">📋 公告管理</router-link>
          <router-link to="/admin/content/privacy" class="nav-item" active-class="nav-item-active">🔒 隐私政策</router-link>
          <router-link to="/admin/content/terms" class="nav-item" active-class="nav-item-active">📄 服务条款</router-link>
          <router-link to="/admin/content/qr-contents" class="nav-item" active-class="nav-item-active">📷 二维码内容</router-link>
          <router-link to="/admin/content/pages" class="nav-item" active-class="nav-item-active">📝 页面内容</router-link>
        </div>

        <div class="nav-group">
          <div class="nav-group-label">API 中转管理</div>
          <router-link to="/admin/api-proxy/providers" class="nav-item sub" active-class="nav-item-active">🌐 渠道管理</router-link>
          <router-link to="/admin/api-proxy/provider-keys" class="nav-item sub" active-class="nav-item-active">🔑 源 Key 池</router-link>
          <router-link to="/admin/api-proxy/model-routes" class="nav-item sub" active-class="nav-item-active">🔀 模型映射</router-link>
          <router-link to="/admin/api-proxy/route-policies" class="nav-item sub" active-class="nav-item-active">⚙️ 路由策略</router-link>
          <router-link to="/admin/api-proxy/monitor" class="nav-item sub" active-class="nav-item-active">📡 中转监控</router-link>
          <router-link to="/admin/api-proxy/proxy-logs" class="nav-item sub" active-class="nav-item-active">📋 请求日志</router-link>
        </div>

        <div class="nav-group">
          <div class="nav-group-label">系统状态</div>
          <router-link to="/admin/system/overview" class="nav-item sub" active-class="nav-item-active">📊 系统总览</router-link>
          <router-link to="/admin/system/provider-health" class="nav-item sub" active-class="nav-item-active">🌐 Provider 健康</router-link>
          <router-link to="/admin/system/key-status" class="nav-item sub" active-class="nav-item-active">🔑 Source Key 状态</router-link>
          <router-link to="/admin/system/routing-status" class="nav-item sub" active-class="nav-item-active">🔀 路由配置状态</router-link>
          <router-link to="/admin/system/payment-events" class="nav-item sub" active-class="nav-item-active">🧾 支付事件</router-link>
          <router-link to="/admin/system/proxy-runtime" class="nav-item sub" active-class="nav-item-active">📡 Proxy 运行状态</router-link>
        </div>

        <div class="nav-group">
          <div class="nav-group-label">系统</div>
          <router-link to="/admin/audit-logs" class="nav-item sub" active-class="nav-item-active">📋 审计日志</router-link>
          <span class="nav-item nav-item-disabled">🔧 系统配置</span>
        </div>

        <div class="nav-divider"></div>
        <router-link to="/" class="nav-item">← 返回商城</router-link>
      </nav>
    </aside>

    <div class="admin-right">
      <header class="admin-topbar">
        <div class="topbar-breadcrumb">
          <span class="breadcrumb-root">后台管理</span>
          <span v-if="currentTitle" class="breadcrumb-sep"> / </span>
          <span v-if="currentTitle" class="breadcrumb-current">{{ currentTitle }}</span>
        </div>

        <div class="topbar-user">
          <span class="user-info">
            <span class="user-name">{{ authStore.user?.username || authStore.user?.email }}</span>
            <span :class="['user-role-badge', authStore.user?.role === 'admin' ? 'badge-admin' : 'badge-user']">
              {{ authStore.user?.role === 'admin' ? '管理员' : '用户' }}
            </span>
          </span>
          <button class="btn-logout" @click="handleLogout">退出</button>
        </div>
      </header>

      <main class="admin-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { APP_VERSION } from '@/constants/appVersion'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const routeTitleMap: Record<string, string> = {
  'admin-dashboard': '总览',
  'admin-users': '用户管理',
  'admin-orders': '订单管理',
  'admin-redeem-codes': '兑换码管理',
  'admin-products': '商品管理',
  'admin-providers': '渠道管理',
  'admin-provider-keys': '源 Key 池',
  'admin-model-routes': '模型映射',
  'admin-route-policies': '路由策略',
  'admin-proxy-monitor': 'API 中转监控',
  'admin-proxy-logs': '请求日志',
  'admin-finance-overview': '财务总览',
  'admin-finance-ledger': '余额账本',
  'admin-finance-usage': 'Usage 明细',
  'admin-content-announcements': '公告管理',
  'admin-content-qr-contents': '二维码内容',
  'admin-content-privacy': '隐私政策',
  'admin-content-terms': '服务条款',
  'admin-content-pages': '页面内容',
  'admin-system-overview': '系统总览',
  'admin-audit-logs': '审计日志',
  'admin-system-provider-health': 'Provider 健康',
  'admin-system-key-status': 'Source Key 状态',
  'admin-system-routing-status': '路由配置状态',
  'admin-system-payment-events': '支付事件',
  'admin-system-proxy-runtime': 'Proxy 运行状态',
  'admin-payment-config': '支付配置',
}

const currentTitle = computed(() => routeTitleMap[String(route.name)] || '')

const handleLogout = () => {
  authStore.logout()
  router.push('/auth/login')
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: #f0f2f5;
}
.admin-sidebar {
  width: 220px;
  height: 100vh;
  overflow: hidden;
  background: #1a1a2e;
  color: #fff;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  padding: 20px 20px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.sidebar-header h2 {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  margin: 0;
}
.version-badge {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.3px;
  color: #f8fafc;
  background: linear-gradient(135deg, rgba(22,119,255,0.9), rgba(56,189,248,0.85));
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.18);
}
.sidebar-nav {
  flex: 1;
  min-height: 0;
  padding: 12px 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-group {
  margin-bottom: 4px;
}
.nav-group-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: rgba(255,255,255,0.3);
  padding: 12px 16px 4px;
  margin-top: 4px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 16px;
  font-size: 13.5px;
  color: rgba(255,255,255,0.65);
  text-decoration: none;
  border-radius: 6px;
  margin: 0 8px;
  transition: all 0.15s;
  cursor: pointer;
}
.nav-item:hover:not(.nav-item-disabled) {
  background: rgba(255,255,255,0.08);
  color: #fff;
}
.nav-item-active {
  background: rgba(255,255,255,0.12) !important;
  color: #fff !important;
  font-weight: 600;
}
.nav-item-disabled {
  opacity: 0.35;
  cursor: default;
}
.nav-item.sub {
  padding-left: 28px;
  font-size: 13px;
}
.nav-divider {
  height: 1px;
  background: rgba(255,255,255,0.08);
  margin: 8px 16px;
}
.admin-right {
  flex: 1;
  min-width: 0;
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.admin-topbar {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  flex-shrink: 0;
}
.topbar-breadcrumb {
  font-size: 14px;
  color: #666;
}
.breadcrumb-root { color: #999; }
.breadcrumb-sep { margin: 0 4px; color: #ccc; }
.breadcrumb-current { color: #333; font-weight: 600; }
.topbar-user {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-name { font-size: 13px; color: #333; }
.user-role-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
}
.badge-admin { background: #fff7e6; color: #d46b08; }
.badge-user { background: #f5f5f5; color: #666; }
.btn-logout {
  background: #fff;
  border: 1px solid #d9d9d9;
  color: #333;
  border-radius: 6px;
  padding: 6px 12px;
  cursor: pointer;
}
.admin-main {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 24px;
}
</style>
