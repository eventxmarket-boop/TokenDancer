<script setup lang="ts">
import { reactive, ref } from 'vue'
import MaterialInputPanel from '@/components/shared/MaterialInputPanel.vue'
import { requestReplyAssistant, type ReplyAssistantResponse } from '@/services/replyAssistantService'
import type { UniversalCreateWizardRawMaterials } from '@/services/createWizardService'

type ReplyAssistantTargetType =
  | 'crush'
  | 'partner'
  | 'ex'
  | 'colleague'
  | 'boss'
  | 'client'
  | 'public_sector'
  | 'mentor'
  | 'friend'
  | 'family'

type ReplyAssistantSceneType =
  | 'daily'
  | 'conflict'
  | 'push_forward'
  | 'work_report'
  | 'follow_up'
  | 'formal_notice'
  | 'rejection'
  | 'repair'

type RewriteMode = 'alt' | 'soft' | 'boundary' | 'formal' | 'short'

const targetPersonOptions: Array<[ReplyAssistantTargetType, string]> = [
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

const sceneOptions: Array<[ReplyAssistantSceneType, string, string]> = [
  ['daily', '日常聊天', '普通消息、寒暄、接话。'],
  ['conflict', '冷战 / 冲突', '有情绪、有摩擦、需要缓和。'],
  ['push_forward', '推进关系', '想往前一步，但要控制节奏。'],
  ['work_report', '工作汇报', '汇报进度、同步结果、说明情况。'],
  ['follow_up', '跟进未回复', '催进度或提醒对方查看。'],
  ['formal_notice', '正式通知', '正式告知、邮件、公告、流程性回复。'],
  ['rejection', '拒绝 / 婉拒', '想拒绝但保持体面。'],
  ['repair', '解释误会 / 修复', '澄清误会、修复关系、缓和气氛。'],
]

const rewriteButtons: Array<{ label: string; mode: RewriteMode }> = [
  { label: '换一个版本', mode: 'alt' },
  { label: '更软一点', mode: 'soft' },
  { label: '更有边界一点', mode: 'boundary' },
  { label: '更正式一点', mode: 'formal' },
  { label: '更简短一点', mode: 'short' },
]

function createEmptyMaterialState(): UniversalCreateWizardRawMaterials {
  return {
    chat_history_text: '',
    memory_notes_text: '',
    text_materials_text: '',
    uploaded_text_documents: [],
    uploaded_image_documents: [],
    ocr_extracted_texts: [],
    image_notes_text: '',
    photo_notes_text: '',
    voice_notes_text: '',
    diary_text: '',
    letter_text: '',
    conflict_text: '',
    draft_message_text: '',
    recent_context_text: '',
    reply_style_samples_text: '',
    relationship_status_text: '',
    interaction_patterns_text: '',
    history_text: '',
    expression_samples_text: '',
  }
}

const form = reactive({
  message: '',
  current_context: '',
  target_person_type: 'crush' as ReplyAssistantTargetType,
  scene_type: 'daily' as ReplyAssistantSceneType,
  target_goal: '更稳妥',
  conversation_context: '',
})

const rawMaterials = ref<UniversalCreateWizardRawMaterials>(createEmptyMaterialState())
const loading = ref(false)
const error = ref('')
const result = ref<ReplyAssistantResponse | null>(null)

async function generateReply(rewriteMode: RewriteMode | 'default' = 'default') {
  loading.value = true
  error.value = ''

  try {
    result.value = await requestReplyAssistant({
      message: form.message,
      target_person_type: form.target_person_type,
      target_person_label: targetPersonOptions.find(([value]) => value === form.target_person_type)?.[1] || '',
      scene_type: form.scene_type,
      current_context: form.current_context,
      target_goal: form.target_goal,
      conversation_context: form.conversation_context,
      rewrite_mode: rewriteMode,
      raw_materials: rawMaterials.value,
    })
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '生成回复建议失败'
    result.value = null
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page-hero page-hero--single reply-assistant-hero">
    <div class="hero-copy">
      <p class="eyebrow">回复助手</p>
      <h1>我该怎么回</h1>
    </div>
    <div class="hero-actions">
      <RouterLink class="secondary-btn" to="/reply-assistant">回入口页</RouterLink>
    </div>
  </section>

  <section class="section-card reply-assistant-workbench">
    <div class="reply-assistant-layout">
      <div class="reply-assistant-column">
        <article class="wizard-stage">
          <div class="section-head">
            <div>
              <h3>对方发来的内容</h3>
            </div>
          </div>

          <label class="form-field">
            <span>对方原话 / 聊天内容</span>
            <textarea
              v-model="form.message"
              class="field-input reply-assistant-textarea"
              rows="6"
              placeholder="贴原话"
            ></textarea>
          </label>

          <label class="form-field">
            <span>补充上下文</span>
            <textarea
              v-model="form.current_context"
              class="field-input reply-assistant-textarea"
              rows="4"
              placeholder="补上下文"
            ></textarea>
          </label>

          <div class="form-grid">
            <label class="form-field">
              <span>对方是什么人</span>
              <select v-model="form.target_person_type" class="field-input">
                <option v-for="[value, label] in targetPersonOptions" :key="value" :value="value">
                  {{ label }}
                </option>
              </select>
            </label>
            <label class="form-field">
              <span>当前场景</span>
              <select v-model="form.scene_type" class="field-input">
                <option v-for="[value, label] in sceneOptions" :key="value" :value="value">
                  {{ label }}
                </option>
              </select>
            </label>
          </div>

          <label class="form-field">
              <span>你的目标</span>
            <textarea
              v-model="form.target_goal"
              class="field-input reply-assistant-textarea"
              rows="4"
              placeholder="想要什么"
            ></textarea>
          </label>

          <div class="hero-actions reply-assistant-actions">
            <button class="primary-btn" type="button" :disabled="loading || !form.message.trim()" @click="generateReply()">
              {{ loading ? '生成中…' : '生成回复建议' }}
            </button>
          </div>

          <details class="advanced-panel">
            <summary>材料</summary>
            <div class="advanced-panel__body">
              <label class="form-field">
                <span>补充聊天</span>
                <textarea
                  v-model="form.conversation_context"
                  class="field-input reply-assistant-textarea"
                  rows="4"
                  placeholder="前后聊天"
                ></textarea>
              </label>

              <MaterialInputPanel
                v-model="rawMaterials"
                path-type="relationship"
                :supports-guided-prompts="false"
              />
            </div>
          </details>

          <div v-if="error" class="state-panel">
            <p class="eyebrow">失败</p>
            <h3>生成失败</h3>
            <p class="state-copy">{{ error }}</p>
          </div>
        </article>
      </div>

      <div class="reply-assistant-column reply-assistant-column--output">
        <article class="summary-panel">
          <p class="eyebrow">判断</p>
          <h3>{{ result?.judgment || '先输入内容。' }}</h3>
        </article>

        <article class="summary-panel">
          <p class="eyebrow">推荐</p>
          <div class="reply-main">
            <p class="state-copy">{{ result?.recommended_reply || '这里显示可发送回复。' }}</p>
          </div>
          <div class="rewrite-actions">
            <button
              v-for="item in rewriteButtons"
              :key="item.mode"
              class="chip-btn"
              type="button"
              :disabled="loading || !form.message.trim()"
              @click="generateReply(item.mode)"
            >
              {{ item.label }}
            </button>
          </div>
        </article>

        <article class="summary-panel">
          <p class="eyebrow">风险</p>
          <p class="state-copy">{{ result?.risk_note || '这里显示风险。' }}</p>
        </article>

        <article class="summary-panel">
          <p class="eyebrow">后果</p>
          <p class="state-copy">{{ result?.likely_consequence || '这里显示走向。' }}</p>
        </article>
      </div>
    </div>
  </section>
</template>

<style scoped>
.reply-assistant-layout {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1.08fr) minmax(0, 0.92fr);
}

.reply-assistant-column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.reply-assistant-workbench {
  padding-bottom: 2rem;
}

.reply-assistant-textarea {
  min-height: 110px;
}

.reply-assistant-actions {
  margin-top: 0.25rem;
}

.advanced-panel {
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 0.85rem 1rem;
  background: rgba(255, 255, 255, 0.58);
}

.advanced-panel summary {
  cursor: pointer;
  list-style: none;
  font-weight: 700;
  color: var(--text);
}

.advanced-panel summary::-webkit-details-marker {
  display: none;
}

.advanced-panel__body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.reply-main {
  min-height: 72px;
}

.rewrite-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-top: 0.9rem;
}

@media (max-width: 980px) {
  .reply-assistant-layout {
    grid-template-columns: 1fr;
  }
}
</style>
