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
      <button class="secondary-btn" type="button" @click="router.push('/how-to-do/songs')">返回歌诀</button>
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
