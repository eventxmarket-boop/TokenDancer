<template>
  <div class="page-container">
    <div class="page-title-row">
      <div>
        <h1 class="page-title">API 可视化测试工作台</h1>
        <p class="page-subtitle">直接在后台发起真实中转请求，验证本次测试到底命中了哪个 Provider、哪个 Source Key、哪条路由策略。</p>
      </div>
      <div class="title-actions">
        <button class="btn-outline-sm" @click="loadOptions">🔄 刷新配置</button>
        <button class="btn-outline-sm" @click="resetSession">🆕 新建会话</button>
      </div>
    </div>

    <div v-if="loadError" class="alert-card alert-danger">{{ loadError }}</div>
    <div v-else-if="!loadingOptions && !options.models.length" class="alert-card alert-warning">
      当前还没有可用的 Model Route。请先完成“渠道管理 → 源 Key 池 → 模型映射 → 路由策略”配置后再测试。
    </div>

    <div class="workspace-grid">
      <AdminSectionCard title="测试配置区">
        <div class="config-grid">
          <div class="form-group span2">
            <label>公版模型 <span class="req">*</span></label>
            <select v-model="form.public_model_name" class="form-select">
              <option value="">— 选择可测试模型 —</option>
              <option v-for="route in options.models" :key="route.id" :value="route.public_model_name">
                {{ route.public_model_name }} / {{ route.provider_name || route.provider_id }}
              </option>
            </select>
            <div class="field-help">来源于真实 Model Route 列表。没有模型时，说明配置链还没闭环。</div>
          </div>

          <div class="form-group">
            <label>路由模式</label>
            <select v-model="form.route_mode" class="form-select">
              <option value="auto">自动路由</option>
              <option value="provider">指定 Provider</option>
              <option value="provider_key">指定 Source Key</option>
            </select>
          </div>

          <div v-if="form.route_mode !== 'auto'" class="form-group">
            <label>Provider</label>
            <select v-model="form.provider_id" class="form-select">
              <option value="">— 选择 Provider —</option>
              <option v-for="provider in eligibleProviders" :key="provider.id" :value="String(provider.id)">
                {{ provider.name }} / {{ provider.provider_type }}
              </option>
            </select>
          </div>

          <div v-if="form.route_mode === 'provider_key'" class="form-group span2">
            <label>Source Key</label>
            <select v-model="form.provider_key_id" class="form-select">
              <option value="">— 选择 Source Key —</option>
              <option v-for="item in eligibleProviderKeys" :key="item.id" :value="String(item.id)">
                {{ item.name }} / {{ item.provider_name }} / {{ item.key_masked }}
              </option>
            </select>
            <div class="field-help">Source Key 只能来自当前模型映射的候选 Provider，不会绕开真实配置链。</div>
          </div>

          <div class="form-group">
            <label>Temperature</label>
            <input v-model.number="form.temperature" type="number" min="0" max="2" step="0.1" class="form-input" />
          </div>
          <div class="form-group">
            <label>Max Tokens</label>
            <input v-model.number="form.max_tokens" type="number" min="1" max="8192" class="form-input" />
          </div>
          <div class="form-group">
            <label>流式</label>
            <select v-model="form.stream" class="form-select" disabled>
              <option :value="false">当前仅支持非流式</option>
            </select>
          </div>
        </div>

        <div v-if="selectedRoute" class="route-brief">
          <div class="brief-title">当前模型映射</div>
          <div class="brief-line">主路由：{{ selectedRoute.provider_name || selectedRoute.provider_id }} / {{ selectedRoute.provider_model_name }}</div>
          <div class="brief-line">备路由：{{ selectedRoute.fallback_provider_name || '未配置' }} / {{ selectedRoute.fallback_model_name || '—' }}</div>
          <div class="brief-line">策略：{{ selectedPolicy?.name || '未配置策略' }} / {{ selectedPolicy?.policy_type || selectedRoute.policy_type }}</div>
        </div>

        <div class="config-actions">
          <button class="btn-outline" @click="clearContext">清空上下文</button>
          <button class="btn-primary" :disabled="!canSend || running" @click="handleSend">
            {{ running ? '发送中…' : '发送测试请求' }}
          </button>
        </div>
      </AdminSectionCard>

      <AdminSectionCard title="执行结果 / 命中详情区">
        <div v-if="!latestResult" class="empty-result">
          发送一次测试请求后，这里会展示真实命中的 Provider / Source Key / Route Policy / fallback 轨迹。
        </div>
        <template v-else>
          <div class="result-header">
            <span :class="['result-badge', latestResult.success ? 'badge-success' : 'badge-danger']">
              {{ latestResult.success ? '请求成功' : '请求失败' }}
            </span>
            <span class="result-meta">HTTP {{ latestResult.status_code }}</span>
            <span class="result-meta">{{ latestResult.latency_ms ? `${latestResult.latency_ms}ms` : '—' }}</span>
          </div>

          <div class="detail-grid">
            <div class="detail-item"><span class="detail-label">Provider</span><span class="detail-value">{{ latestResult.provider_name || '—' }}</span></div>
            <div class="detail-item"><span class="detail-label">Provider Type</span><span class="detail-value">{{ latestResult.provider_type || '—' }}</span></div>
            <div class="detail-item"><span class="detail-label">Source Key</span><span class="detail-value">{{ latestResult.provider_key_name || '—' }}</span></div>
            <div class="detail-item"><span class="detail-label">Route Policy</span><span class="detail-value">{{ latestResult.policy_name || '—' }} / {{ latestResult.policy_type || '—' }}</span></div>
            <div class="detail-item"><span class="detail-label">上游模型</span><span class="detail-value">{{ latestResult.upstream_model_name || '—' }}</span></div>
            <div class="detail-item"><span class="detail-label">请求日志 ID</span><span class="detail-value">{{ latestResult.request_log_id || '—' }}</span></div>
            <div class="detail-item"><span class="detail-label">Provider 切换</span><span class="detail-value">{{ latestResult.provider_switch_count ?? 0 }}</span></div>
            <div class="detail-item"><span class="detail-label">Key 切换</span><span class="detail-value">{{ latestResult.key_switch_count ?? 0 }}</span></div>
            <div class="detail-item"><span class="detail-label">Fallback</span><span class="detail-value">{{ latestResult.fallback_triggered ? '触发' : '未触发' }}</span></div>
            <div class="detail-item"><span class="detail-label">日志写入</span><span class="detail-value">{{ latestResult.log_written ? '已写入' : '未写入' }}</span></div>
            <div class="detail-item"><span class="detail-label">Source Key 使用态</span><span class="detail-value">{{ latestResult.source_key_usage_updated ? '已更新' : '未更新' }}</span></div>
            <div class="detail-item"><span class="detail-label">最后使用</span><span class="detail-value">{{ formatDateTime(latestResult.source_key_last_used_at) }}</span></div>
          </div>

          <div v-if="latestResult.forced_provider_honored !== null || latestResult.forced_source_key_honored !== null" class="forced-checks">
            <div class="forced-item" v-if="latestResult.forced_provider_honored !== null">强制 Provider 命中：{{ latestResult.forced_provider_honored ? '已命中' : '未命中' }}</div>
            <div class="forced-item" v-if="latestResult.forced_source_key_honored !== null">强制 Source Key 命中：{{ latestResult.forced_source_key_honored ? '已命中' : '未命中' }}</div>
          </div>

          <div v-if="latestResult.usage" class="usage-strip">
            <div class="usage-chip">Prompt {{ latestResult.usage.prompt_tokens ?? 0 }}</div>
            <div class="usage-chip">Completion {{ latestResult.usage.completion_tokens ?? 0 }}</div>
            <div class="usage-chip">Total {{ latestResult.usage.total_tokens ?? 0 }}</div>
          </div>

          <div v-if="latestResult.failure_chain_summary || latestResult.error_summary" class="error-panel">
            <div class="error-title">错误 / 失败链</div>
            <div v-if="latestResult.error_summary" class="error-line">{{ latestResult.error_summary }}</div>
            <div v-if="latestResult.failure_chain_summary" class="error-line muted">{{ latestResult.failure_chain_summary }}</div>
          </div>

          <div class="jump-actions">
            <button class="btn-action-sm" @click="goToLogs">查看请求日志</button>
            <button class="btn-action-sm" @click="goToKeyStatus">查看 Source Key 状态</button>
            <button class="btn-action-sm" @click="goToProviderHealth">查看 Provider 健康</button>
            <button class="btn-action-sm" @click="goToRoutingStatus">查看路由配置状态</button>
          </div>
        </template>
      </AdminSectionCard>
    </div>

    <AdminSectionCard title="Chat 对话测试区">
      <div class="chat-shell">
        <div class="chat-history">
          <div v-if="messages.length === 0" class="chat-empty">从这里开始一轮真实中转测试。消息会按多轮上下文发送，不会只做一次性 ping。</div>
          <div v-for="message in messages" :key="message.id" :class="['chat-row', `chat-${message.role}`]">
            <div class="chat-avatar">{{ message.role === 'user' ? '你' : message.role === 'assistant' ? 'AI' : '!' }}</div>
            <div class="chat-bubble">
              <div class="chat-role">{{ message.role === 'user' ? '管理员' : message.role === 'assistant' ? '模型响应' : '执行异常' }}</div>
              <div class="chat-content">{{ message.content }}</div>
            </div>
          </div>
          <div v-if="running" class="chat-row chat-system">
            <div class="chat-avatar">…</div>
            <div class="chat-bubble loading-bubble">
              <div class="chat-role">正在请求真实上游</div>
              <div class="chat-content">本次请求会走真实模型映射、路由策略、Provider / Source Key 选择与日志写入。</div>
            </div>
          </div>
        </div>

        <div class="composer">
          <textarea
            v-model="draft"
            class="composer-input"
            rows="4"
            :disabled="running || !options.models.length"
            placeholder="输入要测试的问题，例如：请只回复 OK，并说明你命中的上游模型。"
          />
          <div class="composer-footer">
            <span class="composer-hint">上下文消息 {{ messages.length }} 条</span>
            <button class="btn-primary" :disabled="!canSend || running" @click="handleSend">
              {{ running ? '发送中…' : '发送消息' }}
            </button>
          </div>
        </div>
      </div>
    </AdminSectionCard>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import { adminProxyTesterApi, type AdminProxyTesterMessage, type AdminProxyTesterOptions, type AdminProxyTesterResult } from '@/api/adminProxyTester'
import type { AdminModelRoute } from '@/api/adminModelRoutes'
import type { AdminProvider } from '@/api/adminProviders'
import type { AdminProviderKey } from '@/api/adminProviderKeys'
import type { AdminRoutePolicy } from '@/api/adminRoutePolicies'
import { useFeedbackStore } from '@/stores/feedback'

interface ChatRow {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
}

const router = useRouter()
const feedback = useFeedbackStore()
const loadingOptions = ref(false)
const loadError = ref('')
const running = ref(false)
const options = reactive<AdminProxyTesterOptions>({
  models: [],
  providers: [],
  provider_keys: [],
  route_policies: [],
})
const draft = ref('')
const messages = ref<ChatRow[]>([])
const latestResult = ref<AdminProxyTesterResult | null>(null)
const form = reactive({
  public_model_name: '',
  route_mode: 'auto' as 'auto' | 'provider' | 'provider_key',
  provider_id: '',
  provider_key_id: '',
  temperature: 0.7,
  max_tokens: 512,
  stream: false,
})

const selectedRoute = computed<AdminModelRoute | null>(() => options.models.find((item) => item.public_model_name === form.public_model_name) || null)
const selectedPolicy = computed<AdminRoutePolicy | null>(() => options.route_policies.find((item) => item.public_model_name === form.public_model_name && item.is_active) || null)
const eligibleProviderIds = computed(() => {
  const ids = new Set<number>()
  if (selectedRoute.value?.provider_id) ids.add(selectedRoute.value.provider_id)
  if (selectedRoute.value?.fallback_provider_id) ids.add(selectedRoute.value.fallback_provider_id)
  return ids
})
const eligibleProviders = computed<AdminProvider[]>(() => options.providers.filter((item) => eligibleProviderIds.value.has(item.id)))
const eligibleProviderKeys = computed<AdminProviderKey[]>(() => {
  const providerId = form.provider_id ? Number(form.provider_id) : null
  return options.provider_keys.filter((item) => {
    if (!eligibleProviderIds.value.has(item.provider_id)) return false
    if (providerId && item.provider_id !== providerId) return false
    return item.status === 'active'
  })
})
const canSend = computed(() => {
  if (!form.public_model_name || !draft.value.trim() || running.value || !options.models.length) return false
  if (form.route_mode === 'provider' && !form.provider_id) return false
  if (form.route_mode === 'provider_key' && !form.provider_key_id) return false
  return true
})

watch(() => form.public_model_name, () => {
  const validProvider = eligibleProviders.value.some((item) => String(item.id) === form.provider_id)
  if (!validProvider) form.provider_id = ''
  const validKey = eligibleProviderKeys.value.some((item) => String(item.id) === form.provider_key_id)
  if (!validKey) form.provider_key_id = ''
})

watch(() => form.provider_id, () => {
  const validKey = eligibleProviderKeys.value.some((item) => String(item.id) === form.provider_key_id)
  if (!validKey) form.provider_key_id = ''
})

watch(() => form.provider_key_id, (value) => {
  if (!value) return
  const key = options.provider_keys.find((item) => String(item.id) === value)
  if (key) form.provider_id = String(key.provider_id)
})

const formatDateTime = (value?: string | null) => {
  if (!value) return '—'
  return new Date(value).toLocaleString('zh-CN')
}

const toTesterMessages = (): AdminProxyTesterMessage[] =>
  messages.value
    .filter((item) => item.role !== 'system')
    .map((item) => ({
      role: item.role,
      content: item.content,
    }))

const addMessage = (role: ChatRow['role'], content: string) => {
  messages.value.push({
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    content,
  })
}

const loadOptions = async () => {
  loadingOptions.value = true
  loadError.value = ''
  try {
    const payload = await adminProxyTesterApi.getOptions()
    options.models = payload.models
    options.providers = payload.providers
    options.provider_keys = payload.provider_keys
    options.route_policies = payload.route_policies
    if (!form.public_model_name && options.models.length) {
      form.public_model_name = options.models[0].public_model_name
    }
  } catch (error: any) {
    loadError.value = error?.message || '加载测试工作台配置失败'
  } finally {
    loadingOptions.value = false
  }
}

const clearContext = () => {
  messages.value = []
  latestResult.value = null
}

const resetSession = () => {
  clearContext()
  draft.value = ''
  form.route_mode = 'auto'
  form.provider_id = ''
  form.provider_key_id = ''
  form.temperature = 0.7
  form.max_tokens = 512
}

const handleSend = async () => {
  if (!canSend.value) return

  const userContent = draft.value.trim()
  addMessage('user', userContent)
  draft.value = ''
  running.value = true

  try {
    const result = await adminProxyTesterApi.run({
      public_model_name: form.public_model_name,
      route_mode: form.route_mode,
      provider_id: form.provider_id ? Number(form.provider_id) : undefined,
      provider_key_id: form.provider_key_id ? Number(form.provider_key_id) : undefined,
      temperature: form.temperature,
      max_tokens: form.max_tokens,
      stream: false,
      messages: toTesterMessages(),
    })
    latestResult.value = result
    if (result.success && result.assistant_message) {
      addMessage('assistant', result.assistant_message)
      feedback.success('测试请求已成功返回')
    } else {
      addMessage('system', `请求失败（HTTP ${result.status_code}）：${result.error_summary || '未知错误'}`)
      feedback.error(result.error_summary || '测试请求失败')
    }
  } catch (error: any) {
    const message = error?.message || '测试请求失败'
    latestResult.value = null
    addMessage('system', `请求异常：${message}`)
    feedback.error(message)
  } finally {
    running.value = false
  }
}

const goToLogs = () => {
  router.push({ path: '/admin/api-proxy/proxy-logs', query: { public_model_name: latestResult.value?.public_model_name || form.public_model_name } })
}
const goToKeyStatus = () => router.push('/admin/system/key-status')
const goToProviderHealth = () => router.push('/admin/system/provider-health')
const goToRoutingStatus = () => router.push('/admin/system/routing-status')

onMounted(loadOptions)
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 20px; }
.page-title-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.page-title { font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 0; }
.page-subtitle { margin: 6px 0 0; color: #667085; font-size: 13px; line-height: 1.6; max-width: 880px; }
.title-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.alert-card { padding: 14px 16px; border-radius: 12px; font-size: 13px; line-height: 1.6; }
.alert-danger { background: #fff1f0; color: #cf1322; border: 1px solid #ffccc7; }
.alert-warning { background: #fffbe6; color: #ad6800; border: 1px solid #ffe58f; }
.workspace-grid { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr); gap: 20px; }
.config-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group.span2 { grid-column: span 2; }
.form-group label { font-size: 12px; font-weight: 600; color: #344054; }
.form-input, .form-select, .composer-input {
  width: 100%; border: 1px solid #d0d5dd; border-radius: 10px; padding: 10px 12px;
  font-size: 13px; line-height: 1.5; background: #fff; color: #101828; box-sizing: border-box;
}
.form-input:focus, .form-select:focus, .composer-input:focus { outline: none; border-color: #1677ff; box-shadow: 0 0 0 3px rgba(22,119,255,0.08); }
.req { color: #d92d20; }
.field-help { font-size: 12px; color: #667085; line-height: 1.5; }
.route-brief { margin-top: 16px; padding: 14px; border-radius: 12px; background: #f8fafc; border: 1px solid #e2e8f0; }
.brief-title { font-size: 12px; font-weight: 700; color: #475467; margin-bottom: 8px; }
.brief-line { font-size: 13px; color: #344054; line-height: 1.6; }
.config-actions { margin-top: 18px; display: flex; gap: 10px; justify-content: flex-end; flex-wrap: wrap; }
.empty-result { font-size: 13px; color: #667085; line-height: 1.7; min-height: 160px; display: flex; align-items: center; }
.result-header { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
.result-badge { display: inline-flex; align-items: center; padding: 5px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.badge-success { background: #ecfdf3; color: #027a48; }
.badge-danger { background: #fef3f2; color: #b42318; }
.result-meta { font-size: 12px; color: #667085; }
.detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.detail-item { padding: 10px 12px; border-radius: 12px; background: #f8fafc; border: 1px solid #e2e8f0; }
.detail-label { display: block; font-size: 11px; color: #667085; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.4px; }
.detail-value { font-size: 13px; color: #101828; font-weight: 600; word-break: break-word; }
.forced-checks { margin-top: 14px; display: flex; gap: 10px; flex-wrap: wrap; }
.forced-item { padding: 8px 12px; border-radius: 999px; background: #eef4ff; color: #175cd3; font-size: 12px; font-weight: 600; }
.usage-strip { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
.usage-chip { padding: 8px 12px; border-radius: 999px; background: #f5f7fa; color: #344054; font-size: 12px; font-weight: 600; }
.error-panel { margin-top: 14px; padding: 14px; border-radius: 12px; background: #fff7ed; border: 1px solid #fed7aa; }
.error-title { font-size: 12px; font-weight: 700; color: #9a3412; margin-bottom: 8px; }
.error-line { font-size: 13px; line-height: 1.6; color: #7c2d12; word-break: break-word; }
.error-line.muted { color: #9a3412; opacity: 0.85; margin-top: 6px; }
.jump-actions { margin-top: 16px; display: flex; gap: 10px; flex-wrap: wrap; }
.chat-shell { display: flex; flex-direction: column; gap: 16px; }
.chat-history { min-height: 300px; max-height: 560px; overflow-y: auto; padding: 4px; display: flex; flex-direction: column; gap: 14px; }
.chat-empty { min-height: 240px; display: flex; align-items: center; justify-content: center; text-align: center; color: #667085; font-size: 13px; padding: 20px; border: 1px dashed #d0d5dd; border-radius: 16px; background: #fafcff; }
.chat-row { display: flex; gap: 12px; align-items: flex-start; }
.chat-user { justify-content: flex-end; }
.chat-user .chat-bubble { background: linear-gradient(135deg, #1677ff, #4096ff); color: #fff; }
.chat-user .chat-role, .chat-user .chat-content { color: #fff; }
.chat-avatar { width: 32px; height: 32px; border-radius: 50%; background: #e4e7ec; color: #344054; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.chat-bubble { max-width: min(760px, 78%); padding: 12px 14px; border-radius: 16px; background: #f8fafc; border: 1px solid #e2e8f0; }
.chat-role { font-size: 11px; font-weight: 700; color: #667085; margin-bottom: 6px; }
.chat-content { font-size: 14px; line-height: 1.7; color: #101828; white-space: pre-wrap; word-break: break-word; }
.chat-system .chat-bubble { background: #fff7ed; border-color: #fed7aa; }
.loading-bubble { border-style: dashed; }
.composer { border-top: 1px solid #eaecf0; padding-top: 16px; display: flex; flex-direction: column; gap: 10px; }
.composer-input { resize: vertical; min-height: 110px; }
.composer-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.composer-hint { font-size: 12px; color: #667085; }
.btn-primary, .btn-outline, .btn-outline-sm, .btn-action-sm {
  border-radius: 10px; cursor: pointer; font-weight: 600; transition: all 0.2s ease; border: 1px solid transparent;
}
.btn-primary { background: #1677ff; color: #fff; padding: 10px 16px; }
.btn-primary:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-outline, .btn-outline-sm, .btn-action-sm { background: #fff; color: #344054; border-color: #d0d5dd; }
.btn-outline { padding: 10px 16px; }
.btn-outline-sm, .btn-action-sm { padding: 8px 12px; font-size: 12px; }
.btn-primary:hover:not(:disabled), .btn-outline:hover, .btn-outline-sm:hover, .btn-action-sm:hover { transform: translateY(-1px); }

@media (max-width: 1180px) {
  .workspace-grid { grid-template-columns: 1fr; }
}

@media (max-width: 720px) {
  .page-title-row { flex-direction: column; }
  .config-grid, .detail-grid { grid-template-columns: 1fr; }
  .form-group.span2 { grid-column: span 1; }
  .chat-bubble { max-width: 100%; }
  .composer-footer, .config-actions { flex-direction: column; align-items: stretch; }
  .jump-actions { flex-direction: column; }
}
</style>
