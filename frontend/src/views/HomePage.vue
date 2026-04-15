<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { listPersonas, type Persona } from '@/services/personaService'

const personas = ref<Persona[]>([])
const loading = ref(true)
const error = ref('')

const spotlight = computed(() => personas.value[0] ?? null)

const load = async () => {
  loading.value = true
  error.value = ''

  try {
    personas.value = await listPersonas()
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : '加载人格列表失败'
    error.value = message
    personas.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void load()
})
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
        <RouterLink class="primary-btn" :to="`/character/${spotlight?.slug ?? 'zhang_xue_feng'}`">先看一个人格</RouterLink>
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
      <div class="spotlight-card" v-else>
        <p class="spotlight-card__label">今天推荐</p>
        <h3>等待人格数据</h3>
        <p>后端接口准备好后，这里会展示首个可用人格。</p>
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

    <div v-if="loading" class="state-panel">
      <p class="eyebrow">加载中</p>
      <h3>正在读取人格列表…</h3>
    </div>

    <div v-else-if="error" class="state-panel">
      <p class="eyebrow">加载失败</p>
      <h3>人格列表暂时不可用</h3>
      <p class="state-copy">{{ error }}</p>
      <button class="primary-btn" type="button" @click="load">重试</button>
    </div>

    <div v-else-if="!personas.length" class="state-panel">
      <p class="eyebrow">暂无人格</p>
      <h3>还没有可展示的人格。</h3>
      <p class="state-copy">请先补充 backend/personas 下的正式人格目录。</p>
    </div>

    <div v-else class="persona-grid">
      <article v-for="persona in personas" :key="persona.slug" class="persona-card">
        <div class="persona-avatar">{{ persona.avatar || persona.name.slice(0, 2) }}</div>
        <div class="persona-body">
          <p class="persona-category">{{ persona.category }}</p>
          <h4>{{ persona.name }}</h4>
          <p class="persona-intro">{{ persona.intro }}</p>
          <div class="tag-row">
            <span v-for="tag in persona.tags" :key="tag" class="tag-chip">{{ tag }}</span>
          </div>
        </div>
        <div class="persona-actions">
          <RouterLink class="text-link" :to="`/character/${persona.slug}`">查看详情</RouterLink>
          <RouterLink class="text-link" :to="`/chat/${persona.slug}`">直接聊天</RouterLink>
        </div>
      </article>
    </div>
  </section>
</template>
