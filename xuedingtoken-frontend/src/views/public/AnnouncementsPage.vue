<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">公告中心</h1>
      <button class="btn-outline-sm" @click="fetch">🔄 刷新</button>
    </div>
    <div v-if="loading" class="state-msg">加载中…</div>
    <div v-else-if="error" class="state-msg error">{{ error }}</div>
    <div v-else-if="list.length === 0" class="state-msg">暂无公告</div>
    <div v-else class="announcement-list">
      <div v-for="a in list" :key="a.id" class="ann-card">
        <div class="ann-header">
          <h3 class="ann-title">{{ a.title }}</h3>
          <span class="ann-date">{{ fmtDate(a.published_at || a.created_at) }}</span>
        </div>
        <div class="ann-content">{{ a.content }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { contentApi } from '@/api/content'

const list = ref<any[]>([])
const loading = ref(true)
const error = ref('')

const fetch = async () => {
  loading.value = true; error.value = ''
  try { list.value = await contentApi.announcements() }
  catch (e: any) { error.value = e.message }
  finally { loading.value = false }
}

onMounted(fetch)

const fmtDate = (d: string) => d ? new Date(d).toLocaleString('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) : '—'
</script>

<style scoped>
.page-container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
.page-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:32px; }
.page-title { font-size:24px; font-weight:700; color:#1a1a2e; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.state-msg { text-align:center; padding:60px; color:#888; }
.state-msg.error { color:#ff4d4f; }
.announcement-list { display:flex; flex-direction:column; gap:20px; }
.ann-card { background:#fff; border:1px solid #f0f0f0; border-radius:12px; padding:24px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
.ann-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
.ann-title { font-size:16px; font-weight:700; color:#1a1a2e; }
.ann-date { font-size:12px; color:#999; }
.ann-content { font-size:14px; color:#555; line-height:1.7; white-space:pre-wrap; }
</style>
