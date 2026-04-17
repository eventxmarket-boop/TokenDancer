<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { requestHowToDo, type HowToDoCatalogCard, type HowToDoResponse } from '@/services/howToDoService'

type MainTab = 'cast' | 'sundial' | 'songs' | 'catalog'
type SongNote = { id: string; title: string; content: string }

type PalaceCatalogGroup = {
  palace: string
  cards: HowToDoCatalogCard[]
}

const mainTabs: Array<{ key: MainTab; label: string; hint: string }> = [
  { key: 'cast', label: '排盘', hint: '问念、分类、时间、起卦方式。' },
  { key: 'sundial', label: '日晷', hint: '当前时间、农历、节气。' },
  { key: 'songs', label: '歌诀', hint: '我添加的 / 内置。' },
  { key: 'catalog', label: '六十四卦', hint: '按宫查看卦象。' },
]

const castModes: Array<{ key: 'coin' | 'character' | 'number' | 'taiji'; label: string; hint: string }> = [
  { key: 'coin', label: '随机摇卦', hint: '平心静气后摇卦。' },
  { key: 'character', label: '手动输入', hint: '汉字、短句或文本。' },
  { key: 'number', label: '数字起卦', hint: '数字、编号或号码。' },
  { key: 'taiji', label: '太极丸起卦', hint: '按太极丸方式起局。' },
]

const questionCategories = [
  '出行平安',
  '能否出行',
  '何时出行',
  '工作推进',
  '感情回应',
  '求财求职',
  '健康平安',
  '其他',
]

const builtInSongTitles = ['浑天甲子歌', '天干与内脏关系对应', '天干与人体对应关系', '地支与内脏关系对应', '地支与人体关系对应', '八卦与人体对应关系', '八记忆卦口诀', '年上月初，五虎遁', '日起时，五鼠遁', '寻找世认宫歌']

const activeTab = ref<MainTab>('cast')
const activeCastMode = ref<'coin' | 'character' | 'number' | 'taiji'>('coin')
const question = ref('')
const category = ref('')
const castSeed = ref(String(Date.now()))
const castText = ref('')
const loading = ref(false)
const errorMessage = ref('')
const result = ref<HowToDoResponse | null>(null)
const songsResult = ref<HowToDoResponse | null>(null)
const selectedCatalog = ref<HowToDoCatalogCard | null>(null)
const catalogCards = ref<HowToDoCatalogCard[]>([])
const catalogQuery = ref('')
const songTab = ref<'mine' | 'builtin'>('mine')
const songNotes = ref<SongNote[]>([])
const songTitle = ref('')
const songContent = ref('')
const timeNow = ref(new Date())
const showProcess = ref(false)
const showResultBoard = ref(true)
const showHidden = ref(true)
const useSymbols = ref(false)
const showNaYin = ref(false)
const weakenRelated = ref(false)
let timer: number | undefined

const currentTimeText = computed(() => timeNow.value.toLocaleString('zh-CN'))
const chineseCalendarText = computed(() => {
  try {
    return new Intl.DateTimeFormat('zh-Hans-CN-u-ca-chinese', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long',
      hour: 'numeric',
      minute: 'numeric',
    }).format(timeNow.value)
  } catch {
    return timeNow.value.toLocaleString('zh-CN')
  }
})

function solarTermInfo(date: Date) {
  const terms = [
    ['小寒', 1, 5], ['大寒', 1, 20],
    ['立春', 2, 4], ['雨水', 2, 19],
    ['惊蛰', 3, 6], ['春分', 3, 21],
    ['清明', 4, 5], ['谷雨', 4, 20],
    ['立夏', 5, 6], ['小满', 5, 21],
    ['芒种', 6, 6], ['夏至', 6, 21],
    ['小暑', 7, 7], ['大暑', 7, 23],
    ['立秋', 8, 8], ['处暑', 8, 23],
    ['白露', 9, 8], ['秋分', 9, 23],
    ['寒露', 10, 8], ['霜降', 10, 23],
    ['立冬', 11, 7], ['小雪', 11, 22],
    ['大雪', 12, 7], ['冬至', 12, 22],
  ] as const
  const nowMonth = date.getMonth() + 1
  const nowDay = date.getDate()
  let currentIndex = 0
  for (let index = 0; index < terms.length; index += 1) {
    const [, month, day] = terms[index]
    const next = terms[index + 1]
    if (nowMonth > month || (nowMonth === month && nowDay >= day)) {
      currentIndex = index
    }
    if (next && nowMonth < next[1] && nowMonth >= month) break
  }
  const current = terms[currentIndex]
  const next = terms[(currentIndex + 1) % terms.length]
  return {
    current: current[0],
    next: next[0],
  }
}

const solarTerms = computed(() => solarTermInfo(timeNow.value))

const castResult = computed(() => result.value?.raw_result as Record<string, any> | undefined)
const castCards = computed(() => result.value?.cards || [])
const castLineDetails = computed(() => {
  const list = castResult.value?.line_details
  if (!Array.isArray(list)) return []
  return [...list].reverse()
})
const castQuestionText = computed(() => {
  const text = result.value?.question?.trim() || question.value.trim() || ''
  return text || '搜索'
})
const castModeText = computed(() => {
  const mode = castResult.value?.cast_mode || activeCastMode.value
  if (mode === 'character') return '汉字 / 文本起卦'
  if (mode === 'number') return '数字起卦'
  return '硬币 / 太极丸起卦'
})
const castCategoryText = computed(() => castCards.value.find((item) => item.label === '分类')?.value || category.value.trim() || '—')
const castTimeText = computed(() => castResult.value?.day_label || currentTimeText.value)
const castShenshaText = computed(() => {
  const shensha = (castResult.value?.shensha || {}) as Record<string, string>
  return [
    `卦身--${shensha.卦身 || '—'}`,
    `贵人--${shensha.贵人 || '—'}`,
    `驿马--${shensha.驿马 || '—'}`,
    `羊刃--${shensha.羊刃 || '—'}`,
  ]
})
const castPanelTitle = computed(() => castResult.value?.panel_title || result.value?.summary || '卦象详情')
const castPanelSubtitle = computed(() => castResult.value?.panel_subtitle || '')

const catalogGroups = computed<PalaceCatalogGroup[]>(() => {
  const groups = new Map<string, HowToDoCatalogCard[]>()
  for (const card of catalogCards.value) {
    const current = groups.get(card.palace) || []
    current.push(card)
    groups.set(card.palace, current)
  }
  return Array.from(groups.entries()).map(([palace, cards]) => ({ palace, cards }))
})

const filteredCatalogGroups = computed(() => {
  const query = catalogQuery.value.trim()
  if (!query) return catalogGroups.value
  return catalogGroups.value
    .map((group) => ({
      palace: group.palace,
      cards: group.cards.filter((card) => `${card.number}${card.name}${card.tag}${card.meaning}`.includes(query)),
    }))
    .filter((group) => group.cards.length > 0)
})

const builtInSongs = computed(() => {
  if (songsResult.value?.cards?.length) {
    return songsResult.value.cards.map((item) => ({
      title: item.label,
      content: item.value,
    }))
  }
  if (songsResult.value?.raw_result?.snippets && Array.isArray(songsResult.value.raw_result.snippets)) {
    return songsResult.value.raw_result.snippets as Array<{ title: string; content: string }>
  }
  return builtInSongTitles.map((title) => ({ title, content: '' }))
})

function setActiveTab(tab: MainTab) {
  activeTab.value = tab
  errorMessage.value = ''
  if (tab === 'catalog' && !catalogCards.value.length) {
    void loadCatalog()
  }
  if (tab === 'songs' && !result.value) {
    void loadSongs()
  }
}

function loadNotes() {
  try {
    const raw = window.localStorage.getItem('liuyao-song-notes')
    songNotes.value = raw ? (JSON.parse(raw) as SongNote[]) : []
  } catch {
    songNotes.value = []
  }
}

function persistNotes(next: SongNote[]) {
  songNotes.value = next
  window.localStorage.setItem('liuyao-song-notes', JSON.stringify(next))
}

function addSongNote() {
  const title = songTitle.value.trim()
  const content = songContent.value.trim()
  if (!title || !content) return
  persistNotes([{ id: String(Date.now()), title, content }, ...songNotes.value].slice(0, 50))
  songTitle.value = ''
  songContent.value = ''
}

function deleteSongNote(id: string) {
  const ok = window.confirm('删除后无法找回，确定要删除吗？')
  if (!ok) return
  persistNotes(songNotes.value.filter((item) => item.id !== id))
}

async function loadCatalog() {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await requestHowToDo({ section: 'catalog', use_ai: false })
    catalogCards.value = response.catalog
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '卦库加载失败'
  } finally {
    loading.value = false
  }
}

async function loadSongs() {
  try {
    const response = await requestHowToDo({ section: 'songs', use_ai: false })
    songsResult.value = response
  } catch {
    // ignore, local built-in content still works
  }
}

function resetCast() {
  question.value = ''
  category.value = ''
  castSeed.value = String(Date.now())
  castText.value = ''
  result.value = null
  selectedCatalog.value = null
  showProcess.value = false
  showResultBoard.value = true
  showHidden.value = true
  useSymbols.value = false
  showNaYin.value = false
  weakenRelated.value = false
}

function useCurrentTime() {
  timeNow.value = new Date()
  castSeed.value = String(Date.now())
  category.value = category.value || questionCategories[0]
}

function getCurrentCastPrompt() {
  return castText.value.trim() || question.value.trim() || category.value.trim()
}

async function cast() {
  if (!getCurrentCastPrompt()) {
    errorMessage.value = '请先输入问念或分类。'
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
      character_text: activeCastMode.value === 'character' ? castText.value.trim() : '',
      number_text: activeCastMode.value === 'number' ? castText.value.trim() : '',
      use_ai: true,
    })
    result.value = response
    window.localStorage.setItem('liuyao-last-result', JSON.stringify(response))
    castSeed.value = String(Date.now())
    showResultBoard.value = true
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '排盘失败'
  } finally {
    loading.value = false
  }
}

function sharePage() {
  const url = window.location.href
  if (navigator.share) {
    void navigator.share({ title: document.title, url })
    return
  }
  void navigator.clipboard.writeText(url)
}

function copyHexagram() {
  const text = [result.value?.summary, result.value?.ai_interpretation].filter(Boolean).join('\n')
  void navigator.clipboard.writeText(text || '暂无可复制内容')
}

function shareScreenshot() {
  const text = result.value?.summary || '当前卦象'
  void navigator.clipboard.writeText(text)
}

onMounted(() => {
  loadNotes()
  void loadCatalog()
  void loadSongs()
  timer = window.setInterval(() => {
    timeNow.value = new Date()
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
      <h1>排盘</h1>
      <p class="hero-text">问念或者分类，请至少输入一个。一卦一问，问念是一个卦象的重要组成部分！</p>
    </div>
  </section>

  <section class="how-to-do-page">
    <div class="how-to-do-mode-row" role="tablist" aria-label="六爻页面">
      <button
        v-for="tab in mainTabs"
        :key="tab.key"
        type="button"
        class="chip-btn"
        :class="{ 'chip-btn--active': activeTab === tab.key }"
        @click="setActiveTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="how-to-do-layout">
      <article class="summary-panel how-to-do-panel">
        <div class="how-to-do-panel__head">
          <div>
            <p class="eyebrow">当前页</p>
            <h3>{{ mainTabs.find((item) => item.key === activeTab)?.label }}</h3>
            <p class="hero-text">{{ mainTabs.find((item) => item.key === activeTab)?.hint }}</p>
          </div>
        </div>

        <template v-if="activeTab === 'cast'">
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
          <p class="how-to-do-note">
            {{ castModes.find((item) => item.key === activeCastMode)?.hint }}
          </p>

          <label class="field-label">
            问念
            <textarea v-model="question" class="text-area" rows="4" placeholder="请输入您的问题"></textarea>
          </label>

          <label class="field-label">
            分类
            <input v-model="category" class="field-input" list="how-to-do-categories" placeholder="出行平安、能否出行、何时出行" />
            <datalist id="how-to-do-categories">
              <option v-for="item in questionCategories" :key="item" :value="item" />
            </datalist>
          </label>

          <div class="how-to-do-field-grid">
            <label class="field-label">
              起卦时间
              <input v-model="castSeed" type="text" class="field-input" />
            </label>
            <label class="field-label">
              当前时间
              <input :value="currentTimeText" type="text" class="field-input" disabled />
            </label>
          </div>

          <label v-if="activeCastMode === 'character' || activeCastMode === 'number'" class="field-label">
            {{ activeCastMode === 'character' ? '汉字 / 文本' : '数字' }}
            <textarea
              v-model="castText"
              class="text-area"
              rows="3"
              :placeholder="activeCastMode === 'character' ? '输入汉字、短句或一段话。' : '输入数字、编号或数字串。'"
            ></textarea>
          </label>

          <div class="how-to-do-actions how-to-do-actions--left">
            <button class="secondary-btn" type="button" @click="showProcess = !showProcess">起图流程？</button>
            <button class="secondary-btn" type="button" @click="resetCast">重置排盘信息</button>
            <button class="primary-btn" type="button" :disabled="loading" @click="cast">
              {{ loading ? '排盘中...' : '开始占卜' }}
            </button>
          </div>

          <p v-if="showProcess" class="how-to-do-note">
            使用三枚同面值的硬币，平心静气，集中注意想自己要问的事情，手摇后扔在桌面上，记录每次几个花，几个字，从下往上依次录入。硬币起卦即金钱卦，是传统也是最靠谱的六爻卦。太极丸与硬币卦同理。
          </p>
        </template>

        <template v-else-if="activeTab === 'sundial'">
          <div class="how-to-do-time-card how-to-do-time-card--accent">
            <strong>{{ currentTimeText }}</strong>
            <p>{{ chineseCalendarText }}</p>
          </div>

          <div class="how-to-do-card-grid">
            <div class="how-to-do-result-card">
              <span>当前节气</span>
              <strong>{{ solarTerms.current }}</strong>
            </div>
            <div class="how-to-do-result-card">
              <span>下一节气</span>
              <strong>{{ solarTerms.next }}</strong>
            </div>
          </div>

          <div class="how-to-do-actions how-to-do-actions--left">
            <button class="primary-btn" type="button" @click="useCurrentTime">更新为当前时间</button>
          </div>
        </template>

        <template v-else-if="activeTab === 'songs'">
          <div class="how-to-do-note">歌诀分为我添加的和内置内容。</div>
          <div class="how-to-do-mode-row">
            <button
              type="button"
              class="chip-btn"
              :class="{ 'chip-btn--active': songTab === 'mine' }"
              @click="songTab = 'mine'"
            >
              我添加的
            </button>
            <button
              type="button"
              class="chip-btn"
              :class="{ 'chip-btn--active': songTab === 'builtin' }"
              @click="songTab = 'builtin'"
            >
              内置
            </button>
          </div>

          <div v-if="songTab === 'mine'">
            <p class="how-to-do-note">
              暂无手动添加的歌诀，可点击右下角加号手动添加歌诀。
            </p>
            <label class="field-label">
              标题
              <input v-model="songTitle" type="text" class="field-input" placeholder="例如：先看动爻" />
            </label>
            <label class="field-label">
              内容
              <textarea v-model="songContent" class="text-area" rows="4" placeholder="写一句速记或口诀。"></textarea>
            </label>
            <div class="how-to-do-actions how-to-do-actions--left">
              <button class="primary-btn" type="button" @click="addSongNote">保存</button>
            </div>
            <div class="liuyao-record-list">
              <article v-for="item in songNotes" :key="item.id" class="liuyao-record-item">
                <strong>{{ item.title }}</strong>
                <p style="margin: .4rem 0 0; color: var(--text-secondary);">{{ item.content }}</p>
                <div class="liuyao-record-actions">
                  <button type="button" class="chip-btn" @click="deleteSongNote(item.id)">删除</button>
                </div>
              </article>
              <div v-if="!songNotes.length" class="empty-panel empty-panel--compact">
                <div class="empty-panel__icon">＋</div>
                <div class="empty-panel__copy">
                  <strong>暂无手动添加的歌诀。</strong>
                  <p>你可以打开右下角加号，先加一条自己的口诀。</p>
                </div>
              </div>
            </div>
            <div class="how-to-do-actions how-to-do-actions--left">
              <RouterLink class="secondary-btn" to="/how-to-do/songs/add">添加歌诀</RouterLink>
            </div>
          </div>

          <div v-else class="how-to-do-songs-grid">
            <div v-for="item in builtInSongs" :key="item.title" class="how-to-do-song-card">
              <strong>{{ item.title }}</strong>
              <p>{{ item.content }}</p>
            </div>
          </div>
        </template>

        <template v-else-if="activeTab === 'catalog'">
          <div class="how-to-do-note">六十四卦按宫分组，方便直接查找。</div>
          <label class="field-label">
            搜索
            <input v-model="catalogQuery" class="field-input" placeholder="输入卦名、宫名或标签" />
          </label>
          <div class="liuyao-catalog-groups">
            <section v-for="group in filteredCatalogGroups" :key="group.palace" class="liuyao-catalog-group">
              <div class="liuyao-catalog-group__head">
                <h4>{{ group.palace }}</h4>
              </div>
              <div class="liuyao-catalog-grid">
                <button
                  v-for="card in group.cards"
                  :key="`${card.number}-${card.name}`"
                  type="button"
                  class="liuyao-catalog-card"
                  :class="{ 'is-selected': selectedCatalog?.number === card.number }"
                  @click="selectedCatalog = card"
                >
                  <strong>{{ card.name }}</strong>
                  <span>{{ card.tag }}</span>
                  <p>{{ card.meaning }}</p>
                </button>
              </div>
            </section>
          </div>
        </template>

        <p v-if="errorMessage" class="how-to-do-error">{{ errorMessage }}</p>
      </article>

      <article class="summary-panel summary-panel--featured how-to-do-result">
        <template v-if="activeTab === 'cast' && result">
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
              <p class="liuyao-result-board__time">{{ castResult?.day_label || castTimeText }}</p>
              <p class="liuyao-result-board__title">{{ castPanelTitle }}<span v-if="castPanelSubtitle">（{{ castPanelSubtitle }}）</span></p>

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
                    <div v-if="line.hidden_spirit && showHidden" class="liuyao-line-board__hidden">↑伏：{{ line.hidden_spirit }}</div>
                    <div class="liuyao-line-board__bars">{{ useSymbols ? (line.is_changing ? '▅ ▅' : '▅▅▅') : line.text }}</div>
                    <div class="liuyao-line-board__tags">
                      <span v-if="line.shi_ying">{{ line.shi_ying }}</span>
                      <span v-if="showNaYin">{{ line.nayin }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="how-to-do-toggle-row" style="margin-top: 1rem;">
                <button class="chip-btn" :class="{ 'chip-btn--active': showHidden }" type="button" @click="showHidden = !showHidden">显示全部伏神</button>
                <button class="chip-btn" :class="{ 'chip-btn--active': useSymbols }" type="button" @click="useSymbols = !useSymbols">使用符号代替阴阳爻符号</button>
                <button class="chip-btn" :class="{ 'chip-btn--active': showNaYin }" type="button" @click="showNaYin = !showNaYin">显示纳音</button>
                <button class="chip-btn" :class="{ 'chip-btn--active': weakenRelated }" type="button" @click="weakenRelated = !weakenRelated">弱化关联变爻</button>
              </div>
            </div>

            <div class="how-to-do-detail-box">
              <p class="eyebrow">卦辞爻辞</p>
              <p>{{ result.ai_interpretation }}</p>
            </div>

            <div class="how-to-do-detail-box">
              <p class="eyebrow">结果反馈</p>
              <div class="how-to-do-suggestions">
                <span v-for="item in result.suggestions" :key="item" class="tag-chip">{{ item }}</span>
              </div>
            </div>

            <div class="how-to-do-detail-box">
              <p class="eyebrow">卦象数据创建时间</p>
              <p>{{ castResult?.timestamp || '—' }}</p>
            </div>

            <div v-if="castResult?.mutual_hexagram" class="how-to-do-detail-box">
              <p class="eyebrow">互卦</p>
              <strong>{{ castResult.mutual_hexagram.name }}卦</strong>
              <p>{{ castResult.mutual_hexagram.meaning }}</p>
            </div>

            <div v-if="selectedCatalog" class="how-to-do-detail-box">
              <p class="eyebrow">六十四卦</p>
              <strong>{{ selectedCatalog.name }}</strong>
              <p>{{ selectedCatalog.tag }} · {{ selectedCatalog.meaning }}</p>
            </div>

            <div class="how-to-do-actions how-to-do-actions--left">
              <button class="secondary-btn" type="button" @click="sharePage">分享当页URL</button>
              <button class="secondary-btn" type="button" @click="shareScreenshot">分享当页截图</button>
              <button class="secondary-btn" type="button" @click="copyHexagram">复制卦象</button>
            </div>
          </div>
        </template>

        <template v-else-if="activeTab === 'sundial'">
          <p class="eyebrow">日晷</p>
          <h3>{{ currentTimeText }}</h3>
          <div class="how-to-do-card-grid">
            <div class="how-to-do-result-card">
              <span>农历参考</span>
              <strong>{{ chineseCalendarText }}</strong>
            </div>
            <div class="how-to-do-result-card">
              <span>当前节气</span>
              <strong>{{ solarTerms.current }}</strong>
            </div>
            <div class="how-to-do-result-card">
              <span>下一节气</span>
              <strong>{{ solarTerms.next }}</strong>
            </div>
            <div class="how-to-do-result-card">
              <span>更新时间</span>
              <strong>{{ currentTimeText }}</strong>
            </div>
          </div>
          <div class="how-to-do-detail-box">
            <p>当前是 {{ solarTerms.current }} 节气，下一节气是 {{ solarTerms.next }}。</p>
          </div>
          <div class="how-to-do-actions how-to-do-actions--left">
            <button class="primary-btn" type="button" @click="useCurrentTime">更新为当前时间</button>
          </div>
        </template>

        <template v-else-if="activeTab === 'songs'">
          <p class="eyebrow">歌诀</p>
          <h3>共 {{ songNotes.length + builtInSongs.length }} 条歌诀</h3>
          <div class="how-to-do-mode-row">
            <button
              type="button"
              class="chip-btn"
              :class="{ 'chip-btn--active': songTab === 'mine' }"
              @click="songTab = 'mine'"
            >
              我添加的
            </button>
            <button
              type="button"
              class="chip-btn"
              :class="{ 'chip-btn--active': songTab === 'builtin' }"
              @click="songTab = 'builtin'"
            >
              内置
            </button>
          </div>

          <div v-if="songTab === 'mine'" class="liuyao-record-list" style="margin-top: 1rem;">
            <article v-for="item in songNotes" :key="item.id" class="liuyao-record-item">
              <strong>{{ item.title }}</strong>
              <p style="margin: .4rem 0 0; color: var(--text-secondary);">{{ item.content }}</p>
              <div class="liuyao-record-actions">
                <button type="button" class="chip-btn" @click="deleteSongNote(item.id)">删除</button>
              </div>
            </article>
            <div v-if="!songNotes.length" class="empty-panel empty-panel--compact">
              <div class="empty-panel__icon">◎</div>
              <div class="empty-panel__copy">
                <strong>暂无手动添加的歌诀。</strong>
                <p>可点击右下角加号手动添加歌诀。</p>
              </div>
            </div>
          </div>

          <div v-else class="how-to-do-songs-grid">
            <div v-for="item in builtInSongs" :key="item.title" class="how-to-do-song-card">
              <strong>{{ item.title }}</strong>
              <p>{{ item.content }}</p>
            </div>
          </div>

          <div class="how-to-do-actions how-to-do-actions--left">
            <RouterLink class="secondary-btn" to="/how-to-do/songs/add">＋</RouterLink>
          </div>
        </template>

        <template v-else-if="activeTab === 'catalog'">
          <p class="eyebrow">六十四卦</p>
          <h3>卦库</h3>
          <div class="how-to-do-card-grid">
            <div class="how-to-do-result-card">
              <span>卦库数量</span>
              <strong>{{ catalogCards.length }} 卦</strong>
            </div>
            <div class="how-to-do-result-card">
              <span>当前选中</span>
              <strong>{{ selectedCatalog?.name || '未选择' }}</strong>
            </div>
          </div>

          <div v-if="selectedCatalog" class="how-to-do-detail-box">
            <p class="eyebrow">卦象详情</p>
            <strong>{{ selectedCatalog.name }}</strong>
            <p>{{ selectedCatalog.palace }} · {{ selectedCatalog.tag }}</p>
            <p>{{ selectedCatalog.meaning }}</p>
          </div>

          <div class="how-to-do-actions how-to-do-actions--left">
            <button class="primary-btn" type="button" :disabled="loading" @click="loadCatalog">
              {{ loading ? '加载中...' : '刷新卦库' }}
            </button>
          </div>
        </template>
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
  gap: 0.65rem;
}

.how-to-do-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 1rem;
}

.how-to-do-panel,
.how-to-do-result {
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

.how-to-do-card-grid,
.how-to-do-songs-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.how-to-do-result-card,
.how-to-do-song-card,
.liuyao-catalog-card,
.liuyao-catalog-group,
.how-to-do-time-card,
.liuyao-record-item {
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

.how-to-do-time-card {
  border-color: rgba(148, 163, 184, 0.24);
}

.how-to-do-time-card--accent {
  border-color: rgba(59, 130, 246, 0.25);
}

.how-to-do-time-card strong {
  display: block;
  font-size: 1rem;
}

.how-to-do-time-card p,
.how-to-do-song-card p,
.liuyao-catalog-card p,
.how-to-do-detail-box p {
  margin: 0.35rem 0 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.liuyao-catalog-groups {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.liuyao-catalog-group__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.65rem;
}

.liuyao-catalog-group__head h4 {
  margin: 0;
}

.liuyao-catalog-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.liuyao-catalog-card {
  text-align: left;
  color: var(--text-primary);
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

.liuyao-catalog-card p {
  font-size: 0.84rem;
}

.liuyao-record-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
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

.how-to-do-detail-box,
.how-to-do-interpretation {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.how-to-do-detail-box strong {
  display: block;
  margin-top: 0.35rem;
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

.liuyao-result-board__time {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.liuyao-result-board__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
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

.liuyao-line-board__tags span {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.how-to-do-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
}

.liuyao-catalog-group {
  padding-bottom: 0.95rem;
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

@media (max-width: 1024px) {
  .how-to-do-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .how-to-do-field-grid,
  .how-to-do-card-grid,
  .how-to-do-songs-grid,
  .liuyao-catalog-grid,
  .liuyao-line-summary-list {
    grid-template-columns: 1fr;
  }
}
</style>
