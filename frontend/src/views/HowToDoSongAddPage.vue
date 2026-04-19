<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

type SongNote = {
  id: string
  title: string
  content: string
}

const router = useRouter()
const title = ref('')
const content = ref('')
const notes = ref<SongNote[]>([])

function loadNotes() {
  try {
    const raw = window.localStorage.getItem('liuyao-song-notes')
    notes.value = raw ? (JSON.parse(raw) as SongNote[]) : []
  } catch {
    notes.value = []
  }
}

function persist(next: SongNote[]) {
  notes.value = next
  window.localStorage.setItem('liuyao-song-notes', JSON.stringify(next))
}

function addNote() {
  const nextTitle = title.value.trim()
  const nextContent = content.value.trim()
  if (!nextTitle || !nextContent) return
  persist([
    { id: String(Date.now()), title: nextTitle, content: nextContent },
    ...notes.value,
  ].slice(0, 50))
  title.value = ''
  content.value = ''
}

function deleteNote(id: string) {
  const ok = window.confirm('删除后无法找回，确定要删除吗？')
  if (!ok) return
  persist(notes.value.filter((item) => item.id !== id))
}

onMounted(loadNotes)
</script>

<template>
  <section class="page-hero page-hero--single">
    <div class="hero-copy">
      <p class="eyebrow">心源六爻</p>
      <h1>添加歌诀</h1>
      <p class="hero-text">把你常用的速记、口诀和提醒加进来。</p>
    </div>
  </section>

  <section class="summary-panel summary-panel--featured">
    <label class="field-label">
      标题
      <input v-model="title" type="text" class="field-input" placeholder="例如：先看动爻" />
    </label>
    <label class="field-label">
      内容
      <textarea v-model="content" class="text-area" rows="5" placeholder="写一句速记或口诀。"></textarea>
    </label>
    <div class="how-to-do-actions">
      <button class="primary-btn" type="button" @click="addNote">保存</button>
      <button class="secondary-btn" type="button" @click="router.push('/how-to-do')">返回歌诀</button>
    </div>

    <div class="liuyao-record-list" style="margin-top: 1rem;">
      <article v-for="item in notes" :key="item.id" class="liuyao-record-item">
        <strong>{{ item.title }}</strong>
        <p style="margin: .4rem 0 0; color: var(--text-secondary);">{{ item.content }}</p>
        <div class="liuyao-record-actions">
          <button type="button" class="chip-btn" @click="deleteNote(item.id)">删除</button>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
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
  line-height: 1.5;
}

.how-to-do-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.65rem;
  margin-top: 0.9rem;
  flex-wrap: wrap;
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

.liuyao-record-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.7rem;
}
</style>
