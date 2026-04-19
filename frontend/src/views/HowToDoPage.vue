<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { requestHowToDo, type HowToDoChatMessage, type HowToDoResponse } from '@/services/howToDoService'
import {
  loadHowToDoHistoryRecords,
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
const chatTurns = ref<Array<{ id: string; role: 'user' | 'assistant'; content: string }>>([])
const historyRecords = ref<HowToDoHistoryRecord[]>([])
const activeHistoryId = ref('')
const castCategorySnapshot = ref('未分类')
const route = useRoute()
const router = useRouter()
const menuOpen = ref(false)
const modePickerOpen = ref(false)
const categoryPickerOpen = ref(false)
const timePickerOpen = ref(false)
const howtodoScrollRef = ref<HTMLDivElement | null>(null)
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

async function refreshHistoryRecords() {
  historyRecords.value = await loadHowToDoHistoryRecords()
}

async function scrollHowToDoToBottom() {
  await nextTick()
  const el = howtodoScrollRef.value
  if (!el) return
  el.scrollTop = el.scrollHeight
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
const selectedCategoryGroupLabel = computed(
  () => questionCategoryGroups.find((item) => item.key === categoryGroup.value)?.label || '',
)
const selectedCategoryLabel = computed(() => category.value || selectedCategoryGroupLabel.value || '选择分类')
const selectedModeLabel = computed(() => {
  const item = castModes.find((mode) => mode.key === activeCastMode.value)
  return item?.label || '选择起卦方式'
})
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
  chatTurns.value = []
  activeHistoryId.value = ''
  castCategorySnapshot.value = '未分类'
  menuOpen.value = false
  closePickers()
}

function handleCategoryGroupChange(value: string) {
  categoryGroup.value = value
  const items = questionCategoryGroups.find((item) => item.key === value)?.items ?? []
  category.value = items.length === 1 ? items[0] : ''
}

function openModePicker() {
  menuOpen.value = false
  categoryPickerOpen.value = false
  timePickerOpen.value = false
  modePickerOpen.value = !modePickerOpen.value
}

function openCategoryPicker() {
  menuOpen.value = false
  modePickerOpen.value = false
  timePickerOpen.value = false
  if (!categoryGroup.value && questionCategoryGroups.length) {
    handleCategoryGroupChange(questionCategoryGroups[0].key)
  }
  categoryPickerOpen.value = !categoryPickerOpen.value
}

function openTimePicker() {
  menuOpen.value = false
  modePickerOpen.value = false
  categoryPickerOpen.value = false
  timePickerOpen.value = !timePickerOpen.value
}

function closePickers() {
  modePickerOpen.value = false
  categoryPickerOpen.value = false
  timePickerOpen.value = false
}

function selectCastMode(mode: CastModeKey) {
  activeCastMode.value = mode
  modePickerOpen.value = false
}

function selectCategoryGroupByKey(key: string) {
  handleCategoryGroupChange(key)
}

function selectCategoryItemByValue(item: string) {
  category.value = item
  categoryPickerOpen.value = false
}

function confirmCastSeed() {
  castSeed.value = castSeed.value.trim() || formatCastSeed()
  timePickerOpen.value = false
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
  void refreshHistoryRecords()
}

function loadHistoryRecord(record: HowToDoHistoryRecord) {
  activeHistoryId.value = record.id
  result.value = record.result
  question.value = record.question
  category.value = record.category === '未分类' ? '' : record.category
  categoryGroup.value = findCategoryGroupKey(category.value)
  castCategorySnapshot.value = record.category || '未分类'
  chatTurns.value = record.chatTurns.map((item) => ({ ...item }))
  showResultBoard.value = true
  activeCastMode.value =
    record.result.raw_result?.cast_mode === 'online'
      ? 'online'
      : record.result.raw_result?.cast_mode === 'manual'
        ? 'manual'
        : 'coin'
  menuOpen.value = false
  void scrollHowToDoToBottom()
}

function toggleCurrentFavorite() {
  if (!activeHistoryId.value) return
  toggleFavoriteHowToDoHistoryRecord(activeHistoryId.value)
  void refreshHistoryRecords()
}

function goToHowToDoArchive(tab: 'history' | 'favorites') {
  menuOpen.value = false
  void router.push({
    path: '/archive/how-to-do',
    query: {
      tab,
    },
  })
}

function toggleMenu() {
  menuOpen.value = !menuOpen.value
  closePickers()
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
    question.value = ''
    void scrollHowToDoToBottom()
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
  const content = question.value.trim()
  if (!content || !result.value) return
  const userTurn = {
    id: `user-${Date.now()}`,
    role: 'user' as const,
    content,
  }
  chatTurns.value.push(userTurn)
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
    question.value = ''
    void scrollHowToDoToBottom()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '追问失败'
  } finally {
    chatLoading.value = false
  }
}

onMounted(() => {
  void (async () => {
    await refreshHistoryRecords()
    const historyId = String(route.query.history || '').trim()
    if (!historyId) {
      void scrollHowToDoToBottom()
      return
    }
    const record = historyRecords.value.find((item) => item.id === historyId)
    if (record) {
      loadHistoryRecord(record)
    }
    void scrollHowToDoToBottom()
  })()
})
</script>

<template>
  <section class="section-card reply-shell how-to-do-shell">
    <button class="reply-history-toggle" type="button" aria-label="查看菜单" @click="toggleMenu">
      <span></span>
      <span></span>
      <span></span>
    </button>

    <transition name="fade">
      <aside v-if="menuOpen" class="reply-history-panel how-to-do-menu">
        <div class="reply-history-panel__head">
          <button class="ghost-button ghost-button--small" type="button" @click="resetCast">新对话</button>
          <button
            class="ghost-button ghost-button--small"
            type="button"
            :disabled="!activeHistoryId"
            @click="toggleCurrentFavorite"
          >
            {{ currentHistoryIsFavorite ? '取消收藏' : '收藏对话' }}
          </button>
        </div>
        <div class="reply-history-panel__links">
          <button type="button" class="reply-history-link" @click="goToHowToDoArchive('history')">历史</button>
          <button type="button" class="reply-history-link" @click="goToHowToDoArchive('favorites')">收藏</button>
        </div>
      </aside>
    </transition>

    <transition name="fade">
      <aside v-if="modePickerOpen" class="howtodo-picker-sheet">
        <div class="howtodo-picker-sheet__head">
          <h3>起卦方式</h3>
          <button type="button" class="ghost-button ghost-button--small" @click="closePickers">关闭</button>
        </div>
        <div class="howtodo-picker-list">
          <button
            v-for="mode in castModes"
            :key="mode.key"
            type="button"
            class="howtodo-picker-option"
            :class="{ 'howtodo-picker-option--active': activeCastMode === mode.key }"
            @click="selectCastMode(mode.key)"
          >
            <strong>{{ mode.label }}</strong>
            <span v-if="mode.hint">{{ mode.hint }}</span>
          </button>
        </div>
      </aside>
    </transition>

    <transition name="fade">
      <aside v-if="categoryPickerOpen" class="howtodo-picker-sheet howtodo-picker-sheet--large">
        <div class="howtodo-picker-sheet__head">
          <h3>分类</h3>
          <button type="button" class="ghost-button ghost-button--small" @click="closePickers">关闭</button>
        </div>
        <div class="howtodo-category-picker">
          <div class="howtodo-category-groups">
            <button
              v-for="group in questionCategoryGroups"
              :key="group.key"
              type="button"
              class="howtodo-category-group"
              :class="{ 'howtodo-category-group--active': categoryGroup === group.key }"
              @click="selectCategoryGroupByKey(group.key)"
            >
              {{ group.label }}
            </button>
          </div>
          <div class="howtodo-category-items">
            <button
              v-for="item in selectedCategoryItems"
              :key="item"
              type="button"
              class="howtodo-category-item"
              :class="{ 'howtodo-category-item--active': category === item }"
              @click="selectCategoryItemByValue(item)"
            >
              {{ item }}
            </button>
          </div>
        </div>
      </aside>
    </transition>

    <transition name="fade">
      <aside v-if="timePickerOpen" class="howtodo-picker-sheet">
        <div class="howtodo-picker-sheet__head">
          <h3>时间</h3>
          <button type="button" class="ghost-button ghost-button--small" @click="closePickers">关闭</button>
        </div>
        <div class="howtodo-time-picker">
          <label class="field-label">
            <span class="reply-input__label">起卦时间</span>
            <input v-model="castSeed" type="text" class="field-input" />
          </label>
          <label class="field-label">
            <span class="reply-input__label">当前时间</span>
            <input :value="new Date().toLocaleString('zh-CN')" type="text" class="field-input" disabled />
          </label>
        </div>
        <div class="howtodo-picker-sheet__actions">
          <button type="button" class="primary-btn" @click="confirmCastSeed">确定</button>
        </div>
      </aside>
    </transition>

    <div ref="howtodoScrollRef" class="howtodo-dialog-scroll">
      <div class="howtodo-assembly">
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
          <p class="how-to-do-note">
            请集中精力，默想所占之事，点击“开始起卦”后，可求得一爻，反复6次。
          </p>
        </div>
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

          <div class="liuyao-result-toolbar">
            <button type="button" class="secondary-btn liuyao-expand-btn" @click="showResultBoard = !showResultBoard">
              {{ showResultBoard ? '收起' : '展开' }}
            </button>
            <button
              type="button"
              class="secondary-btn liuyao-expand-btn"
              :disabled="!activeHistoryId"
              @click="toggleCurrentFavorite"
            >
              {{ currentHistoryIsFavorite ? '取消收藏' : '收藏' }}
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
        </div>
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
      </template>
    </div>

    <div class="howtodo-chat-sheet">
      <div class="howtodo-chat-composer">
        <label class="reply-input">
          <span class="reply-input__label">{{ result ? '继续问这卦' : '问念' }}</span>
          <textarea
            v-model="question"
            class="field-input reply-input__textarea howtodo-chat-composer__input"
            rows="3"
            :placeholder="result ? '继续问这卦怎么理解' : activeQuestionPrompt.placeholder"
          ></textarea>
        </label>
        <div class="howtodo-chat-sheet__controls">
          <button type="button" class="reply-chip reply-chip--picker" @click="openModePicker">
            <span class="reply-chip__label">起卦方式</span>
            <strong>{{ selectedModeLabel }}</strong>
          </button>
          <button type="button" class="reply-chip reply-chip--picker" @click="openCategoryPicker">
            <span class="reply-chip__label">分类</span>
            <strong>{{ selectedCategoryLabel }}</strong>
          </button>
          <button type="button" class="reply-chip reply-chip--picker" @click="openTimePicker">
            <span class="reply-chip__label">时间</span>
            <strong>{{ castSeed }}</strong>
          </button>
        </div>
        <button
          class="primary-btn"
          type="button"
          :disabled="chatLoading || loading || !question.trim()"
          @click="result ? sendChatFollowup() : cast()"
        >
          {{ chatLoading ? '回答中...' : loading ? '排盘中...' : result ? '发送' : '开始占卜' }}
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.reply-shell {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  height: min(920px, calc(100dvh - 156px));
  min-height: 0;
  overflow: hidden;
  padding-top: 3rem;
  padding-bottom: 1rem;
}

.reply-history-toggle {
  position: absolute;
  top: 0.9rem;
  left: 0.9rem;
  z-index: 6;
  display: inline-flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.23rem;
  width: 42px;
  height: 42px;
  border: 1px solid rgba(127, 140, 172, 0.2);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 20px rgba(32, 40, 60, 0.08);
}

.reply-history-toggle span {
  display: block;
  width: 18px;
  height: 2px;
  margin: 0 auto;
  border-radius: 999px;
  background: var(--text-primary, var(--text));
}

.reply-history-panel {
  position: absolute;
  top: 3.8rem;
  left: 0.9rem;
  z-index: 5;
  width: min(340px, calc(100vw - 1.8rem));
  padding: 0.9rem;
  border: 1px solid rgba(127, 140, 172, 0.16);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 24px 50px rgba(24, 32, 57, 0.16);
  backdrop-filter: blur(18px);
}

.reply-history-panel__head {
  display: flex;
  justify-content: flex-start;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.reply-history-panel__links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.reply-history-link {
  flex: 1 1 0;
  min-width: 0;
  min-height: 42px;
  padding: 0.55rem 0.8rem;
  border: 1px solid rgba(127, 140, 172, 0.16);
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.94);
  color: var(--text);
  font-weight: 700;
}

.reply-history-link:hover,
.reply-history-link:focus-visible {
  border-color: rgba(96, 110, 220, 0.32);
  background: rgba(242, 245, 255, 0.98);
}

.howtodo-composer {
  display: grid;
  gap: 0.75rem;
  padding: 0.82rem;
  border: 1px solid rgba(127, 140, 172, 0.16);
  border-radius: 24px;
  background: rgba(252, 253, 255, 0.96);
  box-shadow: 0 18px 40px rgba(24, 32, 57, 0.08);
  backdrop-filter: blur(18px);
}

.howtodo-composer__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.reply-chip {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.16rem;
  border: 1px solid rgba(127, 140, 172, 0.18);
  border-radius: 999px;
  padding: 0.45rem 0.78rem;
  background: #fff;
  font-weight: 700;
  color: var(--text-primary, var(--text));
}

.reply-chip--picker {
  min-width: 0;
  flex: 1 1 0;
}

.reply-chip__label {
  font-size: 0.72rem;
  color: var(--text-secondary, var(--muted));
  font-weight: 600;
}

.reply-chip strong {
  font-size: 0.9rem;
  font-weight: 800;
  line-height: 1.25;
}

.reply-input {
  display: grid;
  gap: 0.38rem;
}

.reply-input__label {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-secondary, var(--muted));
}

.reply-input__textarea {
  min-height: 78px;
  resize: none;
}

.howtodo-composer__actions {
  display: flex;
  justify-content: space-between;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.howtodo-assembly {
  display: grid;
  gap: 0.7rem;
}

.howtodo-picker-sheet {
  position: absolute;
  top: 6rem;
  left: 50%;
  z-index: 8;
  width: min(760px, calc(100vw - 1.8rem));
  transform: translateX(-50%);
  display: grid;
  gap: 0.8rem;
  padding: 0.84rem;
  border: 1px solid rgba(127, 140, 172, 0.16);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 24px 50px rgba(24, 32, 57, 0.16);
}

.howtodo-picker-sheet--large {
  gap: 0.8rem;
}

.howtodo-picker-sheet__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.howtodo-picker-sheet__head h3 {
  margin: 0;
  font-size: 0.98rem;
}

.howtodo-picker-sheet__actions {
  display: flex;
  justify-content: flex-end;
}

.howtodo-picker-list {
  display: grid;
  gap: 0.52rem;
}

.howtodo-picker-option {
  display: grid;
  gap: 0.2rem;
  padding: 0.72rem 0.84rem;
  border-radius: 18px;
  border: 1px solid rgba(127, 140, 172, 0.16);
  background: rgba(248, 250, 252, 0.94);
  color: var(--text);
  text-align: left;
}

.howtodo-picker-option strong {
  font-size: 0.93rem;
}

.howtodo-picker-option span {
  color: var(--muted);
  font-size: 0.8rem;
}

.howtodo-picker-option--active {
  border-color: rgba(96, 110, 220, 0.32);
  background: rgba(242, 245, 255, 0.98);
}

.howtodo-category-picker {
  display: grid;
  grid-template-columns: minmax(128px, 0.9fr) minmax(0, 1.4fr);
  gap: 0.72rem;
}

.howtodo-category-groups,
.howtodo-category-items {
  display: grid;
  gap: 0.48rem;
}

.howtodo-category-groups {
  max-height: 52vh;
  overflow: auto;
}

.howtodo-category-group,
.howtodo-category-item {
  padding: 0.64rem 0.76rem;
  border-radius: 16px;
  border: 1px solid rgba(127, 140, 172, 0.16);
  background: rgba(248, 250, 252, 0.94);
  color: var(--text);
  text-align: left;
  font-weight: 700;
}

.howtodo-category-group--active,
.howtodo-category-item--active {
  border-color: rgba(96, 110, 220, 0.32);
  background: rgba(242, 245, 255, 0.98);
}

.howtodo-time-picker {
  display: grid;
  gap: 0.7rem;
}

.how-to-do-page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field-label {
  display: flex;
  flex-direction: column;
  gap: 0.38rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 0.7rem;
}

.field-input,
.text-area {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 16px;
  background: color-mix(in srgb, var(--card-bg) 92%, transparent);
  color: var(--text-primary);
  padding: 0.65rem 0.85rem;
  font-size: 0.94rem;
  outline: none;
}

.text-area {
  resize: none;
  min-height: 76px;
}

.manual-input-stack {
  display: flex;
  flex-direction: column;
  gap: 0.62rem;
}

.online-cast-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
  margin-bottom: 0.15rem;
}

.online-cast-toolbar__button {
  border-radius: 999px;
  white-space: nowrap;
}

.online-cast-toolbar__status {
  color: var(--text-secondary);
  font-size: 0.86rem;
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
  gap: 0.5rem;
}

.manual-input-item__row--result {
  justify-content: space-between;
  padding: 0.68rem 0.82rem;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 16px;
  background: color-mix(in srgb, var(--card-bg) 92%, transparent);
}

.manual-input-item__row .field-input {
  margin: 0;
}

.manual-input-item__trigger {
  padding: 0.38rem 0.72rem;
  border-radius: 999px;
  white-space: nowrap;
}

.manual-input-item__option {
  flex: 1;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.manual-input-item__bars {
  min-width: 3rem;
  font-size: 0.96rem;
  letter-spacing: 0.08em;
  color: var(--text-primary);
}

.how-to-do-note {
  margin: 0 0 0.9rem;
  font-size: 0.86rem;
  line-height: 1.5;
  color: var(--text-secondary);
}

.how-to-do-note--compact {
  margin-bottom: 0;
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
  gap: 0.72rem;
  padding: 0.95rem;
  border: 1px solid rgba(127, 140, 172, 0.16);
  border-radius: 24px;
  background: rgba(252, 253, 255, 0.96);
  box-shadow: 0 18px 40px rgba(24, 32, 57, 0.08);
  backdrop-filter: blur(18px);
}

.howtodo-dialog-scroll {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding-right: 2px;
  scrollbar-gutter: stable;
}

.howtodo-chat-sheet__controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
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
  line-height: 1.65;
  font-size: 0.93rem;
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
  gap: 0.62rem;
}

.howtodo-chat-composer__input {
  min-height: 78px;
  font-size: 0.92rem;
  line-height: 1.5;
  resize: none;
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

  .reply-shell {
    height: calc(100dvh - 124px);
    padding-top: 3.4rem;
  }

  .howtodo-chat-bubble {
    font-size: 0.91rem;
    line-height: 1.62;
  }

  .howtodo-chat-composer__input {
    font-size: 0.91rem;
  }

  .howtodo-category-picker {
    grid-template-columns: 1fr;
  }

  .howtodo-composer__actions {
    align-items: stretch;
  }

  .howtodo-composer__chips {
    gap: 0.45rem;
  }

  .reply-chip--picker {
    flex: 1 1 100%;
  }
}
</style>
