<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  activateLlmConfig,
  getLlmConfig,
  saveLlmConfig,
  updateLlmConfig,
  type LlmConfig,
  type LlmConfigPayload,
} from '@/services/adminService'

const loading = ref(true)
const saving = ref(false)
const activatingId = ref<number | null>(null)
const error = ref('')
const notice = ref('')
const items = ref<LlmConfig[]>([])
const current = ref<LlmConfig | null>(null)
const editingId = ref<number | null>(null)

const emptyForm = (): LlmConfigPayload => ({
  provider: 'openai_compatible',
  base_url: 'https://api.openai.com/v1',
  api_key: '',
  model_name: 'gpt-5.4-mini',
  temperature: 0.7,
  max_tokens: 800,
  is_default: true,
  is_enabled: true,
})

const form = reactive<LlmConfigPayload>(emptyForm())

const effectiveConfig = computed(
  () => current.value || items.value.find((item) => item.is_default && item.is_enabled) || null,
)

const applyToForm = (config: LlmConfig | null) => {
  const next = config
    ? {
        id: config.id,
        provider: config.provider || 'openai_compatible',
        base_url: config.base_url || 'https://api.openai.com/v1',
        api_key: '',
        model_name: config.model_name || 'gpt-5.4-mini',
        temperature: config.temperature ?? 0.7,
        max_tokens: config.max_tokens ?? 800,
        is_default: config.is_default,
        is_enabled: config.is_enabled,
      }
    : {
        ...emptyForm(),
        id: null,
      }

  editingId.value = config ? config.id : null
  Object.assign(form, next)
}

const loadDashboard = async () => {
  loading.value = true
  error.value = ''

  try {
    const dashboard = await getLlmConfig()
    current.value = dashboard.current
    items.value = dashboard.items
    applyToForm(dashboard.current || dashboard.items[0] || null)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '加载模型配置失败'
    current.value = null
    items.value = []
    applyToForm(null)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  notice.value = ''
  applyToForm(null)
}

const editConfig = (config: LlmConfig) => {
  notice.value = ''
  applyToForm(config)
}

const submitForm = async () => {
  if (saving.value) {
    return
  }

  saving.value = true
  error.value = ''
  notice.value = ''

  const payload: LlmConfigPayload = {
    ...form,
    id: editingId.value,
    api_key: form.api_key.trim(),
    provider: form.provider.trim() || 'openai_compatible',
    base_url: form.base_url.trim(),
    model_name: form.model_name.trim(),
  }

  try {
    if (editingId.value) {
      await updateLlmConfig(editingId.value, payload)
      notice.value = '配置已更新'
    } else {
      await saveLlmConfig(payload)
      notice.value = '配置已保存'
    }
    await loadDashboard()
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '保存模型配置失败'
  } finally {
    saving.value = false
  }
}

const activateConfig = async (id: number) => {
  if (activatingId.value !== null) {
    return
  }

  activatingId.value = id
  error.value = ''
  notice.value = ''

  try {
    await activateLlmConfig(id)
    notice.value = '已切换默认模型'
    await loadDashboard()
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '切换默认模型失败'
  } finally {
    activatingId.value = null
  }
}

onMounted(() => {
  void loadDashboard()
})
</script>

<template>
  <section class="admin-layout">
    <article class="section-card">
      <div class="section-head">
        <div>
          <p class="eyebrow">后台设置</p>
          <h3>大模型配置</h3>
          <p class="section-note">这里先做一套最小可用配置，改完立刻影响聊天链路。</p>
        </div>
        <div class="hero-actions">
          <RouterLink class="secondary-btn" to="/me">返回我的</RouterLink>
          <button class="ghost-btn" type="button" @click="resetForm">新建配置</button>
        </div>
      </div>

      <div v-if="loading" class="state-panel">
        <p class="eyebrow">加载中</p>
        <h3>正在读取当前模型配置…</h3>
      </div>

      <div v-else class="admin-grid">
        <section class="mini-panel">
          <p class="side-title">当前生效模型</p>
          <div v-if="effectiveConfig" class="config-summary">
            <p><strong>provider：</strong>{{ effectiveConfig.provider }}</p>
            <p><strong>model：</strong>{{ effectiveConfig.model_name }}</p>
            <p><strong>base_url：</strong>{{ effectiveConfig.base_url }}</p>
            <p><strong>temperature：</strong>{{ effectiveConfig.temperature }}</p>
            <p><strong>max_tokens：</strong>{{ effectiveConfig.max_tokens }}</p>
            <p><strong>状态：</strong>{{ effectiveConfig.is_default ? '默认' : '非默认' }} / {{ effectiveConfig.is_enabled ? '启用' : '停用' }}</p>
          </div>
          <div v-else class="state-copy">
            当前还没有保存任何模型配置，先填一套就能开始聊天。
          </div>
        </section>

        <section class="mini-panel">
          <p class="side-title">编辑配置</p>
          <form class="admin-form" @submit.prevent="submitForm">
            <div class="form-grid">
              <label class="form-field">
                <span>provider</span>
                <input v-model="form.provider" class="field-input" type="text" placeholder="openai_compatible" />
              </label>
              <label class="form-field">
                <span>base_url</span>
                <input v-model="form.base_url" class="field-input" type="url" placeholder="https://api.openai.com/v1" />
              </label>
              <label class="form-field">
                <span>api_key</span>
                <input v-model="form.api_key" class="field-input" type="password" placeholder="留空则沿用已有密钥" />
              </label>
              <label class="form-field">
                <span>model_name</span>
                <input v-model="form.model_name" class="field-input" type="text" placeholder="gpt-5.4-mini" />
              </label>
              <label class="form-field">
                <span>temperature</span>
                <input v-model.number="form.temperature" class="field-input" type="number" step="0.1" min="0" max="2" />
              </label>
              <label class="form-field">
                <span>max_tokens</span>
                <input v-model.number="form.max_tokens" class="field-input" type="number" step="1" min="1" />
              </label>
            </div>

            <div class="toggle-row">
              <label class="field-check">
                <input v-model="form.is_default" type="checkbox" />
                <span>设为默认</span>
              </label>
              <label class="field-check">
                <input v-model="form.is_enabled" type="checkbox" />
                <span>启用配置</span>
              </label>
            </div>

            <div class="form-actions">
              <button class="primary-btn" type="submit" :disabled="saving">
                {{ editingId ? '保存修改' : '保存配置' }}
              </button>
              <button class="secondary-btn" type="button" @click="loadDashboard">刷新</button>
            </div>
          </form>
        </section>
      </div>

      <p v-if="notice" class="state-copy" style="color: #4d8a62; margin-top: 12px;">
        {{ notice }}
      </p>
      <p v-if="error" class="state-copy" style="color: #c85d4c; margin-top: 12px;">
        {{ error }}
      </p>
    </article>

    <article class="section-card">
      <div class="section-head">
        <div>
          <p class="eyebrow">配置列表</p>
          <h3>已保存的模型卡片</h3>
        </div>
        <p class="section-note">默认配置会被聊天接口优先读取。</p>
      </div>

      <div v-if="!items.length && !loading" class="state-panel">
        <p class="eyebrow">暂无记录</p>
        <h3>现在还没有可选配置。</h3>
      </div>

      <div v-else class="config-list">
        <article v-for="config in items" :key="config.id" class="config-card">
          <div class="config-card__head">
            <div>
              <p class="spotlight-card__label">#{{ config.id }}</p>
              <h4>{{ config.model_name }}</h4>
            </div>
            <div class="config-badges">
              <span class="status-pill" :class="{ active: config.is_default }">
                {{ config.is_default ? '默认' : '候选' }}
              </span>
              <span class="status-pill" :class="{ active: config.is_enabled }">
                {{ config.is_enabled ? '启用' : '停用' }}
              </span>
            </div>
          </div>

          <p class="state-copy">
            {{ config.provider }} · {{ config.base_url }}
          </p>
          <p class="state-copy">
            温度 {{ config.temperature }} · 上限 {{ config.max_tokens }} · 密钥 {{ config.api_key_masked || '未填写' }}
          </p>

          <div class="form-actions">
            <button class="secondary-btn" type="button" @click="editConfig(config)">编辑</button>
            <button
              class="primary-btn"
              type="button"
              :disabled="activatingId !== null && activatingId !== config.id"
              @click="activateConfig(config.id)"
            >
              {{ activatingId === config.id ? '切换中…' : '设为默认' }}
            </button>
          </div>
        </article>
      </div>
    </article>
  </section>
</template>
