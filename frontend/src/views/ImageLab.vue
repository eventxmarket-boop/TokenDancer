<script setup lang="ts">
import { computed, ref } from 'vue'
import { generateImageLabImage, type ImageLabGenerateResponse } from '@/services/imageLabService'

const prompt = ref('')
const size = ref<'1024x1024' | '1024x1536' | '1536x1024' | 'auto'>('1024x1024')
const quality = ref<'low' | 'medium' | 'high' | 'auto'>('medium')
const outputFormat = ref<'png' | 'webp' | 'jpeg'>('png')
const loading = ref(false)
const errorMessage = ref('')
const result = ref<ImageLabGenerateResponse | null>(null)

const canSubmit = computed(() => prompt.value.trim().length >= 3 && prompt.value.trim().length <= 4000)
const imageSrc = computed(() => {
  if (!result.value) return ''
  return `data:${result.value.mime_type};base64,${result.value.image_base64}`
})
const downloadName = computed(() => `image-lab-${Date.now()}.${result.value?.output_format || outputFormat.value}`)

async function submit() {
  if (!canSubmit.value || loading.value) {
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    result.value = await generateImageLabImage({
      prompt: prompt.value.trim(),
      size: size.value,
      quality: quality.value,
      output_format: outputFormat.value,
    })
  } catch (cause) {
    errorMessage.value = cause instanceof Error ? cause.message : '图片生成失败，请稍后重试。'
    result.value = null
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="image-lab-page">
    <div class="image-lab-shell">
      <article class="section-card image-lab-panel">
        <div class="section-head">
          <div>
            <p class="eyebrow">内部测试</p>
            <h3>Image Lab</h3>
            <p class="section-note">输入提示词后由后端调用 OpenAI Image API，返回 base64 图片，仅用于内部科研试用。</p>
          </div>
        </div>

        <label class="image-lab-field">
          <span>提示词</span>
          <textarea
            v-model="prompt"
            class="image-lab-textarea"
            rows="8"
            maxlength="4000"
            placeholder="输入要生成的图片描述，尽量具体一些。"
          />
          <small>最少 3 个字符，最多 4000 个字符。</small>
        </label>

        <div class="image-lab-grid">
          <label class="image-lab-field">
            <span>尺寸</span>
            <select v-model="size">
              <option value="1024x1024">1024x1024</option>
              <option value="1024x1536">1024x1536</option>
              <option value="1536x1024">1536x1024</option>
              <option value="auto">auto</option>
            </select>
          </label>

          <label class="image-lab-field">
            <span>质量</span>
            <select v-model="quality">
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="auto">auto</option>
            </select>
          </label>

          <label class="image-lab-field">
            <span>格式</span>
            <select v-model="outputFormat">
              <option value="png">png</option>
              <option value="webp">webp</option>
              <option value="jpeg">jpeg</option>
            </select>
          </label>
        </div>

        <div class="image-lab-actions">
          <button class="primary-btn" type="button" :disabled="loading || !canSubmit" @click="submit">
            {{ loading ? '生成中...' : '生成图片' }}
          </button>
        </div>

        <p v-if="errorMessage" class="image-lab-error">{{ errorMessage }}</p>
      </article>

      <article class="section-card image-lab-preview">
        <div class="section-head">
          <div>
            <p class="eyebrow">输出</p>
            <h3>结果预览</h3>
          </div>
        </div>

        <div v-if="loading" class="image-lab-empty">正在生成，请稍候…</div>
        <div v-else-if="!result" class="image-lab-empty">生成结果会显示在这里。</div>
        <template v-else>
          <div class="image-lab-meta">
            <span>Model {{ result.model }}</span>
            <span>Size {{ result.size }}</span>
            <span>Quality {{ result.quality }}</span>
            <span>Format {{ result.output_format }}</span>
          </div>

          <div class="image-lab-canvas">
            <img :src="imageSrc" alt="generated image" class="image-lab-image" />
          </div>

          <a class="secondary-btn image-lab-download" :href="imageSrc" :download="downloadName">下载图片</a>
        </template>
      </article>
    </div>
  </section>
</template>

<style scoped>
.image-lab-page {
  width: 100%;
}

.image-lab-shell {
  display: grid;
  grid-template-columns: minmax(320px, 460px) minmax(0, 1fr);
  gap: 18px;
}

.image-lab-panel,
.image-lab-preview {
  min-height: 640px;
}

.image-lab-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 14px;
}

.image-lab-field > span {
  font-size: 0.92rem;
  color: var(--muted);
}

.image-lab-field small {
  color: var(--muted);
  font-size: 0.82rem;
}

.image-lab-textarea,
.image-lab-field select {
  width: 100%;
  border: 1px solid var(--line);
  background: var(--panel-solid);
  color: var(--text);
  border-radius: 18px;
  padding: 14px 16px;
  line-height: 1.55;
  box-shadow: none;
}

.image-lab-textarea {
  min-height: 180px;
  resize: vertical;
}

.image-lab-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.image-lab-actions {
  margin-top: 18px;
}

.image-lab-error {
  margin-top: 14px;
  color: #d54b39;
  line-height: 1.6;
}

.image-lab-preview {
  display: flex;
  flex-direction: column;
}

.image-lab-empty {
  flex: 1;
  display: grid;
  place-items: center;
  color: var(--muted);
  border: 1px dashed var(--line);
  border-radius: 24px;
  min-height: 520px;
  text-align: center;
  padding: 24px;
}

.image-lab-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
}

.image-lab-meta span {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--text);
  font-size: 0.86rem;
}

.image-lab-canvas {
  flex: 1;
  display: grid;
  place-items: center;
  padding: 12px;
  border-radius: 24px;
  border: 1px solid var(--line);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.38), rgba(255, 255, 255, 0.12));
  min-height: 520px;
}

.image-lab-image {
  max-width: 100%;
  max-height: 70vh;
  border-radius: 18px;
  object-fit: contain;
}

.image-lab-download {
  margin-top: 16px;
  align-self: flex-start;
}

@media (max-width: 980px) {
  .image-lab-shell {
    grid-template-columns: 1fr;
  }

  .image-lab-panel,
  .image-lab-preview {
    min-height: auto;
  }

  .image-lab-grid {
    grid-template-columns: 1fr;
  }

  .image-lab-empty,
  .image-lab-canvas {
    min-height: 320px;
  }
}
</style>
