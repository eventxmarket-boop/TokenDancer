<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  deleteReplyCorpus,
  activateLlmConfig,
  getLlmConfig,
  getReplyCorpusDashboard,
  saveLlmConfig,
  saveReplyCorpus,
  updateReplyCorpus,
  updateLlmConfig,
  type LlmConfig,
  type LlmConfigPayload,
  type ReplyCorpus,
  type ReplyCorpusPayload,
} from '@/services/adminService'

const loading = ref(true)
const saving = ref(false)
const activatingId = ref<number | null>(null)
const error = ref('')
const notice = ref('')
const items = ref<LlmConfig[]>([])
const current = ref<LlmConfig | null>(null)
const editingId = ref<number | null>(null)
const corpusLoading = ref(true)
const corpusSaving = ref(false)
const corpusError = ref('')
const corpusNotice = ref('')
const corpusItems = ref<ReplyCorpus[]>([])
const corpusEditingId = ref<number | null>(null)
const corpusFileInputRef = ref<HTMLInputElement | null>(null)
const monitorTargets = ref([
  { name: 'Mescladís 1', url: '' },
  { name: 'Mescladís 2', url: '' },
  { name: 'Mescladís 3', url: '' },
  { name: 'Mescladís 4', url: '' },
  { name: 'Mescladís 5', url: '' },
])

const targetPersonOptions: Array<[string, string]> = [
  ['any', '通用'],
  ['crush', '暧昧对象'],
  ['partner', '伴侣'],
  ['ex', '前任'],
  ['colleague', '同事'],
  ['boss', '上司 / 领导'],
  ['client', '客户 / 对接方'],
  ['public_sector', '体制内 / 公务沟通'],
  ['mentor', '导师 / 前辈'],
  ['friend', '朋友'],
  ['family', '家人'],
]

const sceneOptions: Array<[string, string]> = [
  ['any', '通用'],
  ['daily', '日常聊天'],
  ['conflict', '冷战 / 冲突'],
  ['push_forward', '推进关系'],
  ['work_report', '工作汇报'],
  ['follow_up', '跟进未回复'],
  ['formal_notice', '正式通知'],
  ['rejection', '拒绝 / 婉拒'],
  ['repair', '解释误会 / 修复'],
]

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
const emptyCorpusForm = (): ReplyCorpusPayload => ({
  id: null,
  title: '',
  target_person_type: 'any',
  scene_type: 'any',
  corpus_type: '通用',
  content: '',
  sort_order: 0,
  is_enabled: true,
})

const corpusForm = reactive<ReplyCorpusPayload>(emptyCorpusForm())

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

const applyToCorpusForm = (corpus: ReplyCorpus | null) => {
  const next = corpus
    ? {
        id: corpus.id,
        title: corpus.title || '',
        target_person_type: corpus.target_person_type || 'any',
        scene_type: corpus.scene_type || 'any',
        corpus_type: corpus.corpus_type || '高情商回复',
        content: corpus.content || '',
        sort_order: corpus.sort_order ?? 0,
        is_enabled: corpus.is_enabled,
      }
    : {
        ...emptyCorpusForm(),
        id: null,
      }

  corpusEditingId.value = corpus ? corpus.id : null
  Object.assign(corpusForm, next)
}

const loadReplyCorpusDashboard = async () => {
  corpusLoading.value = true
  corpusError.value = ''

  try {
    const dashboard = await getReplyCorpusDashboard()
    corpusItems.value = dashboard.items
    applyToCorpusForm(dashboard.items[0] || null)
  } catch (cause) {
    corpusError.value = cause instanceof Error ? cause.message : '加载语料失败'
    corpusItems.value = []
    applyToCorpusForm(null)
  } finally {
    corpusLoading.value = false
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

const resetCorpusForm = () => {
  corpusNotice.value = ''
  applyToCorpusForm(null)
}

const editCorpus = (corpus: ReplyCorpus) => {
  corpusNotice.value = ''
  applyToCorpusForm(corpus)
}

const targetPersonLabel = (value: string) =>
  targetPersonOptions.find(([key]) => key === value)?.[1] || value || '通用'

const sceneLabel = (value: string) => sceneOptions.find(([key]) => key === value)?.[1] || value || '通用'

const corpusScopeLabel = computed(() => {
  const target = targetPersonLabel(corpusForm.target_person_type)
  const scene = sceneLabel(corpusForm.scene_type)
  if (corpusForm.target_person_type === 'any' && corpusForm.scene_type === 'any') {
    return '通用'
  }
  return `${target} · ${scene}`
})

const triggerCorpusFilePicker = () => {
  corpusFileInputRef.value?.click()
}

const handleCorpusFileUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement | null
  const files = input?.files
  if (!files || !files.length) {
    return
  }

  const textChunks: string[] = []
  for (const file of Array.from(files)) {
    const extension = file.name.split('.').pop()?.toLowerCase() || ''
    if (!['txt', 'md', 'csv', 'log'].includes(extension) && !file.type.startsWith('text/')) {
      continue
    }
    const text = (await file.text()).trim()
    if (text) {
      textChunks.push(`【${file.name}】\n${text}`)
    }
  }

  if (textChunks.length) {
    corpusForm.content = corpusForm.content ? `${corpusForm.content}\n\n${textChunks.join('\n\n')}` : textChunks.join('\n\n')
    corpusNotice.value = '文件内容已导入到语料框'
  }

  if (input) {
    input.value = ''
  }
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

const submitCorpusForm = async () => {
  if (corpusSaving.value) {
    return
  }

  corpusSaving.value = true
  corpusError.value = ''
  corpusNotice.value = ''

  const payload: ReplyCorpusPayload = {
    ...corpusForm,
    id: corpusEditingId.value,
    title: corpusForm.title.trim(),
    target_person_type: corpusForm.target_person_type,
    scene_type: corpusForm.scene_type,
    corpus_type: corpusScopeLabel.value,
    content: corpusForm.content.trim(),
    sort_order: Number(corpusForm.sort_order || 0),
  }

  try {
    if (corpusEditingId.value) {
      await updateReplyCorpus(corpusEditingId.value, payload)
      corpusNotice.value = '语料已更新'
    } else {
      await saveReplyCorpus(payload)
      corpusNotice.value = '语料已保存'
    }
    await loadReplyCorpusDashboard()
  } catch (cause) {
    corpusError.value = cause instanceof Error ? cause.message : '保存语料失败'
  } finally {
    corpusSaving.value = false
  }
}

const removeCorpus = async (id: number) => {
  if (!window.confirm('删除后无法找回，确定要删除这条语料吗？')) {
    return
  }

  corpusSaving.value = true
  corpusError.value = ''
  corpusNotice.value = ''

  try {
    await deleteReplyCorpus(id)
    corpusNotice.value = '语料已删除'
    await loadReplyCorpusDashboard()
    if (corpusEditingId.value === id) {
      resetCorpusForm()
    }
  } catch (cause) {
    corpusError.value = cause instanceof Error ? cause.message : '删除语料失败'
  } finally {
    corpusSaving.value = false
  }
}

onMounted(() => {
  void loadDashboard()
  void loadReplyCorpusDashboard()
})
</script>

<template>
  <section class="admin-layout">
    <article class="section-card">
      <div class="section-head">
        <div>
          <p class="eyebrow">内部科研</p>
          <h3>Image-2</h3>
          <p class="section-note">直接从 admin 进入，不需要打开 `/persona-api/` 根地址。</p>
        </div>
        <div class="hero-actions">
          <RouterLink class="secondary-btn" to="/image-lab">打开 Image Lab</RouterLink>
        </div>
      </div>

      <div class="admin-grid">
        <section class="mini-panel">
          <p class="side-title">接口入口</p>
          <div class="state-copy">
            <p><strong>页面：</strong><RouterLink to="/image-lab">/image-lab</RouterLink></p>
            <p><strong>接口：</strong><code>/persona-api/image-lab/generate</code></p>
            <p><strong>模型：</strong>gpt-image-2</p>
          </div>
        </section>

        <section class="mini-panel">
          <p class="side-title">接入方式</p>
          <div class="state-copy">
            <p>前端直接走同域 `/persona-api` 前缀。</p>
            <p>后端从环境变量读取 OpenAI Key。</p>
            <p>这里只做内部测试，不落盘保存图片。</p>
          </div>
        </section>

        <section class="mini-panel">
          <p class="side-title">Plus Bridge（实验）</p>
          <div class="state-copy">
            <p>本机已登录 ChatGPT Plus 时，可用 Playwright 做本地桥接。</p>
            <p><code>npm run plus:bridge -- --bootstrap</code></p>
            <p><code>npm run plus:bridge -- --prompt "..." --upload-url /persona-api/image-lab/bridge/submit</code></p>
            <p>桥接结果只做临时 handoff，不保存原始图片文件。</p>
          </div>
        </section>
      </div>
    </article>

    <article class="section-card">
      <div class="section-head">
        <div>
          <p class="eyebrow">后台专用</p>
          <h3>预约监控</h3>
          <p class="section-note">仅管理员可见。脚本位于服务器根目录，普通前端不会展示这块内容。</p>
        </div>
      </div>

      <div class="admin-grid">
        <section class="mini-panel">
          <p class="side-title">部署位置</p>
          <div class="state-copy">
            <p><strong>脚本：</strong><code>/opt/xuedingtoken_latest/monitor.js</code></p>
            <p><strong>状态文件：</strong><code>/opt/xuedingtoken_latest/state.json</code></p>
            <p><strong>环境文件：</strong><code>/opt/xuedingtoken_latest/.env</code></p>
          </div>
        </section>

        <section class="mini-panel">
          <p class="side-title">启动方式</p>
          <div class="state-copy">
            <p><code>cd /opt/xuedingtoken_latest</code></p>
            <p><code>npm install</code></p>
            <p><code>npm run install:chromium</code></p>
            <p><code>npm run monitor</code></p>
          </div>
        </section>
      </div>

      <section class="mini-panel" style="margin-top: 16px;">
        <p class="side-title">监控目标占位</p>
        <div class="config-list">
          <article v-for="target in monitorTargets" :key="target.name" class="config-card">
            <div class="config-card__head">
              <div>
                <p class="spotlight-card__label">{{ target.name }}</p>
                <h4>Google Calendar appointment schedule</h4>
              </div>
            </div>
            <p class="state-copy">
              {{ target.url || '请在服务器 .env 中填写对应的 TARGET_*_URL' }}
            </p>
          </article>
        </div>
      </section>
    </article>

    <article class="section-card">
      <div class="section-head">
        <div>
          <p class="eyebrow">后台设置</p>
          <h3>大模型配置</h3>
          <p class="section-note">这里先做一套最小可用配置，改完立刻影响聊天链路。</p>
        </div>
        <div class="hero-actions">
          <RouterLink class="secondary-btn" to="/image-lab">Image Lab</RouterLink>
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

    <article class="section-card">
      <div class="section-head">
        <div>
          <p class="eyebrow">我该怎么回</p>
          <h3>语料开口</h3>
          <p class="section-note">按对象和场景喂语料，启用后会进入回复助手。</p>
        </div>
        <div class="hero-actions">
          <button class="ghost-btn" type="button" @click="resetCorpusForm">新建语料</button>
        </div>
      </div>

      <div v-if="corpusLoading" class="state-panel">
        <p class="eyebrow">加载中</p>
        <h3>正在读取回复语料…</h3>
      </div>

      <div v-else class="admin-grid">
        <section class="mini-panel">
          <p class="side-title">语料编辑</p>
          <form class="admin-form" @submit.prevent="submitCorpusForm">
            <div class="form-grid">
              <label class="form-field">
                <span>对象</span>
                <select v-model="corpusForm.target_person_type" class="field-input">
                  <option v-for="[value, label] in targetPersonOptions" :key="value" :value="value">
                    {{ label }}
                  </option>
                </select>
              </label>
              <label class="form-field">
                <span>场景</span>
                <select v-model="corpusForm.scene_type" class="field-input">
                  <option v-for="[value, label] in sceneOptions" :key="value" :value="value">
                    {{ label }}
                  </option>
                </select>
              </label>
              <label class="form-field">
                <span>标题</span>
                <input v-model="corpusForm.title" class="field-input" type="text" :placeholder="corpusScopeLabel" />
              </label>
              <label class="form-field">
                <span>排序</span>
                <input v-model.number="corpusForm.sort_order" class="field-input" type="number" step="1" placeholder="越大越靠前" />
              </label>
            </div>

            <div class="state-copy" style="margin-top: 8px;">
              当前类型：{{ corpusScopeLabel }}。排序数字越大，展示越靠前。
            </div>

            <label class="form-field" style="margin-top: 12px;">
              <span>语料内容</span>
              <textarea
                v-model="corpusForm.content"
                class="field-input"
                rows="8"
                placeholder="建议直接粘贴回复样例，比如：场景 / 原话 / 参考回复。"
              />
            </label>

            <input
              ref="corpusFileInputRef"
              type="file"
              accept=".txt,.md,.csv,text/plain,text/markdown,text/csv"
              style="display: none;"
              @change="handleCorpusFileUpload"
            />

            <div class="form-actions" style="justify-content: flex-start; margin-top: 10px;">
              <button class="secondary-btn" type="button" @click="triggerCorpusFilePicker">上传文件</button>
            </div>

            <div class="toggle-row">
              <label class="field-check">
                <input v-model="corpusForm.is_enabled" type="checkbox" />
                <span>启用</span>
              </label>
            </div>

            <div class="form-actions">
              <button class="primary-btn" type="submit" :disabled="corpusSaving">
                {{ corpusEditingId ? '保存修改' : '保存语料' }}
              </button>
              <button class="secondary-btn" type="button" @click="loadReplyCorpusDashboard">刷新</button>
            </div>
          </form>
        </section>

        <section class="mini-panel">
          <p class="side-title">已保存语料</p>
          <div v-if="!corpusItems.length" class="state-copy">
            现在还没有回复语料，先贴一条就能开始用。
          </div>
          <div v-else class="config-list">
            <article v-for="corpus in corpusItems" :key="corpus.id" class="config-card">
              <div class="config-card__head">
                <div>
                  <p class="spotlight-card__label">#{{ corpus.id }}</p>
                  <h4>{{ corpus.title || corpus.corpus_type }}</h4>
                </div>
                <div class="config-badges">
                  <span class="status-pill" :class="{ active: corpus.is_enabled }">
                    {{ corpus.is_enabled ? '启用' : '停用' }}
                  </span>
                  <span class="status-pill active">{{ targetPersonLabel(corpus.target_person_type) }}</span>
                  <span class="status-pill active">{{ sceneLabel(corpus.scene_type) }}</span>
                </div>
              </div>

              <p class="state-copy">
                {{ corpus.content.slice(0, 120) }}{{ corpus.content.length > 120 ? '…' : '' }}
              </p>
              <p class="state-copy">
                排序 {{ corpus.sort_order }} · 类型 {{ corpus.corpus_type }}
              </p>

              <div class="form-actions">
                <button class="secondary-btn" type="button" @click="editCorpus(corpus)">编辑</button>
                <button class="ghost-btn" type="button" @click="removeCorpus(corpus.id)">删除</button>
              </div>
            </article>
          </div>
        </section>
      </div>

      <p v-if="corpusNotice" class="state-copy" style="color: #4d8a62; margin-top: 12px;">
        {{ corpusNotice }}
      </p>
      <p v-if="corpusError" class="state-copy" style="color: #c85d4c; margin-top: 12px;">
        {{ corpusError }}
      </p>
    </article>
  </section>
</template>
