import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/views/HomePage.vue'
import CharacterPage from '@/views/CharacterPage.vue'
import ChatPage from '@/views/ChatPage.vue'
import AdminPage from '@/views/AdminPage.vue'
import RecentSessionsPage from '@/views/RecentSessionsPage.vue'
import MePage from '@/views/MePage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomePage, meta: { title: '首页' } },
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
