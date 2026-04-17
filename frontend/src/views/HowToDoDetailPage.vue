<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { HowToDoResponse } from '@/services/howToDoService'

const router = useRouter()

const lastResult = computed<HowToDoResponse | null>(() => {
  try {
    const raw = window.localStorage.getItem('liuyao-last-result')
    return raw ? (JSON.parse(raw) as HowToDoResponse) : null
  } catch {
    return null
  }
})
</script>

<template>
  <section class="page-hero page-hero--single">
    <div class="hero-copy">
      <p class="eyebrow">心源六爻</p>
      <h1>卦详情</h1>
      <p class="hero-text">这里展示最近一次起卦的完整信息。</p>
    </div>
  </section>

  <section class="summary-panel summary-panel--featured">
    <template v-if="lastResult">
      <p class="eyebrow">{{ lastResult.method_label }}</p>
      <h3>{{ lastResult.summary }}</h3>
      <div class="how-to-do-card-grid">
        <div v-for="card in lastResult.cards" :key="card.label" class="how-to-do-result-card">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
        </div>
      </div>
      <div v-if="lastResult.raw_result?.mutual_hexagram" class="how-to-do-detail-box">
        <p class="eyebrow">互卦</p>
        <strong>{{ (lastResult.raw_result.mutual_hexagram as Record<string, any>).name }}卦</strong>
        <p>{{ (lastResult.raw_result.mutual_hexagram as Record<string, any>).meaning }}</p>
      </div>
      <div class="how-to-do-interpretation">
        <p class="eyebrow">AI 解读</p>
        <p>{{ lastResult.ai_interpretation }}</p>
      </div>
    </template>

    <template v-else>
      <div class="empty-panel empty-panel--compact">
        <div class="empty-panel__icon">◎</div>
        <div class="empty-panel__copy">
          <strong>还没有可显示的详情。</strong>
          <p>先回到起卦页起一卦，再回来查看。</p>
        </div>
      </div>
    </template>

    <div class="how-to-do-actions">
      <button class="secondary-btn" type="button" @click="router.push('/how-to-do/select-gua')">返回起卦</button>
    </div>
  </section>
</template>
