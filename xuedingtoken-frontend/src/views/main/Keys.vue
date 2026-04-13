<template>
  <MainLayout title="API 密钥" subtitle="管理平台 API Key，直接用于 /v1/chat/completions 和 /v1/models">
    <div class="toolbar">
      <button class="btn btn-outline btn-sm" :disabled="loading" @click="handleRefresh">
        🔄 {{ loading ? '刷新中...' : '刷新' }}
      </button>
      <button class="btn btn-primary btn-sm" :disabled="!canCreateKey" @click="showCreate = true">+ 创建密钥</button>
    </div>

    <div class="endpoint-grid">
      <div class="endpoint-card card">
        <div class="endpoint-label">Chat Completions</div>
        <div class="endpoint-row">
          <code class="endpoint-url">{{ chatEndpoint }}</code>
          <CopyButton :text="chatEndpoint" label="复制" @click="feedback.success('中转地址已复制')" />
        </div>
      </div>
      <div class="endpoint-card card">
        <div class="endpoint-label">Models</div>
        <div class="endpoint-row">
          <code class="endpoint-url">{{ modelsEndpoint }}</code>
          <CopyButton :text="modelsEndpoint" label="复制" @click="feedback.success('模型列表地址已复制')" />
        </div>
      </div>
    </div>

    <div class="tips-card card">
      <div class="tips-title">实战提示</div>
      <ul class="tips-list">
        <li>平台 API Key 走 Bearer 鉴权，不依赖后台登录态。</li>
        <li>可按模型白名单限制调用范围，适合给不同业务线分发。</li>
        <li>到期时间为空表示长期有效；停用后会立即拒绝中转请求。</li>
      </ul>
    </div>

    <div :class="['chain-card card', canCreateKey ? 'chain-ready' : 'chain-pending']">
      <div class="chain-title">配置链状态</div>
      <p class="chain-desc" v-if="modelsLoading">正在读取当前可用公版模型…</p>
      <p class="chain-desc" v-else-if="modelsError">{{ modelsError }}</p>
      <template v-else-if="availableModels.length > 0">
        <p class="chain-desc">管理员已完成至少一条可用 Model Route。你现在可以创建平台 API Key，并按这些公版模型配置白名单。</p>
        <div class="model-chip-wrap">
          <button v-for="model in availableModels" :key="model" class="model-chip" @click="appendAllowedModel(model)">{{ model }}</button>
        </div>
      </template>
      <p v-else class="chain-desc">当前还没有可用 Model Route。请先由管理员按顺序完成 Provider -> Provider Key -> Model Route 配置，平台 API Key 才会进入真实可用状态。</p>
    </div>

    <div class="filter-row">
      <input class="input filter-search" placeholder="搜索名称 / Key / 模型" v-model="keyStore.search" />
      <select class="select filter-select" v-model="keyStore.filterGroup">
        <option value="全部">全部分组</option>
        <option v-for="group in groups" :key="group" :value="group">{{ group }}</option>
      </select>
      <select class="select filter-select" v-model="keyStore.filterStatus">
        <option value="全部">全部状态</option>
        <option value="active">启用</option>
        <option value="disabled">停用</option>
      </select>
    </div>

    <div v-if="loading" class="loading-wrap">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="fetchError" class="error-wrap card">
      <div class="error-icon">⚠️</div>
      <p>{{ fetchError }}</p>
      <button class="btn btn-outline btn-sm mt-4" @click="handleRefresh">重试</button>
    </div>

    <div v-else class="table-card card">
      <table class="table">
        <thead>
          <tr>
            <th>名称</th>
            <th>API 密钥</th>
            <th>分组</th>
            <th>可访问模型</th>
            <th>过期时间</th>
            <th>状态</th>
            <th>最近使用</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="keyStore.filtered.length === 0">
            <td colspan="9">
              <BaseEmpty
                icon="🔑"
                title="暂无 API 密钥"
                :desc="canCreateKey ? '创建您的第一个平台 API Key 后，就可以直接走 OpenAI 兼容接口。' : '请先由管理员完成 Provider -> Provider Key -> Model Route 配置。'"
                action="创建密钥"
                @action="showCreate = canCreateKey"
              />
            </td>
          </tr>
          <tr v-for="key in keyStore.filtered" :key="key.id">
            <td>
              <strong>{{ key.name }}</strong>
              <div class="sub-info" v-if="key.last_used_model">最近模型：{{ key.last_used_model }}</div>
            </td>
            <td>
              <code class="key-code">{{ showFullKey === key.id ? key.key_value : maskKey(key.key_value) }}</code>
              <div class="inline-actions">
                <button class="btn btn-ghost btn-xs" @click="toggleKey(key.id)">
                  {{ showFullKey === key.id ? '隐藏' : '查看' }}
                </button>
                <button class="btn btn-ghost btn-xs" @click="handleCopyKey(key.key_value)">复制</button>
              </div>
            </td>
            <td><span class="badge badge-primary">{{ key.group_name }}</span></td>
            <td>
              <span v-if="key.allowed_models" class="model-list">{{ key.allowed_models }}</span>
              <span v-else class="muted">全部模型</span>
            </td>
            <td>{{ formatDateTime(key.expires_at) || '永久有效' }}</td>
            <td>
              <span :class="['badge', key.status === 'active' ? 'badge-success' : 'badge-danger']">
                {{ key.status === 'active' ? '启用' : '停用' }}
              </span>
            </td>
            <td>{{ key.last_used_at ? formatDateTime(key.last_used_at) : '从未使用' }}</td>
            <td>{{ formatDateTime(key.created_at) }}</td>
            <td>
              <div class="action-btns">
                <button class="btn btn-ghost btn-xs" :disabled="togglingKeyId === key.id || deletingKeyId === key.id" @click="handleToggle(key.id, key.status)">
                  {{ togglingKeyId === key.id ? '处理中...' : (key.status === 'active' ? '停用' : '启用') }}
                </button>
                <button class="btn btn-ghost btn-xs text-danger" :disabled="deletingKeyId === key.id || togglingKeyId === key.id" @click="handleDelete(key.id)">
                  {{ deletingKeyId === key.id ? '删除中...' : '删除' }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <BaseModal v-model="showCreate" title="创建 API 密钥">
      <div class="form-group">
        <label class="label">密钥名称</label>
        <input class="input" placeholder="如：生产环境网关 Key" v-model="formName" />
      </div>
      <div class="form-group">
        <label class="label">分组</label>
        <input class="input" placeholder="如：production / staging / team-a" v-model="formGroup" />
      </div>
      <div class="form-group">
        <label class="label">允许模型</label>
        <input class="input" placeholder="留空=全部模型；多个模型用逗号分隔" v-model="formAllowedModels" />
        <div class="form-help" v-if="availableModels.length">点击下方模型可快速加入白名单</div>
        <div class="model-chip-wrap compact" v-if="availableModels.length">
          <button v-for="model in availableModels" :key="model" class="model-chip" @click="appendAllowedModel(model)">{{ model }}</button>
        </div>
      </div>
      <div class="form-group">
        <label class="label">过期时间</label>
        <input class="input" type="datetime-local" v-model="formExpiresAt" />
      </div>
      <div class="modal-actions">
        <button class="btn btn-outline" @click="showCreate = false">取消</button>
        <button class="btn btn-primary" :disabled="!canCreateKey" @click="handleCreateKey">确认创建</button>
      </div>
    </BaseModal>
  </MainLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import MainLayout from '@/components/main/MainLayout.vue'
import CopyButton from '@/components/common/CopyButton.vue'
import BaseEmpty from '@/components/common/BaseEmpty.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import { API_BASE_URL, api } from '@/api/client'
import { useKeyStore } from '@/stores/keys'
import { useFeedbackStore } from '@/stores/feedback'

const keyStore = useKeyStore()
const feedback = useFeedbackStore()
const loading = ref(false)
const fetchError = ref<string | null>(null)
const showCreate = ref(false)
const formName = ref('')
const formGroup = ref('production')
const formAllowedModels = ref('')
const formExpiresAt = ref('')
const showFullKey = ref<number | null>(null)
const availableModels = ref<string[]>([])
const modelsLoading = ref(false)
const modelsError = ref('')
const deletingKeyId = ref<number | null>(null)
const togglingKeyId = ref<number | null>(null)

const chatEndpoint = `${API_BASE_URL}/v1/chat/completions`
const modelsEndpoint = `${API_BASE_URL}/v1/models`
const canCreateKey = computed(() => availableModels.value.length > 0)

const groups = computed(() => {
  const defaults = ['production', 'staging', 'team-a']
  return Array.from(new Set([...defaults, ...keyStore.keys.map((item: any) => item.group_name).filter(Boolean)])).sort()
})

const maskKey = (key: string) => `${key.slice(0, 8)}...${key.slice(-4)}`
const formatDateTime = (value?: string | null) => value ? new Date(value).toLocaleString('zh-CN') : ''

const toggleKey = (id: number) => {
  showFullKey.value = showFullKey.value === id ? null : id
}

const resetCreateForm = () => {
  formName.value = ''
  formGroup.value = 'production'
  formAllowedModels.value = ''
  formExpiresAt.value = ''
}

const appendAllowedModel = (model: string) => {
  const current = formAllowedModels.value.split(',').map((item) => item.trim()).filter(Boolean)
  if (!current.includes(model)) {
    current.push(model)
    formAllowedModels.value = current.join(', ')
  }
}

const loadAvailableModels = async () => {
  modelsLoading.value = true
  modelsError.value = ''
  try {
    const result = await api.get<{ models: string[]; can_create: boolean }>('/keys/available-models')
    availableModels.value = result.models || []
  } catch (e: any) {
    availableModels.value = []
    modelsError.value = e.message || '可用模型读取失败'
  } finally {
    modelsLoading.value = false
  }
}

const handleRefresh = async () => {
  keyStore.search = ''
  keyStore.filterGroup = '全部'
  keyStore.filterStatus = '全部'
  loading.value = true
  fetchError.value = null
  try {
    await Promise.all([keyStore.fetchKeys(), loadAvailableModels()])
    feedback.info('已刷新列表')
  } catch (e: any) {
    fetchError.value = e.message
    feedback.error(e.message)
  } finally {
    loading.value = false
  }
}

const handleCopyKey = (key: string) => {
  navigator.clipboard.writeText(key)
  feedback.success('Key 已复制')
}

const handleCreateKey = async () => {
  if (!canCreateKey.value) {
    feedback.warning('当前还没有可用 Model Route，请先联系管理员完成配置')
    return
  }
  if (!formName.value.trim()) {
    feedback.warning('请填写密钥名称')
    return
  }

  const selectedModels = formAllowedModels.value.split(',').map((item) => item.trim()).filter(Boolean)
  const invalidModels = selectedModels.filter((model) => !availableModels.value.includes(model))
  if (invalidModels.length) {
    feedback.warning(`以下模型当前不可用：${invalidModels.join(', ')}`)
    return
  }

  try {
    await keyStore.createKey({
      name: formName.value.trim(),
      group_name: formGroup.value.trim() || 'production',
      allowed_models: selectedModels.length ? selectedModels.join(', ') : null,
      expires_at: formExpiresAt.value ? new Date(formExpiresAt.value).toISOString() : null,
    })
    feedback.success('API Key 创建成功')
    resetCreateForm()
    showCreate.value = false
  } catch (e: any) {
    feedback.error(e.message)
  }
}

const handleDelete = async (id: number) => {
  const ok = await feedback.confirm({
    title: '删除确认',
    message: '确定要删除此 API Key 吗？该操作不可撤销。',
    danger: true,
  })
  if (!ok) return

  try {
    deletingKeyId.value = id
    await keyStore.deleteKey(id)
    feedback.success('Key 已删除')
  } catch (e: any) {
    feedback.error(e.message)
  } finally {
    deletingKeyId.value = null
  }
}

const handleToggle = async (id: number, currentStatus: string) => {
  const newStatus = currentStatus === 'active' ? 'disabled' : 'active'
  try {
    togglingKeyId.value = id
    await keyStore.updateKey(id, { status: newStatus })
    feedback.info(`密钥已${newStatus === 'active' ? '启用' : '停用'}`)
  } catch (e: any) {
    feedback.error(e.message)
  } finally {
    togglingKeyId.value = null
  }
}

onMounted(async () => {
  loading.value = true
  fetchError.value = null
  try {
    await Promise.all([keyStore.fetchKeys(), loadAvailableModels()])
  } catch (e: any) {
    fetchError.value = e.message || '加载失败'
    feedback.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 20px;
}
.endpoint-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.endpoint-card {
  padding: 18px 20px;
  background: #f9fafb;
  border: 0;
}
.endpoint-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}
.endpoint-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.endpoint-url {
  font-family: monospace;
  font-size: 13px;
  font-weight: 500;
  background: var(--color-bg-secondary);
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  color: var(--color-text);
}
.tips-card {
  margin-bottom: 16px;
  background: linear-gradient(135deg, #f7fbff, #f2f7ff);
}
.tips-title {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 10px;
}
.tips-list {
  margin: 0;
  padding-left: 18px;
  color: var(--color-text-secondary);
  display: grid;
  gap: 6px;
}
.chain-card {
  margin-bottom: 24px;
}
.chain-ready {
  background: #f6ffed;
  border-color: #b7eb8f;
}
.chain-pending {
  background: #fffbe6;
  border-color: #ffe58f;
}
.chain-title {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 10px;
}
.chain-desc {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
}
.model-chip-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.model-chip-wrap.compact {
  margin-top: 10px;
}
.model-chip {
  border: 1px solid var(--color-border);
  background: #fff;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
}
.model-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.filter-row {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.filter-search { max-width: 260px; }
.filter-select { max-width: 160px; }
.loading-wrap {
  text-align: center;
  padding: 64px 0;
  color: var(--color-text-secondary);
}
.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }
.error-wrap {
  text-align: center;
  padding: 64px 0;
}
.error-icon { font-size: 48px; opacity: 0.5; margin-bottom: 12px; }
.table-card {
  overflow: hidden;
  padding: 0;
}
.key-code {
  font-family: monospace;
  font-size: 12px;
  background: var(--color-bg-secondary);
  padding: 2px 6px;
  border-radius: 4px;
}
.inline-actions,
.action-btns {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-top: 6px;
  flex-wrap: wrap;
}
.btn-xs { padding: 2px 6px; font-size: 11px; }
.text-danger { color: var(--color-danger) !important; }
.model-list {
  display: inline-block;
  max-width: 220px;
  white-space: normal;
  word-break: break-word;
  line-height: 1.4;
}
.sub-info {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.muted { color: var(--color-text-secondary); }
.form-group { margin-bottom: 16px; }
.form-help {
  margin-top: 8px;
  color: var(--color-text-secondary);
  font-size: 12px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

@media (max-width: 900px) {
  .endpoint-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .toolbar {
    justify-content: stretch;
  }
  .toolbar .btn {
    width: 100%;
  }
  .filter-search,
  .filter-select {
    max-width: none;
    width: 100%;
  }
  .table-card {
    overflow-x: auto;
  }
  .table {
    min-width: 720px;
  }
  .endpoint-card {
    padding: 16px;
  }
}
</style>
