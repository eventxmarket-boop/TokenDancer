<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { HowToDoResponse } from '@/services/howToDoService'

const router = useRouter()
const showHidden = ref(true)
const useSymbols = ref(false)
const showNaYin = ref(true)

const lastResult = computed<HowToDoResponse | null>(() => {
  try {
    const raw = window.localStorage.getItem('liuyao-last-result')
    return raw ? (JSON.parse(raw) as HowToDoResponse) : null
  } catch {
    return null
  }
})

function sharePage() {
  if (navigator.share) {
    void navigator.share({ title: document.title, url: window.location.href })
    return
  }
  void navigator.clipboard.writeText(window.location.href)
}

function copyHexagram() {
  const text = [lastResult.value?.summary, lastResult.value?.ai_interpretation].filter(Boolean).join('\n')
  void navigator.clipboard.writeText(text || '暂无可复制内容')
}
</script>

<template>
  <section class="page-hero page-hero--single">
    <div class="hero-copy">
      <p class="eyebrow">心源六爻</p>
      <h1>卦象详情</h1>
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

      <div class="how-to-do-detail-box">
        <p class="eyebrow">问念</p>
        <strong>{{ lastResult.question || '未填写' }}</strong>
      </div>

      <div class="how-to-do-detail-box">
        <p class="eyebrow">分类</p>
        <strong>{{ (lastResult.raw_result.category as string) || '未分类' }}</strong>
      </div>

      <div class="how-to-do-detail-box">
        <p class="eyebrow">时间</p>
        <p>{{ (lastResult.raw_result.timestamp as string) || '—' }}</p>
      </div>

      <div class="how-to-do-detail-box">
        <p class="eyebrow">神煞</p>
        <p>卦身：{{ ((lastResult.raw_result.shensha as Record<string, string>) || {}).卦身 || '—' }}</p>
        <p>贵人：{{ ((lastResult.raw_result.shensha as Record<string, string>) || {}).贵人 || '—' }}</p>
        <p>驿马：{{ ((lastResult.raw_result.shensha as Record<string, string>) || {}).驿马 || '—' }}</p>
        <p>羊刃：{{ ((lastResult.raw_result.shensha as Record<string, string>) || {}).羊刃 || '—' }}</p>
      </div>

      <div class="how-to-do-line-summary">
        <p class="eyebrow">六爻</p>
        <div class="liuyao-line-summary-list">
          <div
            v-for="line in (lastResult.raw_result.line_details as Array<Record<string, any>>)"
            :key="line.position"
            class="liuyao-line-summary-item"
            :class="{ 'is-changing': line.is_changing }"
          >
            <strong>{{ line.position_name }} {{ line.six_spirit }}</strong>
            <span>{{ useSymbols ? (line.is_changing ? '▅ ▅' : '▅▅▅') : line.text }}</span>
            <small>{{ showNaYin ? `${line.relation} · ${line.stem_branch} · ${line.nayin}` : `${line.relation} · ${line.stem_branch}` }}</small>
            <small v-if="showHidden">{{ line.hidden_spirit }}</small>
            <small>{{ line.shi_ying }}</small>
          </div>
        </div>
      </div>

      <div v-if="lastResult.raw_result.mutual_hexagram" class="how-to-do-detail-box">
        <p class="eyebrow">互卦</p>
        <strong>{{ (lastResult.raw_result.mutual_hexagram as Record<string, any>).name }}卦</strong>
        <p>{{ (lastResult.raw_result.mutual_hexagram as Record<string, any>).meaning }}</p>
      </div>

      <div class="how-to-do-interpretation">
        <p class="eyebrow">AI 解读</p>
        <p>{{ lastResult.ai_interpretation }}</p>
      </div>

      <div class="how-to-do-toggle-row" style="margin-top: 1rem;">
        <button class="chip-btn" :class="{ 'chip-btn--active': showHidden }" type="button" @click="showHidden = !showHidden">显示全部伏神</button>
        <button class="chip-btn" :class="{ 'chip-btn--active': useSymbols }" type="button" @click="useSymbols = !useSymbols">使用符号代替阴阳爻符号</button>
        <button class="chip-btn" :class="{ 'chip-btn--active': showNaYin }" type="button" @click="showNaYin = !showNaYin">显示纳音</button>
      </div>

      <div class="how-to-do-actions">
        <button class="secondary-btn" type="button" @click="sharePage">分享当页URL</button>
        <button class="secondary-btn" type="button" @click="copyHexagram">复制卦象</button>
        <button class="secondary-btn" type="button" @click="router.push('/how-to-do')">返回排盘</button>
      </div>
    </template>

    <template v-else>
      <div class="empty-panel empty-panel--compact">
        <div class="empty-panel__icon">◎</div>
        <div class="empty-panel__copy">
          <strong>还没有可显示的详情。</strong>
          <p>先回到排盘页起一卦，再回来查看。</p>
        </div>
      </div>

      <div class="how-to-do-actions">
        <button class="secondary-btn" type="button" @click="router.push('/how-to-do')">返回排盘</button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.how-to-do-card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.how-to-do-result-card {
  border-radius: 16px;
  padding: 0.85rem 0.95rem;
  background: color-mix(in srgb, var(--card-bg) 94%, transparent);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.how-to-do-result-card span {
  display: block;
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.how-to-do-result-card strong {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.98rem;
  color: var(--text-primary);
  line-height: 1.5;
}

.how-to-do-detail-box,
.how-to-do-interpretation {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.how-to-do-line-summary {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.liuyao-line-summary-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.liuyao-line-summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  border-radius: 16px;
  padding: 0.8rem 0.9rem;
  background: color-mix(in srgb, var(--card-bg) 94%, transparent);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.liuyao-line-summary-item.is-changing {
  border-color: rgba(59, 130, 246, 0.28);
}

.liuyao-line-summary-item strong {
  font-size: 0.94rem;
}

.liuyao-line-summary-item span {
  font-size: 0.92rem;
  color: var(--text-primary);
}

.liuyao-line-summary-item small {
  font-size: 0.82rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.how-to-do-toggle-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-top: 1rem;
}

.how-to-do-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.empty-panel {
  border-radius: 18px;
  padding: 1rem 1.1rem;
  background: color-mix(in srgb, var(--card-bg) 94%, transparent);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.empty-panel--compact {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.empty-panel__icon {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.08);
  color: var(--text-primary);
}

.empty-panel__copy strong {
  display: block;
}

.empty-panel__copy p {
  margin: 0.35rem 0 0;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .how-to-do-card-grid,
  .liuyao-line-summary-list {
    grid-template-columns: 1fr;
  }
}
</style>
