<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { requestHowToDo, type HowToDoCastMode, type HowToDoCatalogCard, type HowToDoResponse, type HowToDoSection } from '@/services/howToDoService'

type SectionOption = {
  key: HowToDoSection
  label: string
  hint: string
}

type CastModeOption = {
  key: HowToDoCastMode
  label: string
  hint: string
}

type LocalRecord = {
  id: string
  title: string
  createdAt: string
  summary: string
  response: HowToDoResponse
  pinned: boolean
}

const sectionOptions: SectionOption[] = [
  { key: 'cast', label: '起卦', hint: '汉字、数字、硬币、太极丸四种方式。' },
  { key: 'catalog', label: '卦库', hint: '直接看六十四卦。' },
  { key: 'calendar', label: '日历', hint: '看日期与时间参考。' },
  { key: 'clock', label: '时钟', hint: '看当前时刻。' },
  { key: 'records', label: '记录', hint: '看本地保存的起卦记录。' },
  { key: 'songs', label: '歌诀', hint: '看六爻速记与口诀。' },
]

const castModeOptions: CastModeOption[] = [
  { key: 'character', label: '汉字起卦', hint: '输入汉字或一句话。' },
  { key: 'number', label: '数字起卦', hint: '输入一串数字。' },
  { key: 'coin', label: '硬币起卦', hint: '按常见掷币方式起卦。' },
  { key: 'taiji', label: '太极丸起卦', hint: '按太极丸方式起卦。' },
]

const activeSection = ref<HowToDoSection>('cast')
const activeCastMode = ref<HowToDoCastMode>('coin')
const question = ref('')
const castSeed = ref(String(Date.now()))
const characterText = ref('')
const numberText = ref('')
const loading = ref(false)
const errorMessage = ref('')
const result = ref<HowToDoResponse | null>(null)
const catalogQuery = ref('')
const catalogSelected = ref<HowToDoCatalogCard | null>(null)
const records = ref<LocalRecord[]>([])
const currentTime = ref(new Date())
let timer: number | undefined

const catalogCards = computed(() => result.value?.catalog || [])
const filteredCatalogCards = computed(() => {
  const query = catalogQuery.value.trim()
  if (!query) return catalogCards.value
  return catalogCards.value.filter((item) => `${item.number}${item.name}${item.meaning}${item.binary}`.includes(query))
})

const recordCount = computed(() => records.value.length)

function applySection(section: HowToDoSection) {
  activeSection.value = section
  errorMessage.value = ''
  if (section === 'records') {
    loadRecords()
  }
  if (section === 'clock') {
    currentTime.value = new Date()
  }
}

function loadRecords() {
  try {
    const raw = window.localStorage.getItem('liuyao-records')
    const parsed = raw ? (JSON.parse(raw) as LocalRecord[]) : []
    records.value = Array.isArray(parsed) ? parsed : []
  } catch {
    records.value = []
  }
}

function persistRecords(nextRecords: LocalRecord[]) {
  records.value = nextRecords
  window.localStorage.setItem('liuyao-records', JSON.stringify(nextRecords))
}

function saveCurrentRecord() {
  if (!result.value || activeSection.value !== 'cast') return
  const title = question.value.trim() || `${result.value.method_label}`
  const next: LocalRecord[] = [
    {
      id: `${Date.now()}`,
      title,
      createdAt: new Date().toISOString(),
      summary: result.value.summary,
      response: result.value,
      pinned: false,
    },
    ...records.value,
  ]
  persistRecords(next.slice(0, 30))
}

function renameRecord(id: string) {
  const item = records.value.find((record) => record.id === id)
  if (!item) return
  const nextTitle = window.prompt('重命名记录', item.title)?.trim()
  if (!nextTitle) return
  persistRecords(records.value.map((record) => (record.id === id ? { ...record, title: nextTitle } : record)))
}

function togglePinRecord(id: string) {
  persistRecords(
    [...records.value]
      .map((record) => (record.id === id ? { ...record, pinned: !record.pinned } : record))
      .sort((a, b) => Number(b.pinned) - Number(a.pinned) || b.createdAt.localeCompare(a.createdAt)),
  )
}

function deleteRecord(id: string) {
  const ok = window.confirm('删除后无法找回，确定要删除这条记录吗？')
  if (!ok) return
  persistRecords(records.value.filter((record) => record.id !== id))
}

function openRecord(record: LocalRecord) {
  activeSection.value = 'cast'
  question.value = record.response.question || record.title
  castSeed.value = String(Date.now())
  result.value = record.response
}

async function generate(section: HowToDoSection = activeSection.value) {
  errorMessage.value = ''
  loading.value = true
  try {
    const payload =
      section === 'cast'
        ? {
            section,
            cast_mode: activeCastMode.value,
            question: question.value.trim(),
            cast_seed: castSeed.value,
            character_text: characterText.value.trim(),
            number_text: numberText.value.trim(),
            use_ai: true,
          }
        : { section, use_ai: false }

    const response = await requestHowToDo(payload)
    result.value = response
    if (section === 'catalog' && response.catalog.length > 0) {
      catalogSelected.value = response.catalog[0]
    }
    if (section === 'cast') {
      saveCurrentRecord()
      castSeed.value = String(Date.now())
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '生成失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function selectCatalogCard(card: HowToDoCatalogCard) {
  catalogSelected.value = card
}

function useClockSeed() {
  activeSection.value = 'cast'
  activeCastMode.value = 'coin'
  castSeed.value = String(Date.now())
  question.value = `我现在这个时刻该怎么做？`
}

onMounted(() => {
  loadRecords()
  timer = window.setInterval(() => {
    currentTime.value = new Date()
  }, 1000)
})

onBeforeUnmount(() => {
  if (timer) {
    window.clearInterval(timer)
  }
})
</script>

<template>
  <section class="page-hero page-hero--single how-to-do-hero">
    <div class="hero-copy">
      <p class="eyebrow">心源六爻</p>
      <h1>我该怎么做</h1>
      <p class="hero-text">汉字起卦、数字起卦、硬币起卦、太极丸起卦，和卦库、日历、时钟、记录放在同一个页面里。</p>
    </div>
  </section>

  <section class="how-to-do-page">
    <div class="how-to-do-mode-row" role="tablist" aria-label="六爻模块">
      <button
        v-for="option in sectionOptions"
        :key="option.key"
        type="button"
        class="chip-btn"
        :class="{ 'chip-btn--active': activeSection === option.key }"
        @click="applySection(option.key)"
      >
        {{ option.label }}
      </button>
    </div>

    <div class="how-to-do-layout">
      <article class="summary-panel how-to-do-panel">
        <div class="how-to-do-panel__head">
          <div>
            <p class="eyebrow">模块</p>
            <h3>{{ sectionOptions.find((item) => item.key === activeSection)?.label }}</h3>
            <p class="hero-text">{{ sectionOptions.find((item) => item.key === activeSection)?.hint }}</p>
          </div>
        </div>

        <template v-if="activeSection === 'cast'">
          <div class="how-to-do-toggle-row">
            <button
              v-for="option in castModeOptions"
              :key="option.key"
              type="button"
              class="chip-btn"
              :class="{ 'chip-btn--active': activeCastMode === option.key }"
              @click="activeCastMode = option.key"
            >
              {{ option.label }}
            </button>
          </div>

          <p class="how-to-do-note">
            汉字起卦和数字起卦适合把内容直接喂进去。硬币起卦和太极丸起卦适合快速起局。
          </p>

          <label class="field-label" for="how-to-do-question">问题</label>
          <textarea
            id="how-to-do-question"
            v-model="question"
            class="text-area"
            rows="4"
            placeholder="把事说清楚，越具体越好。"
          ></textarea>

          <label v-if="activeCastMode === 'character'" class="field-label">
            汉字 / 文本
            <textarea
              v-model="characterText"
              class="text-area"
              rows="3"
              placeholder="输入汉字、短句或一段话。"
            ></textarea>
          </label>

          <label v-if="activeCastMode === 'number'" class="field-label">
            数字
            <textarea
              v-model="numberText"
              class="text-area"
              rows="3"
              placeholder="输入数字、编号或数字串。"
            ></textarea>
          </label>

          <div class="how-to-do-field-grid">
            <label class="field-label">
              起卦种子
              <input v-model="castSeed" type="text" class="field-input" />
            </label>
            <label class="field-label">
              说明
              <input :value="activeCastMode === 'coin' ? '硬币起卦' : activeCastMode === 'taiji' ? '太极丸起卦' : '文本起卦'" type="text" class="field-input" disabled />
            </label>
          </div>

          <div class="how-to-do-actions">
            <button class="primary-btn" type="button" :disabled="loading" @click="generate('cast')">
              {{ loading ? '生成中...' : '起卦' }}
            </button>
          </div>
        </template>

        <template v-else-if="activeSection === 'catalog'">
          <div class="how-to-do-actions how-to-do-actions--left">
            <button class="primary-btn" type="button" :disabled="loading" @click="generate('catalog')">
              {{ loading ? '加载中...' : '加载卦库' }}
            </button>
          </div>
          <label class="field-label">
            搜索卦名
            <input v-model="catalogQuery" type="text" class="field-input" placeholder="例如：乾、坤、泰、未济" />
          </label>
          <div class="liuyao-catalog-grid">
            <button
              v-for="card in filteredCatalogCards"
              :key="`${card.number}-${card.name}`"
              type="button"
              class="liuyao-catalog-card"
              :class="{ 'is-selected': catalogSelected?.number === card.number }"
              @click="selectCatalogCard(card)"
            >
              <strong>{{ card.number }} {{ card.name }}</strong>
              <span>{{ card.meaning }}</span>
            </button>
          </div>
        </template>

        <template v-else-if="activeSection === 'calendar'">
          <div class="how-to-do-note">
            日历页主要是给起卦找时间参考。你也可以直接用当前日期起卦。
          </div>
          <div class="how-to-do-time-card">
            <strong>{{ currentTime.toLocaleString() }}</strong>
            <p>当前时间</p>
          </div>
          <div class="how-to-do-actions">
            <button class="primary-btn" type="button" @click="useClockSeed">用当前时间起卦</button>
            <button class="secondary-btn" type="button" :disabled="loading" @click="generate('calendar')">查看提示</button>
          </div>
        </template>

        <template v-else-if="activeSection === 'clock'">
          <div class="how-to-do-time-card how-to-do-time-card--accent">
            <strong>{{ currentTime.toLocaleTimeString() }}</strong>
            <p>{{ currentTime.toLocaleDateString() }}</p>
          </div>
          <div class="how-to-do-actions">
            <button class="primary-btn" type="button" @click="useClockSeed">直接用现在起卦</button>
            <button class="secondary-btn" type="button" :disabled="loading" @click="generate('clock')">查看提示</button>
          </div>
        </template>

        <template v-else-if="activeSection === 'records'">
          <p class="how-to-do-note">记录保存在浏览器本地，方便回看最近几次起卦。</p>
          <div class="how-to-do-record-count">共 {{ recordCount }} 条记录</div>
          <div class="liuyao-record-list">
            <article v-for="record in records" :key="record.id" class="liuyao-record-item" :class="{ 'is-pinned': record.pinned }">
              <button class="liuyao-record-open" type="button" @click="openRecord(record)">
                <strong>{{ record.title }}</strong>
                <span>{{ record.summary }}</span>
              </button>
              <div class="liuyao-record-actions">
                <button type="button" class="chip-btn" @click="togglePinRecord(record.id)">
                  {{ record.pinned ? '取消置顶' : '置顶' }}
                </button>
                <button type="button" class="chip-btn" @click="renameRecord(record.id)">重命名</button>
                <button type="button" class="chip-btn" @click="deleteRecord(record.id)">删除</button>
              </div>
            </article>
          </div>
        </template>

        <template v-else-if="activeSection === 'songs'">
          <p class="how-to-do-note">这里放速记、口诀和常见提醒，方便快速看卦时对照。</p>
          <div class="how-to-do-songs-grid">
            <div v-for="item in ['先看本卦，再看动爻。', '有变卦时，优先看后势。', '局势未明时，先稳住再说。', '六爻更适合看变化，不适合一口咬死。']" :key="item" class="how-to-do-song-card">
              {{ item }}
            </div>
          </div>
          <div class="how-to-do-actions">
            <button class="secondary-btn" type="button" :disabled="loading" @click="generate('songs')">刷新口诀</button>
          </div>
        </template>

        <p v-if="errorMessage" class="how-to-do-error">{{ errorMessage }}</p>
      </article>

      <article v-if="result" class="summary-panel summary-panel--featured how-to-do-result">
        <p class="eyebrow">{{ result.method_label }}</p>
        <h3>{{ result.summary }}</h3>

        <div v-if="result.catalog.length" class="how-to-do-catalog-preview">
          <p class="eyebrow">卦库</p>
          <div class="how-to-do-catalog-mini-grid">
            <div v-for="card in result.catalog.slice(0, 8)" :key="`${card.number}-${card.name}`" class="how-to-do-catalog-mini-card">
              <strong>{{ card.number }} {{ card.name }}</strong>
              <span>{{ card.meaning }}</span>
            </div>
          </div>
        </div>

        <div class="how-to-do-card-grid">
          <div v-for="card in result.cards" :key="card.label" class="how-to-do-result-card">
            <span>{{ card.label }}</span>
            <strong>{{ card.value }}</strong>
          </div>
        </div>

        <div v-if="result.raw_result?.lines" class="how-to-do-line-summary">
          <p class="eyebrow">爻位</p>
          <div class="liuyao-line-summary-list">
            <div
              v-for="line in (result.raw_result.lines as Array<Record<string, any>>)"
              :key="line.position"
              class="liuyao-line-summary-item"
              :class="{ 'is-changing': line.is_changing }"
            >
              <strong>{{ line.position_name }}</strong>
              <span>{{ line.text }}</span>
              <small>{{ line.guidance }}</small>
            </div>
          </div>
        </div>

        <div v-if="catalogSelected" class="how-to-do-detail-box">
          <p class="eyebrow">选中卦</p>
          <strong>{{ catalogSelected.number }} {{ catalogSelected.name }}</strong>
          <p>{{ catalogSelected.meaning }}</p>
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
          <strong>先选一个模块，再开始。</strong>
          <p>起卦、卦库、日历、时钟、记录、歌诀都放在这里。</p>
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

.how-to-do-toggle-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-bottom: 0.5rem;
}

.how-to-do-note {
  margin: 0 0 0.9rem;
  font-size: 0.88rem;
  line-height: 1.6;
  color: var(--text-secondary);
}

.how-to-do-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
}

.how-to-do-actions--left {
  justify-content: flex-start;
}

.how-to-do-error {
  margin-top: 0.75rem;
  color: #ef4444;
  font-size: 0.92rem;
}

.how-to-do-catalog-preview {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.how-to-do-catalog-mini-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.how-to-do-catalog-mini-card {
  border-radius: 16px;
  padding: 0.8rem 0.9rem;
  background: color-mix(in srgb, var(--card-bg) 94%, transparent);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.how-to-do-catalog-mini-card strong {
  display: block;
  font-size: 0.94rem;
}

.how-to-do-catalog-mini-card span {
  display: block;
  margin-top: 0.3rem;
  color: var(--text-secondary);
  font-size: 0.84rem;
  line-height: 1.5;
}

.liuyao-catalog-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.liuyao-catalog-card {
  border-radius: 16px;
  padding: 0.8rem 0.9rem;
  background: color-mix(in srgb, var(--card-bg) 94%, transparent);
  border: 1px solid rgba(148, 163, 184, 0.16);
  color: var(--text-primary);
  text-align: left;
}

.liuyao-catalog-card.is-selected {
  border-color: rgba(59, 130, 246, 0.35);
}

.liuyao-catalog-card strong,
.liuyao-catalog-card span {
  display: block;
}

.liuyao-catalog-card span {
  margin-top: 0.3rem;
  color: var(--text-secondary);
  font-size: 0.84rem;
  line-height: 1.5;
}

.how-to-do-time-card {
  border-radius: 18px;
  padding: 1rem 1.1rem;
  background: color-mix(in srgb, var(--card-bg) 94%, transparent);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.how-to-do-time-card--accent {
  border-color: rgba(59, 130, 246, 0.25);
}

.how-to-do-time-card strong {
  display: block;
  font-size: 1rem;
}

.how-to-do-time-card p {
  margin: 0.35rem 0 0;
  color: var(--text-secondary);
  font-size: 0.88rem;
}

.how-to-do-record-count {
  margin-bottom: 0.85rem;
  color: var(--text-secondary);
  font-size: 0.88rem;
}

.liuyao-record-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.liuyao-record-item {
  border-radius: 16px;
  padding: 0.85rem 0.9rem;
  background: color-mix(in srgb, var(--card-bg) 94%, transparent);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.liuyao-record-item.is-pinned {
  border-color: rgba(59, 130, 246, 0.28);
}

.liuyao-record-open {
  width: 100%;
  text-align: left;
  color: var(--text-primary);
}

.liuyao-record-open strong,
.liuyao-record-open span {
  display: block;
}

.liuyao-record-open span {
  margin-top: 0.3rem;
  color: var(--text-secondary);
  font-size: 0.84rem;
  line-height: 1.5;
}

.liuyao-record-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.7rem;
}

.how-to-do-songs-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.how-to-do-song-card {
  border-radius: 16px;
  padding: 0.85rem 0.95rem;
  background: color-mix(in srgb, var(--card-bg) 94%, transparent);
  border: 1px solid rgba(148, 163, 184, 0.16);
  line-height: 1.6;
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

.how-to-do-detail-box {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.how-to-do-detail-box p {
  margin: 0.35rem 0 0;
  color: var(--text-secondary);
  line-height: 1.6;
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

  .how-to-do-catalog-mini-grid,
  .liuyao-catalog-grid,
  .how-to-do-card-grid,
  .liuyao-line-summary-list,
  .how-to-do-songs-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .how-to-do-field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
