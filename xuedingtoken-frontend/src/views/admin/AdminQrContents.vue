<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">二维码内容管理</h1>
      <button class="btn-outline-sm" @click="fetch">🔄 刷新</button>
    </div>
    <div class="page-toolbar">
      <button class="btn-primary" @click="openCreate">+ 添加二维码内容</button>
    </div>

    <div v-if="loading" class="state-msg">加载中…</div>
    <div v-else-if="error" class="state-msg error">{{ error }}</div>
    <div v-else-if="list.length === 0" class="state-msg">暂无内容</div>
    <div v-else class="qr-grid">
      <div v-for="q in list" :key="q.id" class="qr-card">
        <div class="qr-img" :style="q.image_url ? `background-image:url(${q.image_url})` : ''">
          <span v-if="!q.image_url" class="qr-placeholder">📷 无图片</span>
        </div>
        <div class="qr-info">
          <div class="qr-title-row">
            <span class="qr-title">{{ q.title }}</span>
            <span :class="['badge', q.is_active ? 'badge-success' : 'badge-default']">{{ q.is_active ? '启用' : '停用' }}</span>
          </div>
          <div class="qr-desc">{{ q.description || '无描述' }}</div>
          <div class="qr-url" v-if="q.target_url">{{ q.target_url }}</div>
          <div class="qr-meta">排序值：{{ q.sort_order }}</div>
        </div>
        <div class="qr-actions">
          <button class="btn-action-sm" @click="openEdit(q)">编辑</button>
          <button class="btn-warning-sm" @click="toggleActive(q)">{{ q.is_active ? '停用' : '启用' }}</button>
          <button class="btn-danger-sm" @click="confirmDelete(q)">删除</button>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-mask">
      <div class="modal-box">
        <h3 class="modal-title">{{ editingId ? '编辑内容' : '添加内容' }}</h3>
        <div class="form-group"><label>标题</label><input class="form-input" v-model="form.title" placeholder="标题" /></div>
        <div class="form-group"><label>描述</label><textarea class="form-textarea" v-model="form.description" placeholder="描述" rows="3"></textarea></div>
        <div class="form-group"><label>图片URL</label><input class="form-input" v-model="form.image_url" placeholder="https://..." /></div>
        <div class="form-group"><label>跳转链接（可选）</label><input class="form-input" v-model="form.target_url" placeholder="https://..." /></div>
        <div class="form-group"><label>排序值（越大越靠前）</label><input type="number" class="form-input" v-model.number="form.sort_order" /></div>
        <div class="form-group"><label><input type="checkbox" v-model="form.is_active" /> 立即启用</label></div>
        <div class="modal-actions">
          <button class="btn-outline" @click="closeModal">取消</button>
          <button class="btn-primary" @click="doSave" :disabled="saving">{{ saving ? '保存中…' : '保存' }}</button>
        </div>
      </div>
    </div>

    <div v-if="deleteTarget" class="modal-mask">
      <div class="modal-box">
        <h3 class="modal-title">确认删除</h3>
        <p class="modal-msg">确定删除「{{ deleteTarget.title }}」？</p>
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

const form = reactive({ title: '', description: '', image_url: '', target_url: '', sort_order: 0, is_active: true })

const fetch = async () => {
  loading.value = true; error.value = ''
  try { list.value = await adminContentApi.listQrs() }
  catch (e: any) { error.value = e.message }
  finally { loading.value = false }
}

const openCreate = () => { editingId.value = null; Object.assign(form, { title:'', description:'', image_url:'', target_url:'', sort_order:0, is_active:true }); showModal.value = true }
const openEdit = (q: any) => {
  editingId.value = q.id
  Object.assign(form, { title: q.title, description: q.description, image_url: q.image_url, target_url: q.target_url || '', sort_order: q.sort_order, is_active: q.is_active })
  showModal.value = true
}
const closeModal = () => { showModal.value = false; editingId.value = null }

const doSave = async () => {
  if (!form.title.trim()) { feedback.warning('请输入标题'); return }
  saving.value = true
  try {
    if (editingId.value) await adminContentApi.updateQr(editingId.value, { ...form })
    else await adminContentApi.createQr({ ...form })
    feedback.success('保存成功'); closeModal(); fetch()
  } catch (e: any) { feedback.error(e.message || '保存失败') }
  finally { saving.value = false }
}

const toggleActive = async (q: any) => {
  try { await adminContentApi.updateQr(q.id, { is_active: !q.is_active }); feedback.success(q.is_active ? '已停用' : '已启用'); fetch() }
  catch (e: any) { feedback.error(e.message) }
}

const confirmDelete = (q: any) => { deleteTarget.value = q }
const doDelete = async () => {
  if (!deleteTarget.value) return
  deleting.value = true
  try { await adminContentApi.deleteQr(deleteTarget.value.id); feedback.success('已删除'); deleteTarget.value = null; fetch() }
  catch (e: any) { feedback.error(e.message || '删除失败') }
  finally { deleting.value = false }
}

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
.qr-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:16px; }
.qr-card { background:#fff; border:1px solid #f0f0f0; border-radius:12px; padding:16px; }
.qr-img { width:100%; height:140px; background:#fafafa; border-radius:8px; background-size:cover; background-position:center; display:flex; align-items:center; justify-content:center; }
.qr-placeholder { color:#bbb; font-size:13px; }
.qr-info { margin-top:12px; }
.qr-title-row { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.qr-title { font-size:14px; font-weight:600; color:#1a1a2e; }
.qr-desc { font-size:12px; color:#666; margin-bottom:4px; }
.qr-url { font-size:11px; color:#aaa; word-break:break-all; }
.qr-meta { font-size:11px; color:#bbb; margin-top:4px; }
.qr-actions { display:flex; gap:6px; margin-top:12px; }
.btn-action-sm { font-size:11px; padding:3px 10px; background:none; color:#aa3bff; border:1px solid #aa3bff; border-radius:4px; cursor:pointer; }
.btn-warning-sm { font-size:11px; padding:3px 8px; color:#faad14; background:none; border:1px solid #faad14; border-radius:4px; cursor:pointer; }
.btn-danger-sm { font-size:11px; padding:3px 8px; color:#ff4d4f; background:none; border:1px solid #ff4d4f; border-radius:4px; cursor:pointer; }
.badge { font-size:11px; padding:2px 8px; border-radius:10px; font-weight:600; }
.badge-success { background:#f6ffed; color:#52c41a; }
.badge-default { background:#f5f5f5; color:#888; }
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:1000; }
.modal-box { background:#fff; border-radius:12px; padding:28px; width:520px; max-width:90vw; }
.modal-title { font-size:18px; font-weight:700; color:#1a1a2e; margin-bottom:20px; }
.modal-msg { color:#555; margin-bottom:20px; }
.form-group { margin-bottom:16px; }
.form-group label { display:block; font-size:13px; font-weight:600; color:#555; margin-bottom:6px; }
.form-input, .form-textarea { width:100%; padding:8px 12px; border:1px solid #e5e4e7; border-radius:8px; font-size:14px; box-sizing:border-box; }
.form-textarea { resize:vertical; }
.modal-actions { display:flex; justify-content:flex-end; gap:10px; margin-top:20px; }
.btn-outline { padding:8px 18px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:8px; cursor:pointer; }
.btn-danger { padding:8px 18px; background:#ff4d4f; color:#fff; border:none; border-radius:8px; cursor:pointer; }
</style>
