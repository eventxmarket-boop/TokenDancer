<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">公告管理</h1>
      <button class="btn-outline-sm" @click="fetch">🔄 刷新</button>
    </div>
    <div class="page-toolbar">
      <button class="btn-primary" @click="openCreate">+ 创建公告</button>
    </div>

    <div class="ann-list">
      <div v-if="loading" class="state-msg">加载中…</div>
      <div v-else-if="error" class="state-msg error">{{ error }}</div>
      <div v-else-if="list.length === 0" class="state-msg">暂无公告</div>
      <div v-else v-for="a in list" :key="a.id" class="ann-row">
        <div class="ann-info">
          <div class="ann-title-row">
            <span class="ann-title">{{ a.title }}</span>
            <span :class="['badge', a.is_active ? 'badge-success' : 'badge-default']">{{ a.is_active ? '启用' : '停用' }}</span>
          </div>
          <div class="ann-meta">发布于：{{ fmtDate(a.published_at || a.created_at) }} · {{ a.content?.slice(0, 60) }}…</div>
        </div>
        <div class="ann-actions">
          <button class="btn-action-sm" @click="openEdit(a)">编辑</button>
          <button class="btn-warning-sm" @click="toggleActive(a)">{{ a.is_active ? '停用' : '启用' }}</button>
          <button class="btn-danger-sm" @click="confirmDelete(a)">删除</button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="modal-mask">
      <div class="modal-box">
        <h3 class="modal-title">{{ editingId ? '编辑公告' : '创建公告' }}</h3>
        <div class="form-group"><label>标题</label><input class="form-input" v-model="form.title" placeholder="公告标题" /></div>
        <div class="form-group"><label>内容</label><textarea class="form-textarea" v-model="form.content" placeholder="公告内容" rows="5"></textarea></div>
        <div class="form-group"><label>发布时间</label><input type="datetime-local" class="form-input" v-model="form.published_at" /></div>
        <div class="form-group"><label><input type="checkbox" v-model="form.is_active" /> 立即发布</label></div>
        <div class="modal-actions">
          <button class="btn-outline" @click="closeModal">取消</button>
          <button class="btn-primary" @click="doSave" :disabled="saving">{{ saving ? '保存中…' : '保存' }}</button>
        </div>
      </div>
    </div>

    <!-- Delete Confirm -->
    <div v-if="deleteTarget" class="modal-mask">
      <div class="modal-box">
        <h3 class="modal-title">确认删除</h3>
        <p class="modal-msg">确定删除公告「{{ deleteTarget.title }}」？此操作不可恢复。</p>
        <div class="modal-actions">
          <button class="btn-outline" @click="deleteTarget = null">取消</button>
          <button class="btn-danger" @click="doDelete" :disabled="deleting">{{ deleting ? '删除中…' : '确认删除' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { adminContentApi } from '@/api/content'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()
const list = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const showModal = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const deleteTarget = ref<any | null>(null)
const deleting = ref(false)

const form = reactive({ title: '', content: '', is_active: true, published_at: '' })

const fetch = async () => {
  loading.value = true; error.value = ''
  try { list.value = await adminContentApi.listAnnouncements() }
  catch (e: any) { error.value = e.message }
  finally { loading.value = false }
}

const openCreate = () => { editingId.value = null; Object.assign(form, { title: '', content: '', is_active: true, published_at: '' }); showModal.value = true }
const openEdit = (a: any) => {
  editingId.value = a.id
  form.title = a.title; form.content = a.content; form.is_active = a.is_active
  form.published_at = a.published_at ? new Date(a.published_at).toISOString().slice(0, 16) : ''
  showModal.value = true
}
const closeModal = () => { showModal.value = false; editingId.value = null }

const doSave = async () => {
  if (!form.title.trim()) { feedback.warning('请输入标题'); return }
  saving.value = true
  try {
    const payload: any = { title: form.title, content: form.content, is_active: form.is_active }
    if (form.published_at) payload.published_at = new Date(form.published_at).toISOString()
    if (editingId.value) await adminContentApi.updateAnnouncement(editingId.value, payload)
    else await adminContentApi.createAnnouncement(payload)
    feedback.success(editingId.value ? '公告已更新' : '公告已创建')
    closeModal(); fetch()
  } catch (e: any) { feedback.error(e.message || '保存失败') }
  finally { saving.value = false }
}

const toggleActive = async (a: any) => {
  try { await adminContentApi.updateAnnouncement(a.id, { is_active: !a.is_active }); feedback.success(a.is_active ? '已停用' : '已启用'); fetch() }
  catch (e: any) { feedback.error(e.message) }
}

const confirmDelete = (a: any) => { deleteTarget.value = a }
const doDelete = async () => {
  if (!deleteTarget.value) return
  deleting.value = true
  try { await adminContentApi.deleteAnnouncement(deleteTarget.value.id); feedback.success('已删除'); deleteTarget.value = null; fetch() }
  catch (e: any) { feedback.error(e.message || '删除失败') }
  finally { deleting.value = false }
}

const fmtDate = (d: string) => d ? new Date(d).toLocaleString('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) : '—'

onMounted(fetch)
</script>

<style scoped>
.page-container { padding: 24px; }
.page-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; }
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; }
.page-toolbar { margin-bottom:20px; }
.btn-primary { background:#aa3bff; color:#fff; border:none; padding:8px 18px; border-radius:8px; cursor:pointer; font-size:14px; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.state-msg { text-align:center; padding:60px; color:#888; }
.state-msg.error { color:#ff4d4f; }
.ann-list { display:flex; flex-direction:column; gap:12px; }
.ann-row { background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:16px 20px; display:flex; justify-content:space-between; align-items:center; }
.ann-info { flex:1; min-width:0; }
.ann-title-row { display:flex; align-items:center; gap:10px; margin-bottom:6px; }
.ann-title { font-size:14px; font-weight:600; color:#1a1a2e; }
.ann-meta { font-size:12px; color:#999; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.ann-actions { display:flex; gap:8px; flex-shrink:0; }
.btn-action-sm { font-size:11px; padding:3px 10px; background:none; color:#aa3bff; border:1px solid #aa3bff; border-radius:4px; cursor:pointer; }
.btn-warning-sm { font-size:11px; padding:3px 8px; color:#faad14; background:none; border:1px solid #faad14; border-radius:4px; cursor:pointer; }
.btn-danger-sm { font-size:11px; padding:3px 8px; color:#ff4d4f; background:none; border:1px solid #ff4d4f; border-radius:4px; cursor:pointer; }
.badge { font-size:11px; padding:2px 8px; border-radius:10px; font-weight:600; }
.badge-success { background:#f6ffed; color:#52c41a; }
.badge-default { background:#f5f5f5; color:#888; }
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:1000; }
.modal-box { background:#fff; border-radius:12px; padding:28px; width:520px; max-width:90vw; max-height:90vh; overflow-y:auto; }
.modal-title { font-size:18px; font-weight:700; color:#1a1a2e; margin-bottom:20px; }
.modal-msg { color:#555; margin-bottom:20px; line-height:1.6; }
.form-group { margin-bottom:16px; }
.form-group label { display:block; font-size:13px; font-weight:600; color:#555; margin-bottom:6px; }
.form-input, .form-textarea { width:100%; padding:8px 12px; border:1px solid #e5e4e7; border-radius:8px; font-size:14px; box-sizing:border-box; }
.form-textarea { resize:vertical; }
.modal-actions { display:flex; justify-content:flex-end; gap:10px; margin-top:20px; }
.btn-outline { padding:8px 18px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:8px; cursor:pointer; }
.btn-danger { padding:8px 18px; background:#ff4d4f; color:#fff; border:none; border-radius:8px; cursor:pointer; }
</style>
