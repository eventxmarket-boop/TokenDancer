<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { getPersonaById } from '@/data/personas'

const route = useRoute()
const persona = computed(() => getPersonaById(String(route.params.id || '')))
</script>

<template>
  <section v-if="persona" class="detail-layout">
    <article class="detail-card">
      <div class="detail-header">
        <div class="detail-avatar">{{ persona.avatar }}</div>
        <div>
          <p class="eyebrow">{{ persona.category }}</p>
          <h2>{{ persona.name }}</h2>
          <p class="hero-text">{{ persona.intro }}</p>
        </div>
      </div>

      <div class="detail-block">
        <h3>适合聊什么</h3>
        <div class="tag-row">
          <span v-for="topic in persona.topics" :key="topic" class="tag-chip">{{ topic }}</span>
        </div>
      </div>

      <div class="detail-block">
        <h3>一句话简介</h3>
        <p>{{ persona.profile }}</p>
      </div>

      <div class="detail-actions">
        <RouterLink class="primary-btn" :to="`/chat/${persona.id}`">开始聊天</RouterLink>
        <RouterLink class="secondary-btn" to="/">回到首页</RouterLink>
      </div>
    </article>

    <aside class="detail-side">
      <div class="mini-panel">
        <p class="eyebrow">推荐提问</p>
        <ul class="question-list">
          <li v-for="question in persona.recommendedQuestions" :key="question">{{ question }}</li>
        </ul>
      </div>
    </aside>
  </section>

  <section v-else class="empty-state">
    <h2>没有找到这个人格。</h2>
    <RouterLink class="primary-btn" to="/">返回首页</RouterLink>
  </section>
</template>
