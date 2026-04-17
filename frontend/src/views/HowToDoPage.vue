<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { requestHowToDo, type HowToDoMode, type HowToDoResponse } from '@/services/howToDoService'

type ModeOption = {
  key: HowToDoMode
  label: string
  hint: string
}

const modeOptions: ModeOption[] = [
  { key: 'zhouyi', label: '周易64卦', hint: '问一件事，先看势，再看路。' },
  { key: 'liuyao', label: '六爻', hint: '看当前局势和变化点。' },
  { key: 'bazi', label: '八字', hint: '看长期节奏和结构。' },
]

const activeMode = ref<HowToDoMode>('zhouyi')
const question = ref('')
const castSeed = ref(String(Date.now()))
const birthYear = ref(new Date().getFullYear())
const birthMonth = ref(new Date().getMonth() + 1)
const birthDay = ref(new Date().getDate())
const birthHour = ref(new Date().getHours())
const gender = ref<'male' | 'female'>('male')
const loading = ref(false)
const errorMessage = ref('')
const result = ref<HowToDoResponse | null>(null)

const activeOption = computed(() => modeOptions.find((item) => item.key === activeMode.value) || modeOptions[0])

const modeTitle = computed(() => activeOption.value.label)
const modeHint = computed(() => activeOption.value.hint)

function switchMode(mode: HowToDoMode) {
  activeMode.value = mode
  errorMessage.value = ''
}

async function submit() {
  errorMessage.value = ''
  loading.value = true
  try {
    const payload =
      activeMode.value === 'bazi'
        ? {
            mode: activeMode.value,
            question: question.value.trim(),
            birth_year: Number(birthYear.value),
            birth_month: Number(birthMonth.value),
            birth_day: Number(birthDay.value),
            birth_hour: Number(birthHour.value),
            gender: gender.value,
            use_ai: true,
          }
        : {
            mode: activeMode.value,
            question: question.value.trim(),
            cast_seed: castSeed.value,
            use_ai: true,
          }

    result.value = await requestHowToDo(payload)
    castSeed.value = String(Date.now())
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '生成失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!question.value) {
    question.value = '我现在该怎么做？'
  }
})
</script>

<template>
  <section class="page-hero page-hero--single how-to-do-hero">
    <div class="hero-copy">
      <p class="eyebrow">我该怎么做</p>
      <h1>我该怎么做</h1>
      <p class="hero-text">周易、六爻、八字和后台模型解读放在一个页面里。</p>
    </div>
  </section>

  <section class="how-to-do-page">
    <div class="how-to-do-mode-row" role="tablist" aria-label="占问方式">
      <button
        v-for="option in modeOptions"
        :key="option.key"
        type="button"
        class="chip-btn"
        :class="{ 'chip-btn--active': activeMode === option.key }"
        @click="switchMode(option.key)"
      >
        {{ option.label }}
      </button>
    </div>

    <div class="how-to-do-layout">
      <article class="summary-panel how-to-do-panel">
        <div class="how-to-do-panel__head">
          <div>
            <p class="eyebrow">填写</p>
            <h3>{{ modeTitle }}</h3>
            <p class="hero-text">{{ modeHint }}</p>
          </div>
        </div>

        <label v-if="activeMode !== 'bazi'" class="field-label" for="how-to-do-question">问题</label>
        <textarea
          v-if="activeMode !== 'bazi'"
          id="how-to-do-question"
          v-model="question"
          class="text-area"
          rows="4"
          placeholder="把事说清楚，越具体越好。"
        ></textarea>

        <div v-if="activeMode === 'bazi'" class="how-to-do-field-grid">
          <label class="field-label">
            出生年
            <input v-model="birthYear" type="number" class="field-input" min="1900" max="2100" />
          </label>
          <label class="field-label">
            月
            <input v-model="birthMonth" type="number" class="field-input" min="1" max="12" />
          </label>
          <label class="field-label">
            日
            <input v-model="birthDay" type="number" class="field-input" min="1" max="31" />
          </label>
          <label class="field-label">
            时
            <input v-model="birthHour" type="number" class="field-input" min="0" max="23" />
          </label>
          <label class="field-label how-to-do-gender">
            性别
            <select v-model="gender" class="field-input">
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
          </label>
        </div>

        <div class="how-to-do-actions">
          <button class="primary-btn" type="button" :disabled="loading" @click="submit">
            {{ loading ? '生成中...' : activeMode === 'bazi' ? '排盘' : '起卦' }}
          </button>
        </div>

        <p v-if="errorMessage" class="how-to-do-error">{{ errorMessage }}</p>
      </article>

      <article v-if="result" class="summary-panel summary-panel--featured how-to-do-result">
        <p class="eyebrow">基础判断</p>
        <h3>{{ result.summary }}</h3>

        <div class="how-to-do-card-grid">
          <div v-for="card in result.cards" :key="card.label" class="how-to-do-result-card">
            <span>{{ card.label }}</span>
            <strong>{{ card.value }}</strong>
          </div>
        </div>

        <div class="how-to-do-interpretation">
          <p class="eyebrow">AI 解读</p>
          <p>{{ result.ai_interpretation }}</p>
        </div>

        <div class="how-to-do-suggestions">
          <span v-for="item in result.suggestions" :key="item" class="tag-chip">{{ item }}</span>
        </div>
      </article>

      <article v-else class="empty-panel empty-panel--compact how-to-do-empty">
        <div class="empty-panel__icon">◎</div>
        <div class="empty-panel__copy">
          <strong>先输入内容，再生成结果。</strong>
          <p>结果会先给基础判断，再交给后台模型补一句更顺的解释。</p>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.how-to-do-page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.how-to-do-mode-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.how-to-do-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 1rem;
}

.how-to-do-panel,
.how-to-do-result,
.how-to-do-empty {
  min-height: 100%;
}

.how-to-do-panel__head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.field-label {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 0.85rem;
}

.field-input,
.text-area {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 16px;
  background: color-mix(in srgb, var(--card-bg) 92%, transparent);
  color: var(--text-primary);
  padding: 0.8rem 0.95rem;
  font-size: 0.96rem;
  outline: none;
}

.text-area {
  resize: vertical;
  min-height: 120px;
}

.field-input:focus,
.text-area:focus {
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}

.how-to-do-field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
}

.how-to-do-gender {
  grid-column: span 2;
}

.how-to-do-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}

.how-to-do-error {
  margin-top: 0.75rem;
  color: #ef4444;
  font-size: 0.92rem;
}

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

.how-to-do-interpretation {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.how-to-do-interpretation p:last-child {
  margin: 0.35rem 0 0;
  line-height: 1.8;
  color: var(--text-secondary);
}

.how-to-do-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-top: 1rem;
}

@media (max-width: 920px) {
  .how-to-do-layout {
    grid-template-columns: 1fr;
  }

  .how-to-do-card-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .how-to-do-field-grid {
    grid-template-columns: 1fr;
  }

  .how-to-do-gender {
    grid-column: auto;
  }
}
</style>
