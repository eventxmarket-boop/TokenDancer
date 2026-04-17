<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import {
  type FamilyCompanionOCRExtractedText,
  type TextMaterialDocument,
  type UniversalCreateWizardRawMaterials,
  type UploadedImageDocument,
} from '@/services/createWizardService'

type MaterialPathType = 'family' | 'reunion' | 'intimate' | 'self' | 'source' | 'relationship'

const props = withDefaults(
  defineProps<{
    modelValue?: UniversalCreateWizardRawMaterials | Record<string, unknown>
    supportsGuidedPrompts?: boolean
    pathType: MaterialPathType
    subtype?: string
  }>(),
  {
    modelValue: () => ({}),
    supportsGuidedPrompts: false,
    subtype: '',
  },
)

const emit = defineEmits<{
  (event: 'update:modelValue', value: UniversalCreateWizardRawMaterials): void
}>()

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

function normalizeText(value: unknown) {
  return String(value || '').trim()
}

function normalizeState(value: unknown): UniversalCreateWizardRawMaterials {
  const fallback = createEmptyMaterialState()
  if (!value || typeof value !== 'object') {
    return fallback
  }
  const record = value as Record<string, unknown>
  const uploadedTextDocuments = Array.isArray(record.uploaded_text_documents)
    ? record.uploaded_text_documents
        .map((item) => {
          if (!item || typeof item !== 'object') return null
          const doc = item as Record<string, unknown>
          const filename = normalizeText(doc.filename || doc.name)
          const content = normalizeText(doc.content || doc.text || doc.body)
          return filename || content ? { filename, content } : null
        })
        .filter(Boolean)
    : []
  const uploadedImageDocuments = Array.isArray(record.uploaded_image_documents)
    ? record.uploaded_image_documents
        .map((item) => {
          if (!item || typeof item !== 'object') return null
          const doc = item as Record<string, unknown>
          const filename = normalizeText(doc.filename || doc.name)
          const mime_type = normalizeText(doc.mime_type || doc.type) || 'image/*'
          const size = Number(doc.size || 0)
          const data_url = normalizeText(doc.data_url || doc.preview_url || doc.url)
          const ocr_status = normalizeText(doc.ocr_status || doc.status) || '待识别'
          const ocr_text = normalizeText(doc.ocr_text || doc.text || doc.content)
          return filename || data_url || size
            ? { filename, mime_type, size: Number.isFinite(size) ? size : 0, data_url, ocr_status, ocr_text }
            : null
        })
        .filter(Boolean)
    : []
  const ocrExtractedTexts = Array.isArray(record.ocr_extracted_texts)
    ? record.ocr_extracted_texts
        .map((item) => {
          if (!item || typeof item !== 'object') return null
          const doc = item as Record<string, unknown>
          const filename = normalizeText(doc.filename || doc.name)
          const mime_type = normalizeText(doc.mime_type || doc.type) || 'image/*'
          const size = Number(doc.size || 0)
          const text = normalizeText(doc.ocr_text || doc.text || doc.content)
          const status = normalizeText(doc.ocr_status || doc.status) || (text ? 'success' : 'failed')
          return filename || text || size
            ? { filename, mime_type, size: Number.isFinite(size) ? size : 0, ocr_text: text, ocr_status: status }
            : null
        })
        .filter(Boolean)
    : []

  return {
    chat_history_text: normalizeText(record.chat_history_text),
    memory_notes_text: normalizeText(record.memory_notes_text),
    text_materials_text: normalizeText(record.text_materials_text),
    uploaded_text_documents: uploadedTextDocuments as TextMaterialDocument[],
    uploaded_image_documents: uploadedImageDocuments as UploadedImageDocument[],
    ocr_extracted_texts: ocrExtractedTexts as FamilyCompanionOCRExtractedText[],
    image_notes_text: normalizeText(record.image_notes_text),
    photo_notes_text: normalizeText(record.photo_notes_text),
    voice_notes_text: normalizeText(record.voice_notes_text),
    diary_text: normalizeText(record.diary_text),
    letter_text: normalizeText(record.letter_text),
    conflict_text: normalizeText(record.conflict_text),
    draft_message_text: normalizeText(record.draft_message_text),
    recent_context_text: normalizeText(record.recent_context_text),
    reply_style_samples_text: normalizeText(record.reply_style_samples_text),
    relationship_status_text: normalizeText(record.relationship_status_text),
    interaction_patterns_text: normalizeText(record.interaction_patterns_text),
    history_text: normalizeText(record.history_text),
    expression_samples_text: normalizeText(record.expression_samples_text),
  }
}

const localValue = reactive<UniversalCreateWizardRawMaterials>(createEmptyMaterialState())

watch(
  () => props.modelValue,
  (next) => {
    Object.assign(localValue, normalizeState(next))
  },
  { deep: true, immediate: true },
)

watch(
  localValue,
  () => {
    emit('update:modelValue', normalizeState(localValue))
  },
  { deep: true },
)

function normalizeFileText(file: File) {
  return file.name
}

function isTextFile(file: File) {
  if (file.type && (file.type === 'text/plain' || file.type === 'text/markdown' || file.type === 'text/csv')) {
    return true
  }
  return /\.(txt|md|csv)$/i.test(file.name)
}

function isImageFile(file: File) {
  if (file.type && file.type.startsWith('image/')) {
    return true
  }
  return /\.(jpg|jpeg|png|webp)$/i.test(file.name)
}

function guessImageMimeType(file: File) {
  if (file.type && file.type.startsWith('image/')) {
    return file.type
  }
  if (/\.jpe?g$/i.test(file.name)) {
    return 'image/jpeg'
  }
  if (/\.png$/i.test(file.name)) {
    return 'image/png'
  }
  if (/\.webp$/i.test(file.name)) {
    return 'image/webp'
  }
  return 'image/*'
}

function formatFileSize(size: number) {
  if (!Number.isFinite(size) || size <= 0) {
    return '0 KB'
  }
  if (size < 1024) {
    return `${size} B`
  }
  if (size < 1024 * 1024) {
    return `${Math.max(Math.round(size / 1024), 1)} KB`
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

async function readFileAsText(file: File) {
  return await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error(`读取文件失败：${file.name}`))
    reader.readAsText(file)
  })
}

async function readFileAsDataUrl(file: File) {
  return await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error(`读取图片失败：${file.name}`))
    reader.readAsDataURL(file)
  })
}

async function handleTextDocumentChange(event: Event) {
  const target = event.target as HTMLInputElement | null
  const files = Array.from(target?.files || []).filter(isTextFile)
  if (!files.length) {
    if (target) target.value = ''
    return
  }

  const documents = await Promise.all(
    files.map(async (file) => {
      const content = normalizeText(await readFileAsText(file))
      return content ? { filename: normalizeFileText(file), content } : null
    }),
  )

  const validDocuments = documents.filter(Boolean) as TextMaterialDocument[]
  localValue.uploaded_text_documents = [...localValue.uploaded_text_documents, ...validDocuments]
  const appended = validDocuments.map((item) => item.content).filter(Boolean).join('\n')
  if (appended) {
    localValue.text_materials_text = [localValue.text_materials_text, appended].filter(Boolean).join('\n')
    localValue.memory_notes_text = [localValue.memory_notes_text, appended].filter(Boolean).join('\n')
  }
  if (target) target.value = ''
}

async function handleImageDocumentChange(event: Event) {
  const target = event.target as HTMLInputElement | null
  const files = Array.from(target?.files || []).filter(isImageFile)
  if (!files.length) {
    if (target) target.value = ''
    return
  }

  const documents = await Promise.all(
    files.map(async (file) => ({
      filename: file.name,
      mime_type: guessImageMimeType(file),
      size: file.size,
      data_url: await readFileAsDataUrl(file),
      ocr_status: '待识别',
      ocr_text: '',
    })),
  )

  localValue.uploaded_image_documents = [...localValue.uploaded_image_documents, ...documents]
  if (target) target.value = ''
}

function removeTextDocument(index: number) {
  localValue.uploaded_text_documents = localValue.uploaded_text_documents.filter((_, itemIndex) => itemIndex !== index)
}

function removeImageDocument(index: number) {
  localValue.uploaded_image_documents = localValue.uploaded_image_documents.filter((_, itemIndex) => itemIndex !== index)
}

const hasGuidedPromptHint = computed(() => props.supportsGuidedPrompts)
const pathLabel = computed(() => {
  if (props.pathType === 'family') {
    return props.subtype ? `家人陪伴 · ${props.subtype}` : '家人陪伴'
  }
  if (props.pathType === 'reunion') {
    return '重逢人格'
  }
  if (props.pathType === 'intimate') {
    return '亲密关系'
  }
  if (props.pathType === 'self') {
    return '我的人格'
  }
  if (props.pathType === 'source') {
    return '从资料创建'
  }
  if (props.pathType === 'relationship') {
    return '关系人格'
  }
  return '创建材料'
})

const imageUploadedLabel = computed(() => {
  const count = localValue.uploaded_image_documents.length
  if (!count) {
    return '未上传'
  }
  return `${count} 张：${localValue.uploaded_image_documents.map((item) => item.filename).join(' / ')}`
})

const textUploadedLabel = computed(() => {
  const count = localValue.uploaded_text_documents.length
  if (!count) {
    return '未上传'
  }
  return `${count} 个文件：${localValue.uploaded_text_documents.map((item) => item.filename).join(' / ')}`
})

const ocrStatusLabel = computed(() => {
  const items = localValue.uploaded_image_documents
  if (!items.length) {
    return '未识别'
  }
  const successCount = items.filter((item) => ['success', 'partial'].includes(normalizeText(item.ocr_status)) && normalizeText(item.ocr_text)).length
  const failedCount = items.length - successCount
  return `${successCount} 成功 / ${failedCount} 待识别`
})
</script>

<template>
  <section class="material-input-panel">
    <div class="section-head">
      <div>
        <h3>{{ pathLabel }}</h3>
      </div>
    </div>

    <div class="material-input-grid">
      <label class="form-field">
        <span>聊天记录粘贴</span>
        <textarea
          v-model="localValue.chat_history_text"
          class="field-input wizard-textarea"
          rows="5"
          placeholder="贴聊天记录"
        ></textarea>
      </label>

      <label class="form-field">
        <span>记忆笔记 / 回忆片段</span>
        <textarea
          v-model="localValue.memory_notes_text"
          class="field-input wizard-textarea"
          rows="5"
          placeholder="贴记忆片段"
        ></textarea>
      </label>

      <label class="form-field">
        <span>文本材料</span>
        <textarea
          v-model="localValue.text_materials_text"
          class="field-input wizard-textarea"
          rows="5"
          placeholder="贴文本材料"
        ></textarea>
      </label>

      <label class="form-field">
        <span>上传 txt / md / csv</span>
        <input class="field-input" type="file" accept=".txt,.md,.csv,text/plain,text/markdown,text/csv" multiple @change="handleTextDocumentChange" />
        <small class="field-hint">{{ textUploadedLabel }}</small>
      </label>

      <label class="form-field">
        <span>图片上传</span>
        <input
          class="field-input"
          type="file"
          accept="image/*,.jpg,.jpeg,.png,.webp"
          capture="environment"
          multiple
          @change="handleImageDocumentChange"
        />
        <small class="field-hint">{{ imageUploadedLabel }}</small>
      </label>

      <label class="form-field">
        <span>图片说明</span>
        <textarea
          v-model="localValue.image_notes_text"
          class="field-input wizard-textarea"
          rows="4"
          placeholder="补图片说明"
        ></textarea>
      </label>

      <label class="form-field">
        <span>语音说明</span>
        <textarea
          v-model="localValue.voice_notes_text"
          class="field-input wizard-textarea"
          rows="4"
          placeholder="补语音说明"
        ></textarea>
      </label>
    </div>

    <div v-if="hasGuidedPromptHint" class="summary-panel summary-panel--compact material-input-panel__prompt">
      <h3>可继续补</h3>
    </div>

    <div class="material-input-panel__lists">
      <div v-if="localValue.uploaded_text_documents.length" class="summary-panel summary-panel--compact">
        <h3>文本文件</h3>
        <ul class="summary-panel__list">
          <li v-for="(item, index) in localValue.uploaded_text_documents" :key="`${item.filename}-${index}`">
            <span>
              {{ item.filename }}
              <small class="inline-meta">{{ Math.max(item.content.length, 1) }} 字</small>
            </span>
            <strong class="inline-actions">
              <button class="ghost-button ghost-button--small" type="button" @click="removeTextDocument(index)">
                删除
              </button>
            </strong>
          </li>
        </ul>
      </div>

      <div v-if="localValue.uploaded_image_documents.length" class="summary-panel summary-panel--compact">
        <h3>图片</h3>
        <p class="state-copy">{{ ocrStatusLabel }}</p>
        <ul class="summary-panel__list">
          <li v-for="(item, index) in localValue.uploaded_image_documents" :key="`${item.filename}-${index}`">
            <span>
              {{ item.filename }}
              <small class="inline-meta">
                {{ item.mime_type }} · {{ formatFileSize(item.size) }} · {{ item.ocr_status || '待识别' }}
              </small>
            </span>
            <strong class="inline-actions">
              <button class="ghost-button ghost-button--small" type="button" @click="removeImageDocument(index)">
                删除
              </button>
            </strong>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<style scoped>
.material-input-panel {
  display: grid;
  gap: 1rem;
}

.material-input-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.material-input-panel__prompt,
.material-input-panel__lists {
  margin-top: 0.25rem;
}

@media (max-width: 720px) {
  .material-input-grid {
    grid-template-columns: 1fr;
  }
}
</style>
