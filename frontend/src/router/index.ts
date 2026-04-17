import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/views/HomePage.vue'
import SeedPage from '@/views/SeedPage.vue'
import FavoritesPage from '@/views/FavoritesPage.vue'
import CreatePersonaPage from '@/views/CreatePersonaPage.vue'
import CreateWizardPage from '@/views/CreateWizardPage.vue'
import CreateResultPage from '@/views/CreateResultPage.vue'
import ReplyAssistantLandingPage from '@/views/ReplyAssistantLandingPage.vue'
import ReplyAssistantPage from '@/views/ReplyAssistantPage.vue'
import HowToDoPage from '@/views/HowToDoPage.vue'
import HowToDoDetailPage from '@/views/HowToDoDetailPage.vue'
import HowToDoSongAddPage from '@/views/HowToDoSongAddPage.vue'
import CharacterPage from '@/views/CharacterPage.vue'
import ChatPage from '@/views/ChatPage.vue'
import AdminPage from '@/views/AdminPage.vue'
import RecentSessionsPage from '@/views/RecentSessionsPage.vue'
import MySeedsPage from '@/views/MySeedsPage.vue'
import MePage from '@/views/MePage.vue'
import LoginPage from '@/views/LoginPage.vue'
import RegisterPage from '@/views/RegisterPage.vue'
import { ensureAuthReady, isLoggedIn } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomePage, meta: { title: '首页' } },
    { path: '/seed', name: 'seed', component: SeedPage, meta: { title: 'Seed 选择' } },
    {
      path: '/favorites',
      name: 'favorites',
      component: FavoritesPage,
      meta: { title: '收藏人格', requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: LoginPage,
      meta: { title: '登录' },
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterPage,
      meta: { title: '注册' },
    },
    {
      path: '/create',
      name: 'create-persona',
      component: CreatePersonaPage,
      meta: { title: '创建自我人格' },
    },
    {
      path: '/create/wizard',
      name: 'create-wizard',
      component: CreateWizardPage,
      meta: { title: '创建向导' },
    },
    {
      path: '/create/result',
      name: 'create-result',
      component: CreateResultPage,
      meta: { title: '创建结果' },
    },
    {
      path: '/reply-assistant',
      name: 'reply-assistant',
      component: ReplyAssistantLandingPage,
      meta: { title: '我该怎么回' },
    },
    {
      path: '/reply-assistant/workbench',
      name: 'reply-assistant-workbench',
      component: ReplyAssistantPage,
      meta: { title: '我该怎么回' },
    },
    {
      path: '/how-to-do',
      name: 'how-to-do',
      component: HowToDoPage,
      meta: { title: '我该怎么做' },
    },
    {
      path: '/how-to-do/select-gua',
      name: 'how-to-do-select-gua',
      component: HowToDoPage,
      meta: { title: '起卦' },
    },
    {
      path: '/how-to-do/reference',
      name: 'how-to-do-reference',
      component: HowToDoPage,
      meta: { title: '参考' },
    },
    {
      path: '/how-to-do/all-gua',
      name: 'how-to-do-all-gua',
      component: HowToDoPage,
      meta: { title: '六十四卦' },
    },
    {
      path: '/how-to-do/calendar',
      name: 'how-to-do-calendar',
      component: HowToDoPage,
      meta: { title: '日历' },
    },
    {
      path: '/how-to-do/clock',
      name: 'how-to-do-clock',
      component: HowToDoPage,
      meta: { title: '时钟' },
    },
    {
      path: '/how-to-do/records',
      name: 'how-to-do-records',
      component: HowToDoPage,
      meta: { title: '记录' },
    },
    {
      path: '/how-to-do/songs',
      name: 'how-to-do-songs',
      component: HowToDoPage,
      meta: { title: '歌诀' },
    },
    {
      path: '/how-to-do/detail',
      name: 'how-to-do-detail',
      component: HowToDoDetailPage,
      meta: { title: '卦详情' },
    },
    {
      path: '/how-to-do/songs/add',
      name: 'how-to-do-songs-add',
      component: HowToDoSongAddPage,
      meta: { title: '添加歌诀' },
    },
    {
      path: '/character/:id',
      name: 'character',
      component: CharacterPage,
      meta: { title: '人格详情' },
    },
    {
      path: '/chat/:id',
      name: 'chat',
      component: ChatPage,
      meta: { title: '对话' },
    },
    {
      path: '/sessions',
      name: 'sessions',
      component: RecentSessionsPage,
      meta: { title: '最近会话', requiresAuth: true },
    },
    {
      path: '/my-seeds',
      name: 'my-seeds',
      component: MySeedsPage,
      meta: { title: '我创建的 Seed', requiresAuth: true },
    },
    { path: '/me', name: 'me', component: MePage, meta: { title: '个人中心' } },
    { path: '/admin', name: 'admin', component: AdminPage, meta: { title: '后台设置' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
  await ensureAuthReady()

  const requiresAuth = to.matched.some((record) => Boolean(record.meta.requiresAuth))
  if (requiresAuth && !isLoggedIn.value) {
    return {
      path: '/login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  if ((to.name === 'login' || to.name === 'register') && isLoggedIn.value) {
    const redirect = String(to.query.redirect || '').trim()
    return redirect || '/me'
  }
})

router.afterEach((to) => {
  const pageTitle = String(to.meta.title || 'Tokendancer')
  document.title = `${pageTitle} - Tokendancer`
})

export default router
