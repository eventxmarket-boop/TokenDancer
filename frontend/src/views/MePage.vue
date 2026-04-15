<script setup lang="ts">
import { getRecentSessionCards } from '@/services/personaService'

const recent = getRecentSessionCards()
const favorites = ['Paul Graham', 'Charlie Munger', '张雪峰']
</script>

<template>
  <section class="profile-layout">
    <article class="section-card">
      <p class="eyebrow">我的</p>
      <h2>最近聊天与收藏人格</h2>

      <div class="profile-grid">
        <div class="mini-panel">
          <p class="side-title">最近聊天</p>
          <ul class="recent-list">
            <li v-for="item in recent" :key="item.title">
              <strong>{{ item.title }}</strong>
              <span>{{ item.time }}</span>
            </li>
          </ul>
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
        </div>
      </div>
    </article>
  </section>
</template>
