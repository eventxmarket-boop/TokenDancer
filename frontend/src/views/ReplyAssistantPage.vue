<script setup lang="ts">
import { reactive, ref } from 'vue'
import MaterialInputPanel from '@/components/shared/MaterialInputPanel.vue'
import {
  requestReplyAssistant,
  type ReplyAssistantResponse,
} from '@/services/replyAssistantService'
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

const toneQuickActions = [
  { label: '更自然一点', value: '自然、清楚、不过度用力。' },
  { label: '更正式一点', value: '正式、克制、可执行。' },
  { label: '更有边界一点', value: '礼貌但不越界。' },
  { label: '更推进一点', value: '适度主动，给下一步空间。' },
  { label: '更简短一点', value: '短一些，适合即时回复。' },
]

const goalQuickActions = [
  { label: '更稳妥', value: '更稳妥' },
  { label: '更自然', value: '更自然' },
  { label: '更推进', value: '更推进' },
  { label: '更克制', value: '更克制' },
  { label: '更职业', value: '更职业' },
  { label: '更有边界', value: '更有边界' },
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
  target_person_type: 'crush' as ReplyAssistantTargetType,
  scene_type: 'daily' as ReplyAssistantSceneType,
  current_context: '',
  target_goal: '更稳妥',
  tone_hint: '',
  relationship_status: '',
  conversation_context: '',
})

const rawMaterials = ref<UniversalCreateWizardRawMaterials>(createEmptyMaterialState())
const loading = ref(false)
const error = ref('')
const result = ref<ReplyAssistantResponse | null>(null)

function applyTonePreset(value: string) {
  form.tone_hint = value
}

function applyGoalPreset(value: string) {
  form.target_goal = value
}

async function generateReply() {
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
      tone_hint: form.tone_hint,
      relationship_status: form.relationship_status,
      conversation_context: form.conversation_context,
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
      <p class="hero-text">直接贴消息、选人物和场景，系统会帮你理解、拟回复、预判下一句。</p>
    </div>
    <div class="hero-actions">
      <RouterLink class="secondary-btn" to="/">回首页</RouterLink>
    </div>
  </section>

  <section class="section-card reply-assistant-workbench">
    <div class="reply-assistant-layout">
      <div class="reply-assistant-column">
        <article class="wizard-stage">
          <div class="section-head">
            <div>
              <p class="eyebrow">输入区</p>
              <h3>对方发来的内容</h3>
            </div>
            <p class="section-note">可以直接贴单条消息，也可以把整段聊天一起放进来。</p>
          </div>

          <label class="form-field">
            <span>对方原话 / 聊天内容</span>
            <textarea
              v-model="form.message"
              class="field-input reply-assistant-textarea"
              rows="6"
              placeholder="把对方发来的原话贴在这里，支持多行聊天内容"
            ></textarea>
          </label>

          <label class="form-field">
            <span>补充上下文</span>
            <textarea
              v-model="form.current_context"
              class="field-input reply-assistant-textarea"
              rows="4"
              placeholder="比如：前面在聊什么、你们最近什么状态、这句话前后发生了什么"
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

          <div class="form-grid">
            <label class="form-field">
              <span>当前关系 / 状态</span>
              <textarea
                v-model="form.relationship_status"
                class="field-input reply-assistant-textarea"
                rows="4"
                placeholder="例如：暧昧期、合作中、冷战后、第一次沟通"
              ></textarea>
            </label>
            <label class="form-field">
              <span>你想达到什么目标</span>
              <textarea
                v-model="form.target_goal"
                class="field-input reply-assistant-textarea"
                rows="4"
                placeholder="例如：更自然、更正式、更有边界、更推进、更克制"
              ></textarea>
            </label>
          </div>

          <div class="form-grid">
            <label class="form-field">
              <span>语气要求</span>
              <textarea
                v-model="form.tone_hint"
                class="field-input reply-assistant-textarea"
                rows="4"
                placeholder="例如：自然、礼貌、体面、正式、简短"
              ></textarea>
            </label>
            <label class="form-field">
              <span>多轮聊天 / 额外上下文</span>
              <textarea
                v-model="form.conversation_context"
                class="field-input reply-assistant-textarea"
                rows="4"
                placeholder="把前后聊天一起贴进来，系统会一起看"
              ></textarea>
            </label>
          </div>

          <div class="quick-actions">
            <button
              v-for="item in toneQuickActions"
              :key="item.label"
              class="chip-btn"
              type="button"
              @click="applyTonePreset(item.value)"
            >
              {{ item.label }}
            </button>
          </div>

          <div class="quick-actions">
            <button
              v-for="item in goalQuickActions"
              :key="item.label"
              class="chip-btn"
              type="button"
              @click="applyGoalPreset(item.value)"
            >
              {{ item.label }}
            </button>
          </div>

          <MaterialInputPanel
            v-model="rawMaterials"
            path-type="relationship"
            :supports-guided-prompts="false"
          />

          <div class="hero-actions">
            <button class="primary-btn" type="button" :disabled="loading || !form.message.trim()" @click="generateReply">
              {{ loading ? '生成中…' : '生成回复建议' }}
            </button>
          </div>

          <div v-if="error" class="state-panel">
            <p class="eyebrow">生成失败</p>
            <h3>回复建议暂时生成失败</h3>
            <p class="state-copy">{{ error }}</p>
          </div>
        </article>
      </div>

      <div class="reply-assistant-column reply-assistant-column--output">
        <article class="summary-panel">
          <p class="eyebrow">输出区</p>
          <h3>对方这句话可能什么意思</h3>
          <p class="state-copy">
            {{ result?.understanding_result.meaning_guess || '先填上面内容，再生成理解结果。' }}
          </p>
          <ul class="summary-panel__list">
            <li><span>情绪</span><strong>{{ result?.understanding_result.emotion_guess || '未生成' }}</strong></li>
            <li><span>意图</span><strong>{{ result?.understanding_result.intent_guess || '未生成' }}</strong></li>
            <li><span>关系状态</span><strong>{{ result?.understanding_result.relationship_state_guess || '未生成' }}</strong></li>
            <li><span>场景判断</span><strong>{{ result?.understanding_result.scene_guess || '未生成' }}</strong></li>
          </ul>
        </article>

        <article class="summary-panel">
          <p class="eyebrow">推荐回复</p>
          <h3>我该怎么回</h3>
          <p class="state-copy">{{ result?.recommended_reply || '这里会显示一条最适合先发出去的建议。' }}</p>
        </article>

        <article class="summary-panel">
          <p class="eyebrow">候选回复</p>
          <div class="reply-candidate-list">
            <div v-for="item in result?.reply_candidates || []" :key="`${item.label}-${item.text}`" class="reply-candidate-card">
              <div class="reply-candidate-card__top">
                <strong>{{ item.label }}</strong>
                <span class="tag-chip">{{ item.style_tags.join(' / ') || '平衡' }}</span>
              </div>
              <p>{{ item.text }}</p>
              <small v-if="item.reason">{{ item.reason }}</small>
            </div>
          </div>
        </article>

        <article class="summary-panel">
          <p class="eyebrow">风险提示</p>
          <div class="tag-row">
            <span v-for="flag in result?.risk_flags || []" :key="flag" class="tag-chip">{{ flag }}</span>
            <span v-if="!(result?.risk_flags || []).length" class="tag-chip">生成后会显示风险提示</span>
          </div>
        </article>

        <article class="summary-panel">
          <p class="eyebrow">对方下一句可能怎么回</p>
          <div class="reply-candidate-list">
            <div v-for="item in result?.predicted_replies || []" :key="`${item.label}-${item.text}`" class="reply-candidate-card">
              <div class="reply-candidate-card__top">
                <strong>{{ item.label }}</strong>
                <span class="tag-chip">{{ item.risk_level || '中' }}</span>
              </div>
              <p>{{ item.text }}</p>
            </div>
          </div>
        </article>

        <article class="summary-panel">
          <p class="eyebrow">风格标签</p>
          <h3>{{ result?.tone_profile.label || '未生成' }}</h3>
          <p class="state-copy">{{ result?.tone_profile.guidance || '这里会显示语气风格建议。' }}</p>
          <div class="tag-row">
            <span v-for="tag in result?.tone_profile.style_tags || []" :key="tag" class="tag-chip">{{ tag }}</span>
          </div>
        </article>

        <article class="summary-panel">
          <p class="eyebrow">材料摘要</p>
          <p class="state-copy">{{ result?.material_summary || '文本文件、图片和 OCR 材料会在这里汇总。' }}</p>
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

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin: 0.5rem 0;
}

.reply-assistant-textarea {
  min-height: 110px;
}

.reply-candidate-list {
  display: grid;
  gap: 0.75rem;
}

.reply-candidate-card {
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 0.9rem 1rem;
  background: rgba(255, 255, 255, 0.76);
}

.reply-candidate-card__top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.45rem;
}

.reply-candidate-card p {
  margin: 0;
  line-height: 1.6;
}

.reply-candidate-card small {
  display: block;
  margin-top: 0.45rem;
  color: var(--muted);
}

@media (max-width: 980px) {
  .reply-assistant-layout {
    grid-template-columns: 1fr;
  }
}
</style>
