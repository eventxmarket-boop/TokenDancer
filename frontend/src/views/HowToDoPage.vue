<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { requestHowToDo, type HowToDoChatMessage, type HowToDoResponse } from '@/services/howToDoService'
import {
  listHowToDoHistoryRecords,
  toggleFavoriteHowToDoHistoryRecord,
  upsertHowToDoHistoryRecord,
  type HowToDoHistoryRecord,
} from '@/services/howToDoHistoryService'

type CastModeKey = 'manual' | 'coin' | 'online'

const castModes: Array<{ key: CastModeKey; label: string; hint: string }> = [
  { key: 'coin', label: '随机摇卦', hint: '平心静气后摇卦。' },
  { key: 'manual', label: '手动输入', hint: '' },
  { key: 'online', label: '在线起卦', hint: '' },
]

const questionCategoryGroups = [
  {
    key: 'travel',
    label: '出行流动',
    items: ['出行平安', '能否出行', '何时出行', '行人归来', '出国远行'],
  },
  {
    key: 'career',
    label: '工作学业',
    items: ['求官', '求职', '工作推进', '升迁调动', '项目进度', '面试入职', '考试测验', '学业文书'],
  },
  {
    key: 'money',
    label: '财运经营',
    items: ['求财', '投资买卖', '开店经营', '借贷还款'],
  },
  {
    key: 'relationship',
    label: '关系情感',
    items: ['感情回应', '感情复合', '表白推进', '朋友关系'],
  },
  {
    key: 'family',
    label: '家宅家庭',
    items: ['家宅关系', '父母长辈', '子女教育', '搬家迁移'],
  },
  {
    key: 'life',
    label: '健康和日常事务',
    items: ['健康疾病', '生产怀孕', '诉讼官非', '失物寻人'],
  },
  {
    key: 'trade',
    label: '合作交易',
    items: ['合作合伙', '交易签约'],
  },
  {
    key: 'other',
    label: '其他',
    items: ['其他'],
  },
]

const categoryGroupPrompts: Record<
  string,
  { placeholder: string; tip: string }
> = {
  travel: {
    placeholder: '例如：这趟出行能不能成行；更适合哪天出发；对方什么时候回来',
    tip: '适合直接问成不成、什么时候动、路上哪里有阻。',
  },
  career: {
    placeholder: '例如：这次高考能不能上 500 分；这次面试能不能过；这个项目什么时候能推进',
    tip: '适合直接问结果、卡点、时间窗口，问题越具体越容易断。',
  },
  money: {
    placeholder: '例如：这笔钱能不能到账；现在适不适合买入；这家店能不能做起来',
    tip: '适合直接问能不能成、多久兑现、风险点在哪。',
  },
  relationship: {
    placeholder: '例如：他现在是什么态度；这段关系还有没有推进点；适不适合表白',
    tip: '适合直接问态度、走向、推进还是收边界。',
  },
  family: {
    placeholder: '例如：这次更适合搬家还是续住；家里这件事该不该先说；和长辈会不会缓和',
    tip: '适合直接问宜守还是宜动、问题更偏关系还是现实环境。',
  },
  life: {
    placeholder: '例如：这段时间身体是急还是缓；这个东西更偏在哪个方位；这件官非会不会升级',
    tip: '适合直接问风险等级、方向位置、先防什么。',
  },
  trade: {
    placeholder: '例如：这次合作能不能成；这份合同要不要签；这笔钱回不回得来',
    tip: '适合直接问能不能落地、谁在拖、下一步该催还是该守。',
  },
  other: {
    placeholder: '例如：把你最想知道的结果直接问出来，比如会不会成、什么时候动、该不该继续',
    tip: '如果拿不准分类，至少把结果目标和时间范围说清楚。',
  },
}

const activeCastMode = ref<CastModeKey>('coin')
const question = ref('')
const category = ref('')
const categoryGroup = ref('')
const castSeed = ref('')
const manualLines = ref<number[]>([0, 0, 0, 0, 0, 0])
const loading = ref(false)
const chatLoading = ref(false)
const errorMessage = ref('')
const result = ref<HowToDoResponse | null>(null)
const showResultBoard = ref(true)
const chatInput = ref('')
const chatTurns = ref<Array<{ id: string; role: 'user' | 'assistant'; content: string }>>([])
const historyOpen = ref(false)
const historyRecords = ref<HowToDoHistoryRecord[]>([])
const activeHistoryId = ref('')
const castCategorySnapshot = ref('未分类')
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

function createId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function findCategoryGroupKey(value: string) {
  return questionCategoryGroups.find((group) => group.items.includes(value))?.key || ''
}

function refreshHistoryRecords() {
  historyRecords.value = listHowToDoHistoryRecords()
}

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
  if (mode === 'manual') return '手动输入'
  if (mode === 'character') return '汉字起卦'
  return '硬币起卦'
})
const usesManualInput = computed(() => activeCastMode.value === 'manual' || activeCastMode.value === 'online')
const usesOnlineInput = computed(() => activeCastMode.value === 'online')
const usesManualSelectInput = computed(() => activeCastMode.value === 'manual')
const onlineDrawCount = computed(() => manualLines.value.filter((item) => !!item).length)
const castCategoryText = computed(() => castCategorySnapshot.value || '未分类')
const selectedCategoryItems = computed(() => {
  return questionCategoryGroups.find((item) => item.key === categoryGroup.value)?.items ?? []
})
const activeQuestionPrompt = computed(() => {
  return categoryGroupPrompts[categoryGroup.value] ?? {
    placeholder: '例如：直接问你最想知道的结果、时间点或方向',
    tip: '先选大类后，这里会同步显示这一类更适合怎么问。',
  }
})
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
const currentHistoryRecord = computed(() =>
  historyRecords.value.find((item) => item.id === activeHistoryId.value) ?? null,
)
const currentHistoryIsFavorite = computed(() => Boolean(currentHistoryRecord.value?.favorite))
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
  categoryGroup.value = ''
  castSeed.value = formatCastSeed()
  manualLines.value = [0, 0, 0, 0, 0, 0]
  result.value = null
  showResultBoard.value = true
  chatInput.value = ''
  chatTurns.value = []
  historyOpen.value = false
  activeHistoryId.value = ''
  castCategorySnapshot.value = '未分类'
}

function handleCategoryGroupChange(value: string) {
  categoryGroup.value = value
  const items = questionCategoryGroups.find((item) => item.key === value)?.items ?? []
  category.value = items.length === 1 ? items[0] : ''
}

function onCategoryGroupChange(event: Event) {
  const target = event.target as HTMLSelectElement | null
  handleCategoryGroupChange(target?.value || '')
}

function randomLineOptionValue() {
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const array = new Uint32Array(1)
    crypto.getRandomValues(array)
    const raw = array[0]
    const backCount = (raw & 1) + ((raw >> 1) & 1) + ((raw >> 2) & 1)
    if (backCount === 0) return 6
    if (backCount === 1) return 7
    if (backCount === 2) return 8
    return 9
  }
  let backCount = 0
  for (let index = 0; index < 3; index += 1) {
    backCount += Math.random() < 0.5 ? 0 : 1
  }
  if (backCount === 0) return 6
  if (backCount === 1) return 7
  if (backCount === 2) return 8
  return 9
}

function drawOnlineLine(index: number) {
  manualLines.value[index] = randomLineOptionValue()
}

function drawNextOnlineLine() {
  const nextIndex = manualLines.value.findIndex((item) => !item)
  if (nextIndex === -1) return
  drawOnlineLine(nextIndex)
}

function buildHistoryRecord(baseResult: HowToDoResponse, historyId = activeHistoryId.value || createId('howtodo-history')) {
  const existing = historyRecords.value.find((item) => item.id === historyId)
  const now = new Date().toISOString()
  return {
    id: historyId,
    title: question.value.trim() || castQuestionText.value,
    question: question.value.trim() || castQuestionText.value,
    category: castCategorySnapshot.value || category.value.trim() || '未分类',
    castMode: castModeText.value,
    createdAt: existing?.createdAt || now,
    updatedAt: now,
    favorite: existing?.favorite || false,
    result: baseResult,
    chatTurns: chatTurns.value.map((item) => ({ ...item })),
  } satisfies HowToDoHistoryRecord
}

function syncActiveHistory() {
  if (!result.value) return
  const record = buildHistoryRecord(result.value)
  activeHistoryId.value = record.id
  upsertHowToDoHistoryRecord(record)
  refreshHistoryRecords()
}

function loadHistoryRecord(record: HowToDoHistoryRecord) {
  activeHistoryId.value = record.id
  result.value = record.result
  question.value = record.question
  category.value = record.category === '未分类' ? '' : record.category
  categoryGroup.value = findCategoryGroupKey(category.value)
  castCategorySnapshot.value = record.category || '未分类'
  chatTurns.value = record.chatTurns.map((item) => ({ ...item }))
  chatInput.value = ''
  showResultBoard.value = true
  historyOpen.value = false
  activeCastMode.value =
    record.result.raw_result?.cast_mode === 'online'
      ? 'online'
      : record.result.raw_result?.cast_mode === 'manual'
        ? 'manual'
        : 'coin'
}

function toggleCurrentFavorite() {
  if (!activeHistoryId.value) return
  toggleFavoriteHowToDoHistoryRecord(activeHistoryId.value)
  refreshHistoryRecords()
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
    chatTurns.value = []
    if (question.value.trim()) {
      chatTurns.value.push({
        id: `user-${Date.now()}`,
        role: 'user',
        content: question.value.trim(),
      })
    }
    if (response.ai_interpretation.trim()) {
      chatTurns.value.push({
        id: `assistant-${Date.now() + 1}`,
        role: 'assistant',
        content: response.ai_interpretation.trim(),
      })
    }
    castCategorySnapshot.value = category.value.trim() || '未分类'
    window.localStorage.setItem('liuyao-last-result', JSON.stringify(response))
    castSeed.value = formatCastSeed()
    showResultBoard.value = true
    activeHistoryId.value = createId('howtodo-history')
    syncActiveHistory()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '排盘失败'
  } finally {
    loading.value = false
  }
}

function buildCastContext() {
  return {
    question: question.value.trim(),
    category: category.value.trim(),
    cast_mode: castResult.value?.cast_mode || activeCastMode.value,
    summary: result.value?.summary || '',
    raw_result: result.value?.raw_result || {},
  }
}

async function sendChatFollowup() {
  const content = chatInput.value.trim()
  if (!content || !result.value) return
  const userTurn = {
    id: `user-${Date.now()}`,
    role: 'user' as const,
    content,
  }
  chatTurns.value.push(userTurn)
  chatInput.value = ''
  chatLoading.value = true
  errorMessage.value = ''
  try {
    const response = await requestHowToDo({
      section: 'chat',
      user_message: content,
      use_ai: true,
      cast_context: buildCastContext(),
      conversation_history: chatTurns.value.map(
        (item): HowToDoChatMessage => ({
          role: item.role,
          content: item.content,
        }),
      ),
    })
    chatTurns.value.push({
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: response.ai_interpretation.trim(),
    })
    syncActiveHistory()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '追问失败'
  } finally {
    chatLoading.value = false
  }
}

onMounted(() => {
  refreshHistoryRecords()
})
</script>

<template>
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
      <button
        type="button"
        class="chip-btn"
        :class="{ 'chip-btn--active': historyOpen }"
        @click="historyOpen = !historyOpen"
      >
        历史
      </button>
      <button
        type="button"
        class="chip-btn"
        :class="{ 'chip-btn--active': currentHistoryIsFavorite }"
        :disabled="!activeHistoryId"
        @click="toggleCurrentFavorite"
      >
        {{ currentHistoryIsFavorite ? '已收藏' : '收藏' }}
      </button>
    </div>
    <p v-if="castModes.find((item) => item.key === activeCastMode)?.hint" class="how-to-do-note">
      {{ castModes.find((item) => item.key === activeCastMode)?.hint }}
    </p>

    <label class="field-label">
      问念
      <textarea
        v-model="question"
        class="text-area"
        rows="4"
        :placeholder="activeQuestionPrompt.placeholder"
      ></textarea>
    </label>
    <p class="how-to-do-note">{{ activeQuestionPrompt.tip }}</p>

    <div class="how-to-do-field-grid how-to-do-field-grid--category">
      <label class="field-label">
        分类大类
        <select :value="categoryGroup" class="field-input" @change="onCategoryGroupChange">
          <option value="" disabled>请选择大类</option>
          <option v-for="group in questionCategoryGroups" :key="group.key" :value="group.key">{{ group.label }}</option>
        </select>
      </label>

      <label class="field-label">
        具体分类
        <select v-model="category" class="field-input" :disabled="!categoryGroup">
          <option value="" disabled>请选择具体分类</option>
          <option v-for="item in selectedCategoryItems" :key="item" :value="item">{{ item }}</option>
        </select>
      </label>
    </div>

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
      <div class="online-cast-toolbar">
        <button
          type="button"
          class="secondary-btn online-cast-toolbar__button"
          :disabled="onlineDrawCount >= 6"
          @click="drawNextOnlineLine"
        >
          {{ onlineDrawCount >= 6 ? '起卦完成' : '开始起卦' }}
        </button>
        <span class="online-cast-toolbar__status">已起 {{ onlineDrawCount }}/6 爻</span>
      </div>
      <label v-for="entry in manualLineEntries" :key="`online-${entry.key}`" class="field-label manual-input-item">
        <div class="manual-input-item__header">
          <span class="manual-input-item__label">{{ entry.label }}</span>
        </div>
        <div class="manual-input-item__row manual-input-item__row--result">
          <span class="manual-input-item__option">{{ entry.optionLabel }}</span>
          <span class="manual-input-item__bars">{{ entry.barText }}</span>
          <span v-if="entry.changeMark" class="is-change-mark">{{ entry.changeMark }}</span>
        </div>
      </label>
    </div>

    <p class="how-to-do-note" v-if="usesOnlineInput">
      请集中精力，默想所占之事，点击“开始起卦”后，可求得一爻，反复6次。
    </p>

    <div class="how-to-do-actions how-to-do-actions--left">
      <button class="secondary-btn" type="button" @click="resetCast">重置排盘信息</button>
      <button class="primary-btn" type="button" :disabled="loading" @click="cast">
        {{ loading ? '排盘中...' : '开始占卜' }}
      </button>
    </div>

    <p v-if="errorMessage" class="how-to-do-error">{{ errorMessage }}</p>

    <div v-if="historyOpen" class="liuyao-history-panel">
      <div class="liuyao-history-panel__head">
        <h3>历史卦象</h3>
        <span class="status-pill">{{ historyRecords.length }} 条</span>
      </div>
      <div v-if="historyRecords.length" class="liuyao-history-list">
        <button
          v-for="item in historyRecords"
          :key="item.id"
          type="button"
          class="liuyao-history-item"
          :class="{ 'liuyao-history-item--active': item.id === activeHistoryId }"
          @click="loadHistoryRecord(item)"
        >
          <div class="liuyao-history-item__title">
            <strong>{{ item.title || '未命名卦象' }}</strong>
            <span v-if="item.favorite" class="status-pill">收藏</span>
          </div>
          <p>{{ item.category }} · {{ item.castMode }}</p>
          <p>{{ new Date(item.updatedAt).toLocaleString('zh-CN') }}</p>
        </button>
      </div>
      <div v-else class="empty-panel empty-panel--compact liuyao-history-empty">
        <h3>还没有历史卦象。</h3>
        <p class="empty-panel__copy">起一卦后，这里会保留卦象和对话记录。</p>
      </div>
    </div>

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

        <div class="liuyao-result-toolbar">
          <button type="button" class="secondary-btn liuyao-expand-btn" @click="showResultBoard = !showResultBoard">
            {{ showResultBoard ? '收起' : '展开' }}
          </button>
        </div>

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

        <div class="howtodo-chat-sheet">
          <div class="howtodo-chat-list">
            <div
              v-for="turn in chatTurns"
              :key="turn.id"
              class="howtodo-chat-bubble"
              :class="turn.role === 'user' ? 'howtodo-chat-bubble--user' : 'howtodo-chat-bubble--assistant'"
            >
              {{ turn.content }}
            </div>
          </div>
          <div class="howtodo-chat-composer">
            <textarea
              v-model="chatInput"
              class="text-area howtodo-chat-composer__input"
              rows="3"
              placeholder="继续问这卦怎么理解"
            ></textarea>
            <button class="primary-btn" type="button" :disabled="chatLoading || !chatInput.trim()" @click="sendChatFollowup">
              {{ chatLoading ? '回答中...' : '发送' }}
            </button>
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

.online-cast-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}

.online-cast-toolbar__button {
  border-radius: 999px;
  white-space: nowrap;
}

.online-cast-toolbar__status {
  color: var(--text-secondary);
  font-size: 0.88rem;
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

.liuyao-result-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.liuyao-history-panel {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  padding: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 22px;
  background: color-mix(in srgb, var(--card-bg) 94%, transparent);
}

.liuyao-history-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.liuyao-history-panel__head h3 {
  margin: 0;
  font-size: 1rem;
}

.liuyao-history-list {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.liuyao-history-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  text-align: left;
  padding: 0.9rem 1rem;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: color-mix(in srgb, var(--card-bg) 97%, transparent);
  color: var(--text-primary);
}

.liuyao-history-item--active {
  border-color: color-mix(in srgb, var(--brand) 34%, rgba(148, 163, 184, 0.16));
  background: color-mix(in srgb, var(--brand) 10%, var(--card-bg));
}

.liuyao-history-item__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.liuyao-history-item p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.88rem;
}

.liuyao-history-empty {
  min-height: 0;
}

.howtodo-chat-sheet {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.howtodo-chat-list {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.howtodo-chat-bubble {
  max-width: min(92%, 760px);
  padding: 0.9rem 1rem;
  border-radius: 18px;
  line-height: 1.7;
  font-size: 0.95rem;
  white-space: pre-wrap;
}

.howtodo-chat-bubble--assistant {
  align-self: flex-start;
  background: color-mix(in srgb, var(--card-bg) 96%, transparent);
  border: 1px solid rgba(148, 163, 184, 0.18);
  color: var(--text-primary);
}

.howtodo-chat-bubble--user {
  align-self: flex-end;
  background: color-mix(in srgb, var(--brand) 16%, var(--card-bg));
  color: var(--text-primary);
}

.howtodo-chat-composer {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.howtodo-chat-composer__input {
  min-height: 92px;
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

  .online-cast-toolbar {
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
