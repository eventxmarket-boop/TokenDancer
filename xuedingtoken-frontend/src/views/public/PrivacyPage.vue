<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">{{ page.title || '隐私政策' }}</h1>
    </div>
    <div class="content-body" v-if="!loading && !error">
      <div class="content-text" v-if="page.content" v-html="formatContent(page.content)"></div>
      <div v-else class="empty-state">暂无内容</div>
    </div>
    <div v-if="loading" class="loading-state">加载中…</div>
    <div v-if="error" class="error-state">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { contentApi } from '@/api/content'

const page = ref<any>({})
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    page.value = await contentApi.privacy()
  } catch (e: any) { error.value = e.message || '加载失败' }
  finally { loading.value = false }
})

const escapeHtml = (c: string) => c
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;')

const formatContent = (c: string) => escapeHtml(c).replace(/\n/g, '<br>')
</script>

<style scoped>
.page-container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
.page-title-row { margin-bottom: 32px; }
.page-title { font-size: 24px; font-weight: 700; color: #1a1a2e; }
.content-body { line-height: 1.8; color: #333; font-size: 15px; }
.content-text { white-space: pre-wrap; }
.empty-state, .loading-state, .error-state { text-align: center; padding: 60px; color: #888; }
.error-state { color: #ff4d4f; }
</style>
