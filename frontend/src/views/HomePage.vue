<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { listPersonas } from '@/services/personaService'
import type { Persona } from '@/data/personas'

const personas = ref<Persona[]>([])

onMounted(async () => {
  personas.value = await listPersonas()
})

const spotlight = computed(() => personas.value[0])
</script>

<template>
  <section class="hero-card">
    <div class="hero-copy">
      <p class="eyebrow">官方首发人格馆</p>
      <h2>先选视角，再开始聊天。</h2>
      <p class="hero-text">
        这里放的是几位首发人格：你可以先看简介，再进详情，最后进入聊天页开始对话。
      </p>
      <div class="hero-actions">
        <RouterLink class="primary-btn" :to="`/character/${spotlight?.id ?? 'paul_graham'}`">先看一个人格</RouterLink>
        <RouterLink class="secondary-btn" to="/me">去我的页面</RouterLink>
      </div>
    </div>

    <div class="hero-visual">
      <div class="floating-orb"></div>
      <div class="spotlight-card" v-if="spotlight">
        <p class="spotlight-card__label">今天推荐</p>
        <h3>{{ spotlight.name }}</h3>
        <p>{{ spotlight.intro }}</p>
      </div>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">首发人格</p>
        <h3>四个角色，四种入口。</h3>
      </div>
      <p class="section-note">每个卡片都可以直接进入详情或开始聊天。</p>
    </div>

    <div class="persona-grid">
      <article v-for="persona in personas" :key="persona.id" class="persona-card">
        <div class="persona-avatar">{{ persona.avatar }}</div>
        <div class="persona-body">
          <p class="persona-category">{{ persona.category }}</p>
          <h4>{{ persona.name }}</h4>
          <p class="persona-intro">{{ persona.intro }}</p>
          <div class="tag-row">
            <span v-for="tag in persona.tags" :key="tag" class="tag-chip">{{ tag }}</span>
          </div>
        </div>
        <div class="persona-actions">
          <RouterLink class="text-link" :to="`/character/${persona.id}`">查看详情</RouterLink>
          <RouterLink class="text-link" :to="`/chat/${persona.id}`">直接聊天</RouterLink>
        </div>
      </article>
    </div>
  </section>
</template>
