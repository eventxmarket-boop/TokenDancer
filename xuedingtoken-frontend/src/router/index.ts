import { createRouter, createWebHistory } from 'vue-router'
import { ADMIN_PANEL_NAME, APP_BRAND_NAME, CONSOLE_BRAND_NAME } from '@/constants/branding'

import ShopHome from '../views/shop/ShopHome.vue'
import ProductList from '../views/shop/ProductList.vue'
import ProductDetail from '../views/shop/ProductDetail.vue'
import Cart from '../views/shop/Cart.vue'
import Login from '../views/shop/Login.vue'
import Register from '../views/shop/Register.vue'

import Dashboard from '../views/main/Dashboard.vue'
import Redeem from '../views/main/Redeem.vue'
import Keys from '../views/main/Keys.vue'
import Usage from '../views/main/Usage.vue'
import Profile from '../views/main/Profile.vue'
import ClientInstall from '../views/main/ClientInstall.vue'

import AdminLayout from '../views/admin/AdminLayout.vue'
import AdminDashboard from '../views/admin/AdminDashboard.vue'
import AdminUsers from '../views/admin/AdminUsers.vue'
import AdminOrders from '../views/admin/AdminOrders.vue'
import AdminRedeemCodes from '../views/admin/AdminRedeemCodes.vue'
import AdminProducts from '../views/admin/AdminProducts.vue'
import AdminProviders from '../views/admin/AdminProviders.vue'
import AdminProviderKeys from '../views/admin/AdminProviderKeys.vue'
import AdminModelRoutes from '../views/admin/AdminModelRoutes.vue'
import AdminRoutePolicies from '../views/admin/AdminRoutePolicies.vue'
import AdminProxyLogs from '../views/admin/AdminProxyLogs.vue'

const adminRoutes = [
  { path: '', redirect: '/admin/dashboard' },
  { path: 'dashboard', component: AdminDashboard, name: 'admin-dashboard' },
  { path: 'users', component: AdminUsers, name: 'admin-users' },
  { path: 'orders', component: AdminOrders, name: 'admin-orders' },
  { path: 'redeem-codes', component: AdminRedeemCodes, name: 'admin-redeem-codes' },
  { path: 'products', component: AdminProducts, name: 'admin-products' },
  { path: 'finance/overview', component: () => import('@/views/admin/AdminFinanceOverview.vue'), name: 'admin-finance-overview' },
  { path: 'finance/ledger', component: () => import('@/views/admin/AdminLedger.vue'), name: 'admin-finance-ledger' },
  { path: 'finance/usage', component: () => import('@/views/admin/AdminUsageRecords.vue'), name: 'admin-finance-usage' },
  { path: 'api-proxy/providers', component: AdminProviders, name: 'admin-providers' },
  { path: 'api-proxy/provider-keys', component: AdminProviderKeys, name: 'admin-provider-keys' },
  { path: 'api-proxy/model-routes', component: AdminModelRoutes, name: 'admin-model-routes' },
  { path: 'api-proxy/route-policies', component: AdminRoutePolicies, name: 'admin-route-policies' },
  { path: 'api-proxy/tester', component: () => import('@/views/admin/AdminProxyTester.vue'), name: 'admin-proxy-tester' },
  { path: 'api-proxy/monitor', component: () => import('@/views/admin/AdminProxyMonitor.vue'), name: 'admin-proxy-monitor' },
  { path: 'api-proxy/proxy-logs', component: AdminProxyLogs, name: 'admin-proxy-logs' },
  { path: 'content/announcements', component: () => import('@/views/admin/AdminAnnouncements.vue') },
  { path: 'content/qr-contents', component: () => import('@/views/admin/AdminQrContents.vue') },
  { path: 'content/privacy', component: () => import('@/views/admin/AdminPolicyPrivacy.vue') },
  { path: 'content/terms', component: () => import('@/views/admin/AdminPolicyTerms.vue') },
  { path: 'content/pages', component: () => import('@/views/admin/AdminContentPages.vue') },
  { path: 'system/overview', component: () => import('@/views/admin/AdminSystemOverview.vue'), name: 'admin-system-overview' },
  { path: 'system/provider-health', component: () => import('@/views/admin/AdminProviderHealth.vue'), name: 'admin-system-provider-health' },
  { path: 'system/key-status', component: () => import('@/views/admin/AdminProviderKeyStatus.vue'), name: 'admin-system-key-status' },
  { path: 'system/routing-status', component: () => import('@/views/admin/AdminRoutingStatus.vue'), name: 'admin-system-routing-status' },
  { path: 'system/payment-events', component: () => import('@/views/admin/AdminPaymentEvents.vue'), name: 'admin-system-payment-events' },
  { path: 'system/proxy-runtime', component: () => import('@/views/admin/AdminProxyRuntime.vue'), name: 'admin-system-proxy-runtime' },
  { path: 'audit-logs', component: () => import('@/views/admin/AdminAuditLogs.vue'), name: 'admin-audit-logs' },
  { path: 'payment-config', component: () => import('@/views/admin/AdminPaymentConfig.vue'), name: 'admin-payment-config' },
]

const routes = [
  { path: '/', component: ShopHome, name: 'shop-home' },
  { path: '/products', component: ProductList, name: 'products' },
  { path: '/products/:id', component: ProductDetail, name: 'product-detail' },
  { path: '/cart', component: Cart, name: 'cart' },
  {
    path: '/checkout/:orderId',
    component: () => import('@/views/shop/CheckoutPage.vue'),
    name: 'checkout',
    meta: { requiresAuth: true },
  },
  {
    path: '/orders',
    component: () => import('@/views/shop/OrdersPage.vue'),
    name: 'orders',
    meta: { requiresAuth: true },
  },
  { path: '/shop/alipay-qr', component: () => import('@/views/shop/AlipayQrPage.vue'), name: 'alipay-qr', meta: { requiresAuth: true } },
  { path: '/auth/login', component: Login, name: 'login' },
  { path: '/auth/register', component: Register, name: 'register' },
  { path: '/auth/forgot-password', component: () => import('@/views/shop/ForgotPasswordPage.vue'), name: 'forgot-password' },

  { path: '/main/dashboard', component: Dashboard, name: 'dashboard', meta: { requiresAuth: true } },
  { path: '/main/redeem', component: Redeem, name: 'redeem', meta: { requiresAuth: true } },
  { path: '/main/keys', component: Keys, name: 'keys', meta: { requiresAuth: true } },
  { path: '/main/usage', component: Usage, name: 'usage', meta: { requiresAuth: true } },
  { path: '/main/profile', component: Profile, name: 'profile', meta: { requiresAuth: true } },
  { path: '/main/client-install', component: ClientInstall, name: 'client-install', meta: { requiresAuth: true } },
  { path: '/main/subscriptions', component: () => import('@/views/main/SubscriptionsPage.vue'), name: 'subscriptions', meta: { requiresAuth: true } },
  { path: '/main/billing', component: () => import('@/views/main/BillingPage.vue'), name: 'billing', meta: { requiresAuth: true } },
  { path: '/main/playground', component: () => import('../views/main/ProxyPlayground.vue'), name: 'ProxyPlayground', meta: { requiresAuth: true } },
  { path: '/about', component: () => import('@/views/public/AboutPage.vue') },
  { path: '/privacy', component: () => import('@/views/public/PrivacyPage.vue') },
  { path: '/terms', component: () => import('@/views/public/TermsPage.vue') },
  { path: '/announcements', component: () => import('@/views/public/AnnouncementsPage.vue') },
  { path: '/docs-center', component: () => import('@/views/public/DocsCenterPage.vue') },
  { path: '/help', component: () => import('@/views/public/HelpCenterPage.vue'), name: 'help' },
  { path: '/faq', component: () => import('@/views/public/FaqPage.vue'), name: 'faq' },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: adminRoutes,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() { return { top: 0 } },
})

const routeTitleMap: Record<string, string> = {
  'shop-home': APP_BRAND_NAME,
  products: '商品中心',
  'product-detail': '商品详情',
  cart: '购物车',
  checkout: '结算',
  orders: '我的订单',
  login: '登录',
  register: '注册',
  'forgot-password': '找回密码',
  dashboard: '控制台总览',
  redeem: '兑换中心',
  keys: 'API 密钥',
  usage: '用量记录',
  profile: '账户中心',
  'client-install': '一键部署',
  subscriptions: '订阅中心',
  billing: '账务中心',
  ProxyPlayground: 'API Playground',
  'admin-dashboard': '后台总览',
  'admin-users': '用户管理',
  'admin-orders': '订单管理',
  'admin-redeem-codes': '兑换码管理',
  'admin-products': '商品管理',
  'admin-finance-overview': '财务总览',
  'admin-finance-ledger': '余额账本',
  'admin-finance-usage': 'Usage 明细',
  'admin-providers': '渠道管理',
  'admin-provider-keys': '源 Key 池',
  'admin-model-routes': '模型映射',
  'admin-route-policies': '路由策略',
  'admin-proxy-tester': 'API 测试工作台',
  'admin-proxy-monitor': 'API 中转监控',
  'admin-proxy-logs': '请求日志',
  'admin-system-overview': '系统总览',
  'admin-system-provider-health': 'Provider 健康',
  'admin-system-key-status': 'Source Key 状态',
  'admin-system-routing-status': '路由配置状态',
  'admin-system-payment-events': '支付事件',
  'admin-system-proxy-runtime': 'Proxy 运行状态',
  'admin-audit-logs': '审计日志',
  'admin-payment-config': '支付配置',
}

router.beforeEach(async (to: any) => {
  const { useAuthStore } = await import('@/stores/auth')
  const auth = useAuthStore()

  if (to.meta.requiresAuth || to.meta.requiresAdmin) {
    if (!auth.token) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }

    if (!auth.user) {
      const ok = await auth.fetchMe()
      if (!ok) {
        auth.logout()
        return { name: 'login', query: { redirect: to.fullPath } }
      }
    }

    if (auth.user && auth.user.status !== 'active') {
      auth.logout()
      return { name: 'login' }
    }

    if (to.meta.requiresAdmin && auth.user?.role !== 'admin') {
      return { name: 'shop-home' }
    }
  }

  return true
})

router.afterEach((to: any) => {
  const name = String(to.name || '')
  const pageTitle = routeTitleMap[name]

  if (!pageTitle) {
    document.title = APP_BRAND_NAME
    return
  }

  if (pageTitle === APP_BRAND_NAME) {
    document.title = APP_BRAND_NAME
    return
  }

  const scope = name.startsWith('admin-')
    ? ADMIN_PANEL_NAME
    : ['dashboard', 'redeem', 'keys', 'usage', 'profile', 'client-install', 'subscriptions', 'billing', 'ProxyPlayground'].includes(name)
      ? CONSOLE_BRAND_NAME
      : APP_BRAND_NAME

  document.title = `${pageTitle} - ${scope}`
})

export default router
