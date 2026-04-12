<template>
  <MainLayout title="API 测试" subtitle="直接测试 /proxy/chat/completions 接口">
    <div class="playground">
      <div class="params-card card">
        <h3 class="section-title">模型参数</h3>
        <div class="params-row">
          <div class="param-group">
            <label class="label">模型</label>
            <input class="input" v-model="model" placeholder="如 minimax-chat" />
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
            :disabled="loading || !userMessage.trim()"
            @click="handleSend"
          >
            {{ loading ? '⏳ 发送中...' : '▶ 发送请求' }}
          </button>
        </div>
      </div>

      <div class="response-card card">
        <h3 class="section-title">回复内容</h3>

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
          <div v-if="streamActive" class="stream-indicator">
            <span class="dot"></span> 流式输出中
          </div>
          <div class="response-content" v-html="renderedContent"></div>
        </div>
      </div>

      <div class="debug-card card" v-if="debugInfo">
        <h3 class="section-title">调试信息 <span class="debug-subtitle">以下字段来自后端本次实际执行结果</span></h3>
        <div class="debug-grid">
          <div class="debug-item">
            <span class="debug-label">public_model</span>
            <span class="debug-value">{{ debugInfo.public_model ?? '-' }}</span>
          </div>
          <div class="debug-item">
            <span class="debug-label">upstream_model_name</span>
            <span class="debug-value">{{ debugInfo.upstream_model_name ?? '-' }}</span>
          </div>
          <div class="debug-item">
            <span class="debug-label">provider_type</span>
            <span class="debug-value">{{ debugInfo.provider_type ?? '-' }}</span>
          </div>
          <div class="debug-item">
            <span class="debug-label">provider_id</span>
            <span class="debug-value">{{ debugInfo.provider_id ?? '-' }}</span>
          </div>
          <div class="debug-item">
            <span class="debug-label">provider_key_id</span>
            <span class="debug-value">{{ debugInfo.provider_key_id ?? '-' }}</span>
          </div>
          <div class="debug-item">
            <span class="debug-label">policy_type</span>
            <span class="debug-value">{{ debugInfo.policy_type ?? '-' }}</span>
          </div>
          <div class="debug-item">
            <span class="debug-label">fallback_used</span>
            <span class="debug-value">{{ debugInfo.fallback_used ? '是' : '否' }}</span>
          </div>
          <div class="debug-item">
            <span class="debug-label">provider_switch_count</span>
            <span class="debug-value">{{ debugInfo.provider_switch_count ?? '-' }}</span>
          </div>
          <div class="debug-item">
            <span class="debug-label">key_switch_count</span>
            <span class="debug-value">{{ debugInfo.key_switch_count ?? '-' }}</span>
          </div>
          <div class="debug-item">
            <span class="debug-label">latency_ms</span>
            <span class="debug-value">{{ debugInfo.latency_ms != null ? debugInfo.latency_ms + 'ms' : '-' }}</span>
          </div>
          <div class="debug-item">
            <span class="debug-label">cost</span>
            <span class="debug-value">{{ debugInfo.cost != null ? '$' + Number(debugInfo.cost).toFixed(6) : '-' }}</span>
          </div>
          <div class="debug-item">
            <span class="debug-label">total_tokens</span>
            <span class="debug-value">{{ debugInfo.total_tokens ?? '-' }}</span>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import MainLayout from '@/components/main/MainLayout.vue'
import { chatCompletions, type ChatCompletionsPayload } from '@/api/proxy'

type Status = 'empty' | 'loading' | 'error' | 'success'

const model = ref('minimax-chat')
const temperature = ref(0.7)
const maxTokens = ref(1024)
const stream = ref(false)
const userMessage = ref('')
const status = ref<Status>('empty')
const errorMessage = ref('')
const responseText = ref('')
const streamActive = ref(false)
const debugInfo = ref<Record<string, any> | null>(null)
const loading = computed(() => status.value === 'loading')

const renderedContent = computed(() => {
  return responseText.value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
})

const handleSend = async () => {
  if (!userMessage.value.trim() || loading.value) return

  status.value = 'loading'
  errorMessage.value = ''
  responseText.value = ''
  debugInfo.value = null
  streamActive.value = false

  const payload: ChatCompletionsPayload = {
    model: model.value,
    messages: [{ role: 'user', content: userMessage.value }],
    temperature: temperature.value,
    max_tokens: maxTokens.value,
    stream: false,
  }

  try {
    const res = await chatCompletions(payload)
    responseText.value = res.choices?.[0]?.message?.content || ''
    debugInfo.value = res.debug || null
    status.value = 'success'
  } catch (e: any) {
    status.value = 'error'
    errorMessage.value = e.message || '未知错误'
  }
}
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
  color: var(--color-text-muted);
}

.input,
.select {
  height: 42px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0 12px;
  background: var(--color-bg-secondary);
  color: var(--color-text);
}
.label {
  font-size: 13px;
  color: var(--color-text-muted);
}
.stream-disabled {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.stream-hint {
  font-size: 12px;
  color: var(--color-text-muted);
}

.empty-state,
.loading-state,
.error-state,
.success-state {
  min-height: 160px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.empty-state,
.loading-state {
  align-items: center;
  color: var(--color-text-muted);
}
.empty-icon {
  font-size: 32px;
  margin-bottom: 8px;
}
.loading-dots {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  animation: pulse 1s infinite ease-in-out;
}
.loading-dots span:nth-child(2) { animation-delay: 0.15s; }
.loading-dots span:nth-child(3) { animation-delay: 0.3s; }
@keyframes pulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}
.error-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #cf1322;
  background: #fff1f0;
  border: 1px solid #ffccc7;
  border-radius: 999px;
  padding: 6px 10px;
  width: fit-content;
  margin-bottom: 12px;
}
.error-text,
.response-content {
  white-space: pre-wrap;
  line-height: 1.7;
  color: var(--color-text);
  font-size: 14px;
  margin: 0;
}
.stream-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  font-size: 12px;
  color: var(--color-primary);
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 1s infinite ease-in-out;
}

.debug-subtitle {
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 400;
  margin-left: 6px;
}
.debug-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}
.debug-item {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 12px;
  background: var(--color-bg-secondary);
}
.debug-label {
  display: block;
  font-size: 12px;
  color: var(--color-text-muted);
  margin-bottom: 6px;
}
.debug-value {
  display: block;
  font-size: 13px;
  color: var(--color-text);
  word-break: break-all;
}

@media (max-width: 768px) {
  .params-row {
    grid-template-columns: 1fr;
  }

  .input-footer {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
}
</style>
