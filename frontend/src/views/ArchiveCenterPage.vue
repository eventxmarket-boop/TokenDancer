<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  listHowToDoHistoryRecords,
  loadHowToDoHistoryRecords,
  toggleFavoriteHowToDoHistoryRecord,
  type HowToDoHistoryRecord,
} from '@/services/howToDoHistoryService'
import {
  listReplyAssistantHistoryRecords,
  toggleReplyAssistantPinnedRecord,
  loadReplyAssistantHistoryRecords as loadReplyAssistantArchiveRecords,
  type ReplyAssistantHistoryRecord,
} from '@/services/replyAssistantArchiveService'

type ArchiveKind = 'reply' | 'how-to-do'
type ArchiveTab = 'history' | 'favorites'
type ReplyArchiveHistoryRecord = ReplyAssistantHistoryRecord

const route = useRoute()
const router = useRouter()

const replyTargetLabels: Record<string, string> = {
  crush: '暧昧对象',
  partner: '伴侣',
  ex: '前任',
  colleague: '同事',
  boss: '上司 / 领导',
  client: '客户 / 对接方',
  public_sector: '体制内 / 公务沟通',
  mentor: '导师 / 前辈',
  friend: '朋友',
  family: '家人',
}

const replySceneLabels: Record<string, string> = {
  daily: '日常聊天',
  conflict: '冷战 / 冲突',
  push_forward: '推进关系',
  work_report: '工作汇报',
  follow_up: '跟进未回复',
  formal_notice: '正式通知',
  rejection: '拒绝 / 婉拒',
  repair: '解释误会 / 修复',
}

const archiveKind = computed<ArchiveKind>(() =>
  route.params.kind === 'how-to-do' ? 'how-to-do' : 'reply',
)
const archiveTitle = computed(() => (archiveKind.value === 'reply' ? '我该怎么回' : '我该怎么做'))
const archiveSubtitle = computed(() =>
  archiveKind.value === 'reply' ? '查看历史对话和收藏对话。' : '查看历史卦象和收藏卦象。',
)
const backTarget = computed(() =>
  archiveKind.value === 'reply' ? '/reply-assistant/workbench' : '/how-to-do',
)
const activeTab = ref<ArchiveTab>('history')
const replyRecords = ref<ReplyArchiveHistoryRecord[]>([])
const howToDoRecords = ref<HowToDoHistoryRecord[]>([])

async function loadReplyArchiveRecords() {
  replyRecords.value = listReplyAssistantHistoryRecords()
  replyRecords.value = await loadReplyAssistantArchiveRecords()
}

async function loadHowToDoArchiveRecords() {
  howToDoRecords.value = listHowToDoHistoryRecords()
  howToDoRecords.value = await loadHowToDoHistoryRecords()
}

async function refreshRecords() {
  if (archiveKind.value === 'reply') {
    await loadReplyArchiveRecords()
  } else {
    await loadHowToDoArchiveRecords()
  }
}

const activeHistoryRecords = computed(() => {
  const source = archiveKind.value === 'reply' ? replyRecords.value : howToDoRecords.value
  if (activeTab.value === 'favorites') {
    return source.filter((item) => Boolean((item as ReplyAssistantHistoryRecord).pinned ?? (item as HowToDoHistoryRecord).favorite))
  }
  return source
})

const emptyCopy = computed(() => {
  if (archiveKind.value === 'reply') {
    return activeTab.value === 'favorites' ? '这里还没有收藏对话。' : '这里还没有历史对话。'
  }
  return activeTab.value === 'favorites' ? '这里还没有收藏卦象。' : '这里还没有历史卦象。'
})

const emptyHint = computed(() =>
  archiveKind.value === 'reply'
    ? '先回到“我该怎么回”生成几次回复，历史会在这里自动收进来。'
    : '先回到“我该怎么做”起一卦，历史和收藏都会在这里出现。',
)

function formatTime(value: string) {
  return value ? new Date(value).toLocaleString('zh-CN') : '—'
}

function getReplyPreview(record: ReplyArchiveHistoryRecord) {
  const assistantTurn = [...(record.turns || [])].reverse().find((turn) => turn.role === 'assistant')
  const userTurn = [...(record.turns || [])].reverse().find((turn) => turn.role === 'user')
  return (assistantTurn?.content || userTurn?.content || record.title || '未命名对话').trim()
}

function getHowToDoPreview(record: HowToDoHistoryRecord) {
  return (record.question || record.title || '未命名卦象').trim()
}

function openRecord(record: ReplyArchiveHistoryRecord | HowToDoHistoryRecord) {
  if (archiveKind.value === 'reply') {
    void router.push({
      path: '/reply-assistant/workbench',
      query: { history: record.id },
    })
    return
  }

  void router.push({
    path: '/how-to-do',
    query: { history: record.id },
  })
}

function toggleRecordFavorite(record: ReplyArchiveHistoryRecord | HowToDoHistoryRecord) {
  if (archiveKind.value === 'reply') {
    const toggled = toggleReplyAssistantPinnedRecord(record.id)
    if (toggled) {
      void loadReplyArchiveRecords()
    }
    return
  }

  toggleFavoriteHowToDoHistoryRecord(record.id)
  void loadHowToDoArchiveRecords()
}

function goBack() {
  void router.push(backTarget.value)
}

function setTab(tab: ArchiveTab) {
  activeTab.value = tab
  void router.replace({
    path: route.path,
    query: {
      ...route.query,
      tab,
    },
  })
}

onMounted(() => {
  const nextTab = route.query.tab === 'favorites' ? 'favorites' : 'history'
  activeTab.value = nextTab
  void refreshRecords()
})

watch(
  () => route.params.kind,
  () => {
    void refreshRecords()
  },
)

watch(
  () => route.query.tab,
  () => {
    activeTab.value = route.query.tab === 'favorites' ? 'favorites' : 'history'
  },
)
</script>

<template>
  <section class="archive-page">
    <div class="archive-page__inner">
      <div class="archive-window">
        <div class="archive-window__head">
          <div>
            <p class="eyebrow">{{ archiveTitle }}</p>
            <h1>{{ archiveKind === 'reply' ? '历史 / 收藏对话' : '历史 / 收藏卦象' }}</h1>
            <p class="hero-text">{{ archiveSubtitle }}</p>
          </div>

          <div class="archive-window__actions">
            <button class="secondary-btn" type="button" @click="goBack">返回</button>
          </div>
        </div>

        <div class="archive-tabs">
          <button
            type="button"
            class="chip-btn"
            :class="{ 'chip-btn--active': activeTab === 'history' }"
            @click="setTab('history')"
          >
            历史
          </button>
          <button
            type="button"
            class="chip-btn"
            :class="{ 'chip-btn--active': activeTab === 'favorites' }"
            @click="setTab('favorites')"
          >
            收藏
          </button>
        </div>

        <div v-if="!activeHistoryRecords.length" class="empty-panel empty-panel--compact archive-empty">
          <h3>{{ emptyCopy }}</h3>
          <p class="empty-panel__copy">{{ emptyHint }}</p>
          <RouterLink v-if="archiveKind === 'reply'" class="primary-btn" to="/reply-assistant/workbench">去继续回复</RouterLink>
          <RouterLink v-else class="primary-btn" to="/how-to-do">去继续起卦</RouterLink>
        </div>

        <div v-else class="archive-list">
          <article
            v-for="record in activeHistoryRecords"
            :key="record.id"
            class="archive-card"
          >
            <div class="archive-card__head">
              <div>
                <h3>{{ record.title || '未命名' }}</h3>
                <p class="archive-card__preview">
                  {{ archiveKind === 'reply' ? getReplyPreview(record as ReplyArchiveHistoryRecord) : getHowToDoPreview(record as HowToDoHistoryRecord) }}
                </p>
              </div>
              <span v-if="(record as ReplyArchiveHistoryRecord).pinned || (record as HowToDoHistoryRecord).favorite" class="status-pill">收藏</span>
            </div>

            <div class="archive-card__meta">
              <span class="tag-chip">
                {{
                  archiveKind === 'reply'
                    ? `${replyTargetLabels[(record as ReplyArchiveHistoryRecord).form?.target_person_type || ''] || '未分类'} · ${replySceneLabels[(record as ReplyArchiveHistoryRecord).form?.scene_type || ''] || '日常聊天'}`
                    : `${(record as HowToDoHistoryRecord).category || '未分类'} · ${(record as HowToDoHistoryRecord).castMode || '硬币起卦'}`
                }}
              </span>
              <span class="tag-chip">{{ formatTime(record.updatedAt) }}</span>
            </div>

            <div class="archive-card__actions">
              <button type="button" class="secondary-btn" @click="openRecord(record)">
                {{ archiveKind === 'reply' ? '打开对话' : '打开卦象' }}
              </button>
              <button type="button" class="ghost-btn" @click="toggleRecordFavorite(record)">
                {{
                  archiveKind === 'reply'
                    ? ((record as ReplyArchiveHistoryRecord).pinned ? '取消收藏' : '收藏对话')
                    : ((record as HowToDoHistoryRecord).favorite ? '取消收藏' : '收藏卦象')
                }}
              </button>
            </div>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.archive-page {
  display: flex;
  justify-content: center;
}

.archive-page__inner {
  width: min(760px, 100%);
}

.archive-window {
  display: grid;
  gap: 1rem;
  padding: 1.05rem;
  border: 1px solid var(--line);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow);
  backdrop-filter: blur(16px);
}

.archive-window__head {
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  align-items: flex-start;
}

.archive-window__head h1 {
  margin: 0;
  font-size: 1.5rem;
}

.archive-window__head .hero-text {
  margin-top: 0.35rem;
}

.archive-window__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.archive-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.archive-list {
  display: grid;
  gap: 0.8rem;
}

.archive-card {
  display: grid;
  gap: 0.8rem;
  padding: 0.95rem 1rem;
  border: 1px solid rgba(127, 140, 172, 0.16);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.8);
}

.archive-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.archive-card__head h3 {
  margin: 0;
  font-size: 1.1rem;
}

.archive-card__preview {
  margin: 0.35rem 0 0;
  color: var(--text);
  line-height: 1.6;
}

.archive-card__meta,
.archive-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.archive-card__actions {
  justify-content: flex-start;
}

.archive-empty {
  margin-top: 0.2rem;
}

@media (max-width: 700px) {
  .archive-window {
    padding: 0.9rem;
    border-radius: 24px;
  }

  .archive-window__head {
    flex-direction: column;
  }

  .archive-card__head {
    flex-direction: column;
  }
}
</style>
