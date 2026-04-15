import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/views/HomePage.vue'
import SeedPage from '@/views/SeedPage.vue'
import FavoritesPage from '@/views/FavoritesPage.vue'
import CreatePersonaPage from '@/views/CreatePersonaPage.vue'
import CreateWizardPage from '@/views/CreateWizardPage.vue'
import CreateResultPage from '@/views/CreateResultPage.vue'
import CharacterPage from '@/views/CharacterPage.vue'
import ChatPage from '@/views/ChatPage.vue'
import AdminPage from '@/views/AdminPage.vue'
import RecentSessionsPage from '@/views/RecentSessionsPage.vue'
import MePage from '@/views/MePage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomePage, meta: { title: '首页' } },
    { path: '/seed', name: 'seed', component: SeedPage, meta: { title: 'Seed 选择' } },
    {
      path: '/favorites',
      name: 'favorites',
      component: FavoritesPage,
      meta: { title: '收藏人格' },
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
      meta: { title: '人格草稿' },
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
      meta: { title: '最近会话' },
    },
    { path: '/me', name: 'me', component: MePage, meta: { title: '我的' } },
    { path: '/admin', name: 'admin', component: AdminPage, meta: { title: '后台设置' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.afterEach((to) => {
  const pageTitle = String(to.meta.title || '人格小屋')
  document.title = `${pageTitle} - 人格小屋`
})

export default router
