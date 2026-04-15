<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { loadRecentSessions, type RecentSessionSummary } from '@/services/chatService'
import { getFavoriteSlugs } from '@/services/favoriteService'
import { listPersonas, type Persona } from '@/services/personaService'

const recent = ref<RecentSessionSummary[]>([])
const favoritePersonas = ref<Persona[]>([])
const recentLoading = ref(true)
const favoritesLoading = ref(true)

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

const loadFavorites = async () => {
  favoritesLoading.value = true
  try {
    const personas = await listPersonas()
    const slugs = new Set(getFavoriteSlugs())
    favoritePersonas.value = personas.filter((persona) => slugs.has(persona.slug))
  } catch {
    favoritePersonas.value = []
  } finally {
    favoritesLoading.value = false
  }
}

const sessionLink = (session: RecentSessionSummary) => ({
  path: `/chat/${session.persona_slug}`,
  query: { session_id: session.id },
})

const favoriteCount = computed(() => favoritePersonas.value.length)

onMounted(() => {
  void loadRecent()
  void loadFavorites()
})
</script>

<template>
  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">我的</p>
        <h2>最近会话、收藏人格和快捷入口。</h2>
      </div>
      <div class="hero-actions">
        <RouterLink class="secondary-btn" to="/favorites">去收藏页</RouterLink>
        <RouterLink class="primary-btn" to="/create">创造自我人格</RouterLink>
      </div>
    </div>

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
        <div v-else class="state-copy">还没有最近会话，先从 Seed 选一个人格开始聊吧。</div>
      </div>

      <div class="mini-panel">
        <p class="side-title">收藏人格</p>
        <div v-if="favoritesLoading" class="state-copy">正在读取收藏…</div>
        <div v-else-if="favoritePersonas.length" class="tag-row">
          <span v-for="persona in favoritePersonas" :key="persona.slug" class="tag-chip">
            {{ persona.name }}
          </span>
        </div>
        <div v-else class="state-copy">
          还没有收藏人格，去 Seed 页面把常用的人格先收进来。
        </div>
      </div>

      <div class="mini-panel">
        <p class="side-title">快捷入口</p>
        <p>这页先做一个轻量中枢，后面再接更完整的个人主页功能。</p>
        <p class="state-copy">当前收藏数：{{ favoriteCount }}</p>
        <RouterLink class="primary-btn" to="/seed">去 Seed</RouterLink>
        <RouterLink class="secondary-btn" to="/sessions" style="margin-top: 10px;">最近会话</RouterLink>
        <RouterLink class="secondary-btn" to="/favorites" style="margin-top: 10px;">收藏人格</RouterLink>
        <RouterLink class="secondary-btn" to="/admin" style="margin-top: 10px;">后台设置</RouterLink>
      </div>
    </div>
  </section>
</template>
