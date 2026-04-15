<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { loadRecentSessions, type RecentSessionSummary } from '@/services/chatService'

const recent = ref<RecentSessionSummary[]>([])
const recentLoading = ref(true)
const favorites = ['Paul Graham', 'Charlie Munger', '张雪峰']

const loadRecent = async () => {
  recentLoading.value = true
  try {
    recent.value = await loadRecentSessions(5)
  } catch {
    recent.value = []
  } finally {
    recentLoading.value = false
  }
}

const sessionLink = (session: RecentSessionSummary) => ({
  path: `/chat/${session.persona_slug}`,
  query: { session_id: session.id },
})

onMounted(() => {
  void loadRecent()
})
</script>

<template>
  <section class="profile-layout">
    <article class="section-card">
      <p class="eyebrow">我的</p>
      <h2>最近聊天与收藏人格</h2>

      <div class="profile-grid">
        <div class="mini-panel">
          <p class="side-title">最近聊天</p>
          <div v-if="recentLoading" class="state-copy">正在读取最近会话…</div>
          <div v-else-if="recent.length">
            <ul class="recent-list">
              <li v-for="item in recent" :key="item.id">
                <RouterLink class="recent-list__link" :to="sessionLink(item)">
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.persona_name }} · {{ new Date(item.updated_at).toLocaleString() }}</span>
                </RouterLink>
              </li>
            </ul>
          </div>
          <div v-else class="state-copy">
            还没有最近会话，先从首页选一个人格开始聊吧。
          </div>
        </div>

        <div class="mini-panel">
          <p class="side-title">收藏人格</p>
          <div class="tag-row">
            <span v-for="name in favorites" :key="name" class="tag-chip">{{ name }}</span>
          </div>
        </div>

        <div class="mini-panel">
          <p class="side-title">反馈入口</p>
          <p>这一版先把入口做轻，后续再接更完整的反馈流。</p>
          <RouterLink class="primary-btn" to="/">返回首页</RouterLink>
          <RouterLink class="secondary-btn" to="/sessions" style="margin-top: 10px;">最近会话</RouterLink>
          <RouterLink class="secondary-btn" to="/admin" style="margin-top: 10px;">后台设置</RouterLink>
        </div>
      </div>
    </article>
  </section>
</template>
