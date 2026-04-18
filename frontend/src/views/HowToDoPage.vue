<script setup lang="ts">
import { computed, ref } from 'vue'
import { requestHowToDo, type HowToDoResponse } from '@/services/howToDoService'

type CastModeKey = 'manual' | 'coin' | 'taiji' | 'online'

const castModes: Array<{ key: CastModeKey; label: string; hint: string }> = [
  { key: 'coin', label: '随机摇卦', hint: '平心静气后摇卦。' },
  { key: 'manual', label: '手动输入', hint: '按 6 次依次录入。' },
  { key: 'taiji', label: '太极丸起卦', hint: '按太极丸方式起局。' },
  { key: 'online', label: '在线起卦', hint: '按 6 次依次录入。' },
]

const questionCategories = [
  '出行平安',
  '能否出行',
  '何时出行',
  '行人归来',
  '求财',
  '求官',
  '求职',
  '工作推进',
  '升迁调动',
  '考试测验',
  '学业文书',
  '感情回应',
  '婚姻复合',
  '表白推进',
  '朋友关系',
  '家宅关系',
  '父母长辈',
  '子女教育',
  '健康疾病',
  '诉讼官非',
  '失物寻人',
  '合作合伙',
  '交易签约',
  '投资买卖',
  '开店经营',
  '搬家迁移',
  '出国远行',
  '生产怀孕',
  '借贷还款',
  '项目进度',
  '面试入职',
  '其他',
]

const activeCastMode = ref<CastModeKey>('coin')
const question = ref('')
const category = ref('')
const castSeed = ref('')
const manualLines = ref<number[]>([0, 0, 0, 0, 0, 0])
const loading = ref(false)
const errorMessage = ref('')
const result = ref<HowToDoResponse | null>(null)
const showResultBoard = ref(true)
const lineOptions = [
  { value: 8, label: '少阴', detail: '2背1字', barText: '▅ ▅' },
  { value: 7, label: '少阳', detail: '1背2字', barText: '▅▅▅' },
  { value: 6, label: '老阴', detail: '0背3字', barText: '▅ ▅', changeMark: 'x' },
  { value: 9, label: '老阳', detail: '3背0字', barText: '▅▅▅', changeMark: 'o' },
]
const lineLabels = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']

function formatCastSeed(now = new Date()) {
  const year = now.getFullYear()
  const month = `${now.getMonth() + 1}`.padStart(2, '0')
  const day = `${now.getDate()}`.padStart(2, '0')
  const hour = `${now.getHours()}`.padStart(2, '0')
  const minute = `${now.getMinutes()}`.padStart(2, '0')
  const second = `${now.getSeconds()}`.padStart(2, '0')
  return `${year}/${month}/${day} ${hour}:${minute}:${second}`
}

castSeed.value = formatCastSeed()

const castResult = computed(() => result.value?.raw_result as Record<string, any> | undefined)
const castLineDetails = computed(() => {
  const list = castResult.value?.line_details
  if (!Array.isArray(list)) return []
  return [...list].reverse()
})
const transformedLineDetails = computed(() => {
  const list = castResult.value?.transformed_line_details
  if (!Array.isArray(list)) return []
  return [...list].reverse()
})
const castQuestionText = computed(() => result.value?.question?.trim() || question.value.trim() || '搜索')
const castModeText = computed(() => {
  const mode = castResult.value?.cast_mode || activeCastMode.value
  if (mode === 'online') return '在线起卦'
  if (mode === 'manual') return '硬币 / 太极丸起卦'
  if (mode === 'taiji') return '太极丸起卦'
  if (mode === 'character') return '汉字起卦'
  return '硬币起卦'
})
const usesManualInput = computed(() => activeCastMode.value === 'manual' || activeCastMode.value === 'online')
const usesOnlineInput = computed(() => activeCastMode.value === 'online')
const usesManualSelectInput = computed(() => activeCastMode.value === 'manual')
const castCategoryText = computed(() => category.value.trim() || '未分类')
const castTimeText = computed(() => castResult.value?.day_label || '—')
const castShenshaText = computed(() => {
  const shensha = (castResult.value?.shensha || {}) as Record<string, string>
  return [
    `卦身--${shensha.卦身 || '—'}`,
    `贵人--${shensha.贵人 || '—'}`,
    `驿马--${shensha.驿马 || '—'}`,
    `羊刃--${shensha.羊刃 || '—'}`,
  ]
})
const castPanelTitle = computed(() => castResult.value?.panel_title || '卦象')
const castPanelSubtitle = computed(() => castResult.value?.panel_subtitle || '')
const manualLineEntries = computed(() =>
  [...manualLines.value]
    .map((value, index) => {
      const option = lineOptions.find((item) => item.value === value)
      const barText = option?.barText || '—'
      const changeMark = option?.changeMark || ''
      return {
        key: `${index}-${value}`,
        label: lineLabels[index],
        value,
        optionLabel: option ? `${option.label}（${option.detail}）` : '请选择',
        barText,
        changeMark,
      }
    })
    .reverse()
)

function resetCast() {
  question.value = ''
  category.value = ''
  castSeed.value = formatCastSeed()
  manualLines.value = [0, 0, 0, 0, 0, 0]
  result.value = null
  showResultBoard.value = true
}

function randomLineOptionValue() {
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const array = new Uint32Array(1)
    crypto.getRandomValues(array)
    return lineOptions[array[0] % lineOptions.length].value
  }
  return lineOptions[Math.floor(Math.random() * lineOptions.length)].value
}

function drawOnlineLine(index: number) {
  manualLines.value[index] = randomLineOptionValue()
}

async function cast() {
  if (!question.value.trim() && !category.value.trim() && !usesManualInput.value) {
    errorMessage.value = '请先输入问念或分类。'
    return
  }
  if (usesManualInput.value && manualLines.value.some((item) => !item)) {
    errorMessage.value = usesOnlineInput.value ? '请先完成 6 次起卦。' : '请把 6 次手动输入补完整。'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    const requestCastMode = activeCastMode.value === 'online' ? 'manual' : activeCastMode.value
    const response = await requestHowToDo({
      section: 'cast',
      cast_mode: requestCastMode,
      question: question.value.trim(),
      category: category.value.trim(),
      cast_seed: castSeed.value,
      manual_lines: usesManualInput.value ? manualLines.value.map((item) => Number(item)) : [],
      use_ai: true,
    })
    if (activeCastMode.value === 'online') {
      ;(response.raw_result as Record<string, any>).cast_mode = 'online'
    }
    result.value = response
    window.localStorage.setItem('liuyao-last-result', JSON.stringify(response))
    castSeed.value = formatCastSeed()
    showResultBoard.value = true
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '排盘失败'
  } finally {
    loading.value = false
  }
}

</script>

<template>
  <section class="page-hero page-hero--single how-to-do-hero">
    <div class="hero-copy">
      <p class="eyebrow">心源六爻</p>
      <h1>排盘</h1>
      <p class="hero-text">问念或者分类，请至少输入一个。一卦一问，问念是一个卦象的重要组成部分！</p>
    </div>
  </section>

  <section class="summary-panel summary-panel--featured how-to-do-page">
    <div class="how-to-do-toggle-row">
      <button
        v-for="mode in castModes"
        :key="mode.key"
        type="button"
        class="chip-btn"
        :class="{ 'chip-btn--active': activeCastMode === mode.key }"
        @click="activeCastMode = mode.key"
      >
        {{ mode.label }}
      </button>
    </div>
    <p class="how-to-do-note">{{ castModes.find((item) => item.key === activeCastMode)?.hint }}</p>

    <label class="field-label">
      问念
      <textarea v-model="question" class="text-area" rows="4" placeholder="请输入您的问题"></textarea>
    </label>

    <label class="field-label">
      分类
      <select v-model="category" class="field-input">
        <option value="" disabled>请选择分类</option>
        <option v-for="item in questionCategories" :key="item" :value="item">{{ item }}</option>
      </select>
    </label>

    <div class="how-to-do-field-grid">
      <label class="field-label">
        起卦时间
        <input v-model="castSeed" type="text" class="field-input" />
      </label>
      <label class="field-label">
        当前时间
        <input :value="new Date().toLocaleString('zh-CN')" type="text" class="field-input" disabled />
      </label>
    </div>

    <div v-if="usesManualSelectInput" class="manual-input-stack">
      <label v-for="entry in manualLineEntries" :key="entry.key" class="field-label manual-input-item">
        <span class="manual-input-item__label">{{ entry.label }}</span>
        <div class="manual-input-item__row">
          <select v-model="manualLines[lineLabels.indexOf(entry.label)]" class="field-input">
            <option :value="0" disabled>请选择</option>
            <option v-for="option in lineOptions" :key="option.value" :value="option.value">
              {{ option.label }} {{ option.barText }}（{{ option.detail }}）
            </option>
          </select>
          <span class="manual-input-item__bars">{{ entry.barText }}</span>
          <span v-if="entry.changeMark" class="is-change-mark">{{ entry.changeMark }}</span>
        </div>
      </label>
    </div>

    <div v-if="usesOnlineInput" class="manual-input-stack">
      <label v-for="entry in manualLineEntries" :key="`online-${entry.key}`" class="field-label manual-input-item">
        <div class="manual-input-item__header">
          <span class="manual-input-item__label">{{ entry.label }}</span>
          <button
            type="button"
            class="secondary-btn manual-input-item__trigger"
            @click="drawOnlineLine(lineLabels.indexOf(entry.label))"
          >
            开始起卦
          </button>
        </div>
        <div class="manual-input-item__row manual-input-item__row--result">
          <span class="manual-input-item__option">{{ entry.optionLabel }}</span>
          <span class="manual-input-item__bars">{{ entry.barText }}</span>
          <span v-if="entry.changeMark" class="is-change-mark">{{ entry.changeMark }}</span>
        </div>
      </label>
    </div>

    <p class="how-to-do-note" v-if="usesManualSelectInput">
      从下往上依次录入 6 次结果。最下面是初爻，最上面是上爻。
    </p>

    <p class="how-to-do-note" v-if="usesOnlineInput">
      每一爻点一次“开始起卦”即可随机四选一。六次都完成后，再开始占卜。
    </p>

    <p v-else class="how-to-do-note">
      使用三枚同面值的硬币，平心静气，集中注意想自己要问的事情，手摇后扔在桌面上，记录每次几个花，几个字，从下往上依次录入。硬币起卦即金钱卦，是传统也是最靠谱的六爻卦。太极丸与硬币卦同理。
    </p>

    <div class="how-to-do-actions how-to-do-actions--left">
      <button class="secondary-btn" type="button" @click="resetCast">重置排盘信息</button>
      <button class="primary-btn" type="button" :disabled="loading" @click="cast">
        {{ loading ? '排盘中...' : '开始占卜' }}
      </button>
    </div>

    <p v-if="errorMessage" class="how-to-do-error">{{ errorMessage }}</p>

    <template v-if="result">
      <div class="liuyao-result-sheet">
        <div class="liuyao-result-meta">
          <div class="liuyao-result-meta__item">
            <span>问念：</span>
            <strong>{{ castQuestionText }}</strong>
          </div>
          <div class="liuyao-result-meta__item">
            <span>起卦方式：</span>
            <strong>{{ castModeText }}</strong>
          </div>
          <div class="liuyao-result-meta__item">
            <span>分类：</span>
            <strong>{{ castCategoryText }}</strong>
          </div>
          <div class="liuyao-result-meta__item">
            <span>时间：</span>
            <strong>{{ castTimeText }}</strong>
          </div>
          <div class="liuyao-result-meta__item">
            <span>神煞：</span>
            <strong>{{ castShenshaText.join(' / ') }}</strong>
          </div>
        </div>

        <button type="button" class="secondary-btn liuyao-expand-btn" @click="showResultBoard = !showResultBoard">
          {{ showResultBoard ? '收起' : '展开' }}
        </button>

        <div v-if="showResultBoard" class="liuyao-result-board">
          <p class="liuyao-result-board__ganzhi">{{ castResult?.ganzhi_line || castResult?.day_label || castTimeText }}</p>
          <p class="liuyao-result-board__time">{{ castResult?.day_label || castTimeText }}</p>
          <div class="liuyao-result-frame">
            <div class="liuyao-result-columns">
              <div class="liuyao-result-column">
                <div class="liuyao-result-column__header">
                  {{ castPanelTitle }}<span v-if="castPanelSubtitle">（{{ castPanelSubtitle }}）</span>
                </div>
                <div v-for="line in castLineDetails" :key="`main-${line.position}`" class="liuyao-result-line">
                  <div class="liuyao-result-line__top">
                    <span class="liuyao-result-line__spirit">{{ line.six_spirit }}</span>
                    <span class="liuyao-result-line__relation">{{ line.relation }}{{ line.stem_branch }}</span>
                    <span class="liuyao-result-line__bars">{{ line.bar_text || (line.yin_yang === '阳' ? '▅▅▅' : '▅ ▅') }}</span>
                    <span v-if="line.change_mark" class="is-change-mark">{{ line.change_mark }}</span>
                    <span v-if="line.shi_ying" class="liuyao-result-line__marker">{{ line.shi_ying }}</span>
                  </div>
                  <div v-if="line.hidden_spirit" class="liuyao-result-line__hidden">↑伏：{{ line.hidden_spirit }}</div>
                </div>
              </div>

              <div v-if="castResult?.transformed_hexagram" class="liuyao-result-column">
                <div class="liuyao-result-column__header">
                  {{ castResult.transformed_hexagram.panel_title || castResult.transformed_hexagram.name }}<span v-if="castResult.transformed_hexagram.panel_subtitle">（{{ castResult.transformed_hexagram.panel_subtitle }}）</span>
                </div>
                <div v-for="line in transformedLineDetails" :key="`transformed-${line.position}`" class="liuyao-result-line">
                  <div class="liuyao-result-line__top">
                    <span class="liuyao-result-line__spirit">{{ line.six_spirit }}</span>
                    <span class="liuyao-result-line__relation">{{ line.relation }}{{ line.stem_branch }}</span>
                    <span class="liuyao-result-line__bars">{{ line.bar_text || (line.yin_yang === '阳' ? '▅▅▅' : '▅ ▅') }}</span>
                    <span v-if="line.change_mark" class="is-change-mark">{{ line.change_mark }}</span>
                    <span v-if="line.shi_ying" class="liuyao-result-line__marker">{{ line.shi_ying }}</span>
                  </div>
                  <div v-if="line.hidden_spirit" class="liuyao-result-line__hidden">↑伏：{{ line.hidden_spirit }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </template>
  </section>
</template>

<style scoped>
.how-to-do-page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
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

.how-to-do-field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
}

.manual-input-stack {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.manual-input-item {
  margin-bottom: 0;
}

.manual-input-item__label {
  font-weight: 600;
  color: var(--text-primary);
}

.manual-input-item__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.manual-input-item__row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.manual-input-item__row--result {
  justify-content: space-between;
  padding: 0.8rem 0.95rem;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 16px;
  background: color-mix(in srgb, var(--card-bg) 92%, transparent);
}

.manual-input-item__row .field-input {
  margin: 0;
}

.manual-input-item__trigger {
  padding: 0.45rem 0.8rem;
  border-radius: 999px;
  white-space: nowrap;
}

.manual-input-item__option {
  flex: 1;
  color: var(--text-primary);
  font-size: 0.92rem;
}

.manual-input-item__bars {
  min-width: 3rem;
  font-size: 1rem;
  letter-spacing: 0.08em;
  color: var(--text-primary);
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
  flex-wrap: wrap;
}

.how-to-do-actions--left {
  justify-content: flex-start;
}

.how-to-do-error {
  margin-top: 0.75rem;
  color: #ef4444;
  font-size: 0.92rem;
}

.liuyao-result-sheet {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.liuyao-result-meta {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding-bottom: 0.9rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.liuyao-result-meta__item {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: flex-start;
  line-height: 1.55;
}

.liuyao-result-meta__item span {
  color: var(--text-secondary);
}

.liuyao-result-meta__item strong {
  color: var(--text-primary);
  font-weight: 600;
}

.liuyao-expand-btn {
  width: fit-content;
}

.liuyao-result-board {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  padding: 1rem 0;
}

.liuyao-result-board__ganzhi {
  margin: 0;
  color: var(--text-primary);
  font-size: 0.98rem;
  font-weight: 700;
  line-height: 1.5;
}

.liuyao-result-board__time {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.liuyao-result-frame {
  padding: 1rem 0;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 20px;
  background: color-mix(in srgb, var(--card-bg) 96%, transparent);
  overflow-x: auto;
}

.liuyao-result-columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
  align-items: start;
  padding: 0 1rem;
}

.liuyao-result-column {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.liuyao-result-column__header {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  padding-bottom: 0.3rem;
}

.liuyao-result-line {
  display: flex;
  flex-direction: column;
  gap: 0.08rem;
}

.liuyao-result-line__top {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
  min-height: 1.5rem;
}

.liuyao-result-line__spirit {
  font-weight: 700;
  color: var(--text-primary);
}

.liuyao-result-line__relation {
  font-size: 0.95rem;
  color: var(--text-primary);
  line-height: 1.45;
}

.liuyao-result-line__bars {
  font-size: 1rem;
  letter-spacing: 0.08em;
  color: var(--text-primary);
  white-space: nowrap;
}

.liuyao-result-line__hidden {
  font-size: 0.84rem;
  color: var(--text-secondary);
  padding-left: calc(2.8rem + 0.35rem);
}

.liuyao-result-line__marker {
  font-size: 0.9rem;
  color: var(--text-primary);
  font-weight: 700;
}

.is-change-mark {
  color: #c2410c;
  font-weight: 800;
}

@media (max-width: 768px) {
  .how-to-do-field-grid {
    grid-template-columns: 1fr;
  }

  .manual-input-item__header {
    align-items: flex-start;
    flex-direction: column;
  }

  .manual-input-item__row {
    flex-wrap: wrap;
  }

  .manual-input-item__row--result {
    align-items: flex-start;
  }

  .liuyao-result-frame {
    padding: 0.85rem 0;
  }

  .liuyao-result-columns {
    grid-template-columns: 1fr;
    padding: 0 0.85rem;
  }
}
</style>
