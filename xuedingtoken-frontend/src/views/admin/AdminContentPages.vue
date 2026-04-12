<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">页面内容管理</h1>
      <button class="btn-outline-sm" @click="fetch">🔄 刷新</button>
    </div>

    <!-- Page Selector -->
    <div class="page-tabs" v-if="!loading && !error">
      <button
        v-for="pg in pageList"
        :key="pg.slug"
        :class="['tab-btn', selectedSlug === pg.slug ? 'tab-active' : '']"
        @click="selectPage(pg.slug)"
      >{{ pg.title }}</button>
    </div>

    <!-- Loading / Error -->
    <div v-if="loading" class="state-msg">加载中…</div>
    <div v-else-if="error" class="state-msg error">{{ error }} <button class="btn-retry" @click="fetch">重试</button></div>

    <!-- Editor -->
    <div v-else class="editor-section">
      <div class="editor-hint">当前编辑：<strong>{{ currentTitle }}</strong>（对应前台 /{{ selectedSlug }} 页面）</div>
      <div class="form-group"><label>页面标题</label><input class="form-input" v-model="form.title" placeholder="页面标题" /></div>
      <div class="form-group"><label>正文内容</label><textarea class="form-textarea" v-model="form.content" placeholder="请输入页面内容…" rows="22"></textarea></div>
      <div class="page-actions">
        <button class="btn-primary" @click="doSave" :disabled="saving">{{ saving ? '保存中…' : '保存修改' }}</button>
      </div>
      <div class="page-meta" v-if="page.updated_at">最近更新：{{ fmtDate(page.updated_at) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { adminContentApi } from '@/api/content'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()

const pageList = [
  { slug: 'about', title: '关于我们' },
  { slug: 'docs_center', title: '文档中心' },
  { slug: 'faq', title: '常见问题' },
  { slug: 'help_center', title: '帮助中心' },
]

const selectedSlug = ref('about')
const page = ref<any>({})
const loading = ref(false)
const error = ref('')
const saving = ref(false)
const form = reactive({ title: '', content: '' })

const currentTitle = computed(() => pageList.find(p => p.slug === selectedSlug.value)?.title || selectedSlug.value)

const selectPage = async (slug: string) => {
  selectedSlug.value = slug
  await fetch()
}

const fetch = async () => {
  loading.value = true; error.value = ''
  try {
    page.value = await adminContentApi.getPage(selectedSlug.value)
    form.title = page.value.title || ''
    form.content = page.value.content || ''
  } catch (e: any) { error.value = e.message }
  finally { loading.value = false }
}

const doSave = async () => {
  if (!form.title.trim()) { feedback.warning('请填写标题'); return }
  saving.value = true
  try {
    await adminContentApi.updatePage(selectedSlug.value, form)
    feedback.success(`${currentTitle.value} 已保存`)
    fetch()
  } catch (e: any) { feedback.error(e.message || '保存失败') }
  finally { saving.value = false }
}

const fmtDate = (d: string) => d ? new Date(d).toLocaleString('zh-CN') : '—'
onMounted(fetch)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 900px; }
.page-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; }
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; }
.state-msg { text-align:center; padding:60px; color:#888; }
.state-msg.error { color:#ff4d4f; }
.btn-retry { margin-left:12px; text-decoration:underline; cursor:pointer; background:none; border:none; color:#1677ff; font-size:14px; }

.page-tabs { display:flex; gap:8px; margin-bottom:20px; flex-wrap:wrap; }
.tab-btn { padding:7px 16px; border:1px solid #e5e4e7; border-radius:8px; background:#fff; color:#555; font-size:13.5px; cursor:pointer; transition:all .15s; }
.tab-btn:hover { border-color:#aa3bff; color:#aa3bff; }
.tab-active { background:#aa3bff; color:#fff; border-color:#aa3bff; font-weight:600; }

.editor-hint { font-size:12px; color:#999; margin-bottom:16px; }

.form-group { margin-bottom:16px; }
.form-group label { display:block; font-size:13px; font-weight:600; color:#555; margin-bottom:6px; }
.form-input, .form-textarea { width:100%; padding:8px 12px; border:1px solid #e5e4e7; border-radius:8px; font-size:14px; box-sizing:border-box; }
.form-textarea { resize:vertical; font-family:inherit; }
.page-actions { margin-top:16px; }
.page-meta { font-size:12px; color:#999; margin-top:12px; }

.btn-primary { background:#aa3bff; color:#fff; border:none; padding:8px 20px; border-radius:8px; cursor:pointer; font-size:14px; }
.btn-primary:disabled { opacity:.6; cursor:not-allowed; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
</style>
