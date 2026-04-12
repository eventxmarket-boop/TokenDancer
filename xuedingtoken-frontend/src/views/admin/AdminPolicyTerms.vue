<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">服务条款</h1>
      <button class="btn-outline-sm" @click="fetch">🔄 刷新</button>
    </div>
    <div class="page-hint">以下内容为前台 /terms 页面的生效版本</div>

    <div v-if="loading" class="state-msg">加载中…</div>
    <div v-else-if="error" class="state-msg error">{{ error }}</div>
    <div v-else>
      <div class="form-group"><label>标题</label><input class="form-input" v-model="form.title" placeholder="服务条款" /></div>
      <div class="form-group"><label>正文</label><textarea class="form-textarea" v-model="form.content" placeholder="请输入服务条款内容…" rows="20"></textarea></div>
      <div class="page-actions">
        <button class="btn-primary" @click="doSave" :disabled="saving">{{ saving ? '保存中…' : '保存' }}</button>
      </div>
      <div class="page-meta" v-if="page.updated_at">最近更新：{{ fmtDate(page.updated_at) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { adminContentApi } from '@/api/content'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()
const page = ref<any>({})
const loading = ref(false)
const error = ref('')
const saving = ref(false)
const form = reactive({ title: '', content: '' })

const fetch = async () => {
  loading.value = true; error.value = ''
  try {
    page.value = await adminContentApi.getTerms()
    form.title = page.value.title || ''
    form.content = page.value.content || ''
  } catch (e: any) { error.value = e.message }
  finally { loading.value = false }
}

const doSave = async () => {
  saving.value = true
  try {
    await adminContentApi.updateTerms(form)
    feedback.success('服务条款已保存')
    fetch()
  } catch (e: any) { feedback.error(e.message || '保存失败') }
  finally { saving.value = false }
}

const fmtDate = (d: string) => d ? new Date(d).toLocaleString('zh-CN') : '—'
onMounted(fetch)
</script>

<style scoped>
.page-container { padding: 24px; max-width: 900px; }
.page-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; }
.page-hint { font-size:12px; color:#999; margin-bottom:20px; }
.state-msg { text-align:center; padding:60px; color:#888; }
.state-msg.error { color:#ff4d4f; }
.form-group { margin-bottom:16px; }
.form-group label { display:block; font-size:13px; font-weight:600; color:#555; margin-bottom:6px; }
.form-input, .form-textarea { width:100%; padding:8px 12px; border:1px solid #e5e4e7; border-radius:8px; font-size:14px; box-sizing:border-box; }
.form-textarea { resize:vertical; font-family:inherit; }
.page-actions { margin-top:16px; }
.page-meta { font-size:12px; color:#999; margin-top:12px; }
.btn-primary { background:#aa3bff; color:#fff; border:none; padding:8px 20px; border-radius:8px; cursor:pointer; font-size:14px; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
</style>
