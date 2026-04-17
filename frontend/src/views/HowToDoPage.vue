<script setup lang="ts">
import { computed, ref } from 'vue'
import { requestHowToDo, type HowToDoResponse } from '@/services/howToDoService'

const castModes: Array<{ key: 'manual' | 'coin' | 'number' | 'taiji'; label: string; hint: string }> = [
  { key: 'coin', label: '随机摇卦', hint: '平心静气后摇卦。' },
  { key: 'manual', label: '手动输入', hint: '按 6 次依次录入。' },
  { key: 'number', label: '数字起卦', hint: '数字、编号或号码。' },
  { key: 'taiji', label: '太极丸起卦', hint: '按太极丸方式起局。' },
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

const activeCastMode = ref<'manual' | 'coin' | 'number' | 'taiji'>('coin')
const question = ref('')
const category = ref('')
const castSeed = ref('')
const castText = ref('')
const manualLines = ref<number[]>([0, 0, 0, 0, 0, 0])
const loading = ref(false)
const errorMessage = ref('')
const result = ref<HowToDoResponse | null>(null)
const showResultBoard = ref(true)
const lineOptions = [
  { value: 6, label: '6 老阴' },
  { value: 7, label: '7 少阳' },
  { value: 8, label: '8 少阴' },
  { value: 9, label: '9 老阳' },
]

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
  if (mode === 'manual') return '手动输入'
  if (mode === 'number') return '数字起卦'
  return '硬币 / 太极丸起卦'
})
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

function resetCast() {
  question.value = ''
  category.value = ''
  castSeed.value = formatCastSeed()
  castText.value = ''
  manualLines.value = [0, 0, 0, 0, 0, 0]
  result.value = null
  showResultBoard.value = true
}

async function cast() {
  if (!question.value.trim() && !category.value.trim() && activeCastMode.value !== 'manual') {
    errorMessage.value = '请先输入问念或分类。'
    return
  }
  if (activeCastMode.value === 'manual' && manualLines.value.some((item) => !item)) {
    errorMessage.value = '请把 6 次手动输入补完整。'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await requestHowToDo({
      section: 'cast',
      cast_mode: activeCastMode.value,
      question: question.value.trim(),
      category: category.value.trim(),
      cast_seed: castSeed.value,
      manual_lines: activeCastMode.value === 'manual' ? manualLines.value.map((item) => Number(item)) : [],
      number_text: activeCastMode.value === 'number' ? castText.value.trim() : '',
      use_ai: true,
    })
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

    <div v-if="activeCastMode === 'manual'" class="manual-input-grid">
      <label v-for="(label, index) in ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']" :key="label" class="field-label">
        {{ label }}
        <select v-model="manualLines[index]" class="field-input">
          <option :value="0" disabled>请选择</option>
          <option v-for="option in lineOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
      </label>
    </div>

    <label v-if="activeCastMode === 'number'" class="field-label">
      数字
      <textarea
        v-model="castText"
        class="text-area"
        rows="3"
        placeholder="输入数字、编号或数字串。"
      ></textarea>
    </label>

    <p class="how-to-do-note">
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
          <div class="liuyao-result-board__titles">
            <p class="liuyao-result-board__title">{{ castPanelTitle }}<span v-if="castPanelSubtitle">（{{ castPanelSubtitle }}）</span></p>
          </div>

          <div class="liuyao-result-frame">
            <div class="liuyao-result-boards__item">
              <div class="liuyao-line-board">
                <div
                  v-for="line in castLineDetails"
                  :key="line.position"
                  class="liuyao-line-board__row"
                  :class="{ 'is-changing': line.is_changing }"
                >
                  <div class="liuyao-line-board__spirit">{{ line.six_spirit }}</div>
                  <div class="liuyao-line-board__content">
                    <div class="liuyao-line-board__relation">{{ line.relation }}{{ line.stem_branch }}</div>
                    <div v-if="line.hidden_spirit" class="liuyao-line-board__hidden">↑伏：{{ line.hidden_spirit }}</div>
                    <div class="liuyao-line-board__bars">{{ line.is_changing ? '▅ ▅' : '▅▅▅' }}</div>
                    <div class="liuyao-line-board__tags">
                      <span v-if="line.shi_ying">{{ line.shi_ying }}</span>
                      <span>{{ line.nayin }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="castResult?.transformed_hexagram" class="liuyao-result-boards__item">
              <p class="liuyao-result-board__title liuyao-result-board__title--right">
                {{ castResult.transformed_hexagram.name }}（{{ castResult.transformed_hexagram.upper_trigram }}·{{ castResult.transformed_hexagram.lower_trigram }}）
              </p>
              <div class="liuyao-line-board">
                <div
                  v-for="line in transformedLineDetails"
                  :key="`transformed-${line.position}`"
                  class="liuyao-line-board__row"
                  :class="{ 'is-changing': line.is_changing }"
                >
                  <div class="liuyao-line-board__spirit">{{ line.six_spirit }}</div>
                  <div class="liuyao-line-board__content">
                    <div class="liuyao-line-board__relation">{{ line.relation }}{{ line.stem_branch }}</div>
                    <div v-if="line.hidden_spirit" class="liuyao-line-board__hidden">↑伏：{{ line.hidden_spirit }}</div>
                    <div class="liuyao-line-board__bars">{{ line.is_changing ? '▅ ▅' : '▅▅▅' }}</div>
                    <div class="liuyao-line-board__tags">
                      <span v-if="line.shi_ying">{{ line.shi_ying }}</span>
                      <span>{{ line.nayin }}</span>
                    </div>
                  </div>
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

.manual-input-grid {
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

.liuyao-result-board__titles {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem 1rem;
  align-items: baseline;
}

.liuyao-result-board__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
}

.liuyao-result-board__title--right {
  text-align: right;
}

.liuyao-result-frame {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 1rem;
  align-items: start;
  padding: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 20px;
  background: color-mix(in srgb, var(--card-bg) 96%, transparent);
}

.liuyao-result-boards__item {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 0.25rem 0 0;
}

.liuyao-line-board {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.liuyao-line-board__row {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr);
  gap: 0.75rem;
  align-items: start;
  padding: 0.7rem 0.8rem;
  border-radius: 16px;
  background: color-mix(in srgb, var(--card-bg) 94%, transparent);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.liuyao-line-board__row.is-changing {
  border-color: rgba(59, 130, 246, 0.28);
}

.liuyao-line-board__spirit {
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.5;
}

.liuyao-line-board__content {
  display: flex;
  flex-direction: column;
  gap: 0.18rem;
}

.liuyao-line-board__relation {
  font-size: 0.95rem;
  color: var(--text-primary);
}

.liuyao-line-board__hidden {
  font-size: 0.88rem;
  color: var(--text-secondary);
}

.liuyao-line-board__bars {
  font-size: 1rem;
  letter-spacing: 0.08em;
  color: var(--text-primary);
}

.liuyao-line-board__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.6rem;
  font-size: 0.84rem;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .how-to-do-field-grid {
    grid-template-columns: 1fr;
  }

  .manual-input-grid {
    grid-template-columns: 1fr;
  }

  .liuyao-result-frame {
    grid-template-columns: 1fr;
  }
}
</style>
