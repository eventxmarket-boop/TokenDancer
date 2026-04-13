<template>
  <MainLayout title="API 测试" subtitle="直接测试当前账号可用的正式 API 中转入口">
    <div class="playground">
      <div class="params-card card">
        <h3 class="section-title">模型参数</h3>
        <div class="params-row">
          <div class="param-group">
            <label class="label">模型</label>
            <select class="select" v-model="model" :disabled="loading || modelsLoading || availableModels.length === 0">
              <option value="">{{ modelsLoading ? '加载模型中...' : '请选择可用模型' }}</option>
              <option v-for="item in availableModels" :key="item.id" :value="item.id">
                {{ item.id }}
              </option>
            </select>
            <div class="param-help" v-if="modelsError">{{ modelsError }}</div>
            <div class="param-help" v-else-if="availableModels.length === 0">当前没有可用模型，请先联系管理员完成中转配置。</div>
          </div>
          <div class="param-group">
            <label class="label">Temperature</label>
            <input class="input" type="number" v-model.number="temperature" min="0" max="2" step="0.1" />
          </div>
          <div class="param-group">
            <label class="label">Max Tokens</label>
            <input class="input" type="number" v-model.number="maxTokens" min="1" max="8192" />
          </div>
          <div class="param-group stream-param">
            <label class="label">流式</label>
            <div class="stream-disabled">
              <select class="select" v-model="stream" disabled>
                <option :value="false">关闭</option>
              </select>
              <span class="stream-hint">当前测试页仅支持非流式调用</span>
            </div>
          </div>
        </div>
      </div>

      <div class="input-card card">
        <h3 class="section-title">消息内容</h3>
        <textarea
          class="textarea"
          v-model="userMessage"
          placeholder="输入你的问题..."
          rows="5"
          :disabled="loading"
        ></textarea>
        <div class="input-footer">
          <span class="char-count">{{ userMessage.length }} 字符</span>
          <button
            class="btn btn-primary"
            :disabled="loading || !userMessage.trim() || !model"
            @click="handleSend"
          >
            {{ loading ? '⏳ 发送中...' : '▶ 发送请求' }}
          </button>
        </div>
      </div>

      <div class="response-card card">
        <h3 class="section-title">回复内容</h3>

        <div v-if="responseMeta" class="response-meta">
          <span class="meta-chip">状态码 {{ responseMeta.statusCode }}</span>
          <span class="meta-chip">{{ responseMeta.statusText }}</span>
          <span class="meta-chip">{{ responseMeta.latencyMs != null ? `${responseMeta.latencyMs}ms` : '耗时待返回' }}</span>
        </div>

        <div v-if="status === 'empty'" class="empty-state">
          <div class="empty-icon">💬</div>
          <p>发送请求后，回复内容将显示在这里</p>
        </div>

        <div v-else-if="status === 'loading'" class="loading-state">
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
          <p>等待模型响应...</p>
        </div>

        <div v-else-if="status === 'error'" class="error-state">
          <div class="error-badge">❌ 请求失败</div>
          <pre class="error-text">{{ errorMessage }}</pre>
        </div>

        <div v-else class="success-state">
          <div class="response-content" v-html="renderedContent"></div>
        </div>
      </div>

      <div class="usage-card card" v-if="usageInfo">
        <h3 class="section-title">本次用量</h3>
        <div class="usage-grid">
          <div class="usage-item">
            <span class="usage-label">Prompt Tokens</span>
            <strong class="usage-value">{{ usageInfo.prompt_tokens ?? 0 }}</strong>
          </div>
          <div class="usage-item">
            <span class="usage-label">Completion Tokens</span>
            <strong class="usage-value">{{ usageInfo.completion_tokens ?? 0 }}</strong>
          </div>
          <div class="usage-item">
            <span class="usage-label">Total Tokens</span>
            <strong class="usage-value">{{ usageInfo.total_tokens ?? 0 }}</strong>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import MainLayout from '@/components/main/MainLayout.vue'
import { chatCompletions, listProxyModels, type ChatCompletionsPayload } from '@/api/proxy'

type Status = 'empty' | 'loading' | 'error' | 'success'
type ProxyModel = { id: string }

const model = ref('')
const temperature = ref(0.7)
const maxTokens = ref(1024)
const stream = ref(false)
const userMessage = ref('')
const status = ref<Status>('empty')
const errorMessage = ref('')
const responseText = ref('')
const responseMeta = ref<{ statusCode: number; statusText: string; latencyMs: number | null } | null>(null)
const usageInfo = ref<{ prompt_tokens?: number; completion_tokens?: number; total_tokens?: number } | null>(null)
const availableModels = ref<ProxyModel[]>([])
const modelsLoading = ref(false)
const modelsError = ref('')
const loading = computed(() => status.value === 'loading')

const renderedContent = computed(() => {
  return responseText.value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
})

const loadModels = async () => {
  modelsLoading.value = true
  modelsError.value = ''
  try {
    const result = await listProxyModels()
    availableModels.value = Array.isArray(result.data) ? result.data : []
    if (!model.value && availableModels.value.length > 0) {
      model.value = availableModels.value[0].id
    }
  } catch (e: any) {
    availableModels.value = []
    modelsError.value = e.message || '可用模型加载失败'
  } finally {
    modelsLoading.value = false
  }
}

const handleSend = async () => {
  if (!userMessage.value.trim() || loading.value || !model.value) return

  status.value = 'loading'
  errorMessage.value = ''
  responseText.value = ''
  responseMeta.value = null
  usageInfo.value = null

  const payload: ChatCompletionsPayload = {
    model: model.value,
    messages: [{ role: 'user', content: userMessage.value }],
    temperature: temperature.value,
    max_tokens: maxTokens.value,
    stream: false,
  }

  try {
    const startedAt = performance.now()
    const res = await chatCompletions(payload)
    responseText.value = res.choices?.[0]?.message?.content || ''
    usageInfo.value = res.usage || null
    responseMeta.value = {
      statusCode: 200,
      statusText: '请求成功',
      latencyMs: res.debug?.latency_ms ?? Math.round(performance.now() - startedAt),
    }
    status.value = 'success'
  } catch (e: any) {
    status.value = 'error'
    errorMessage.value = e.message || '未知错误'
    responseMeta.value = {
      statusCode: Number(e?.status) || 0,
      statusText: '请求失败',
      latencyMs: null,
    }
  }
}

onMounted(loadModels)
</script>

<style scoped>
.playground {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 900px;
}

.card {
  padding: 24px;
  border-radius: var(--radius-lg);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 16px;
}

.params-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 120px;
  gap: 16px;
  align-items: end;
}
.param-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.param-help {
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.input-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.textarea {
  width: 100%;
  resize: vertical;
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  box-sizing: border-box;
  outline: none;
  transition: border-color 0.2s;
}
.textarea:focus {
  border-color: var(--color-primary);
}
.textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.char-count {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.response-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.meta-chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  font-size: 12px;
  color: var(--color-text-secondary);
}
.empty-state,
.loading-state,
.error-state,
.success-state {
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  border: 1px dashed var(--color-border);
  padding: 24px;
}
.empty-state,
.loading-state {
  flex-direction: column;
  gap: 10px;
  color: var(--color-text-secondary);
}
.empty-icon {
  font-size: 32px;
}
.loading-dots {
  display: flex;
  gap: 6px;
}
.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  animation: bounce 0.8s infinite alternate;
}
.loading-dots span:nth-child(2) { animation-delay: 0.1s; }
.loading-dots span:nth-child(3) { animation-delay: 0.2s; }
@keyframes bounce {
  from { transform: translateY(0); opacity: 0.5; }
  to { transform: translateY(-6px); opacity: 1; }
}
.error-state {
  align-items: stretch;
  justify-content: flex-start;
  text-align: left;
  background: #fff5f5;
  border-color: #fecaca;
}
.error-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #fee2e2;
  color: #b91c1c;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 12px;
}
.error-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  color: #7f1d1d;
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.7;
}
.success-state {
  align-items: flex-start;
  justify-content: flex-start;
  text-align: left;
}
.response-content {
  color: var(--color-text);
  font-size: 14px;
  line-height: 1.8;
  width: 100%;
  word-break: break-word;
}

.usage-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.usage-item {
  padding: 14px 16px;
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
}
.usage-label {
  display: block;
  font-size: 11px;
  text-transform: uppercase;
  color: var(--color-text-secondary);
  letter-spacing: 0.04em;
}
.usage-value {
  display: block;
  margin-top: 8px;
  font-size: 20px;
  color: var(--color-text);
}

@media (max-width: 900px) {
  .params-row {
    grid-template-columns: 1fr 1fr;
  }
  .usage-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .playground {
    gap: 16px;
  }
  .card {
    padding: 18px;
  }
  .params-row {
    grid-template-columns: 1fr;
  }
  .usage-grid {
    grid-template-columns: 1fr;
  }
  .input-footer {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
}
</style>
