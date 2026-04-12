<template>
  <MainLayout title="一键部署" subtitle="快速部署您的 AI 应用">
    <!-- No keys available state -->
    <div v-if="keyStore.keys.length === 0" class="install-empty card">
      <div class="install-empty-icon">🚀</div>
      <h3>暂无可部署的 API Key</h3>
      <p>请先创建并分配 <strong>Anthropic</strong> 或 <strong>Antigravity</strong> 分组的 API Key</p>
      <button class="btn btn-primary mt-4" @click="$router.push('/main/keys')">前往创建 API Key</button>
    </div>

    <!-- Keys available - show deploy options -->
    <div v-else>
      <!-- Key selector -->
      <div class="key-selector-section card" style="margin-bottom: 24px;">
        <h3 class="section-h3">选择要部署的 API Key</h3>
        <div class="key-chips">
          <button
            v-for="k in keyStore.keys"
            :key="k.id"
            class="key-chip"
            :class="{ active: selectedKeyId === k.id }"
            @click="selectedKeyId = k.id"
          >
            <span class="key-chip-icon">🔑</span>
            <span>{{ k.name }}</span>
            <span class="badge badge-primary key-chip-group">{{ k.group_name }}</span>
          </button>
        </div>
      </div>

      <!-- Deploy type tabs -->
      <div class="deploy-section card">
        <h3 class="section-h3">选择部署客户端</h3>
        <BaseTabs v-model:modelValue="activeTab" :tabs="tabOptions" />
        <div class="command-block">
          <div class="command-header">
            <span class="command-label">{{ activeTabLabel }} 环境变量</span>
            <CopyButton :text="currentCommand" label="复制命令" @click="handleCopy" />
          </div>
          <pre class="command-code">{{ currentCommand }}</pre>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import MainLayout from '@/components/main/MainLayout.vue'
import BaseTabs from '@/components/common/BaseTabs.vue'
import CopyButton from '@/components/common/CopyButton.vue'
import { useKeyStore } from '@/stores/keys'
import { useFeedbackStore } from '@/stores/feedback'
import { installService } from '@/services/installService'
import { storage } from '@/utils/storage'

const keyStore = useKeyStore()
const feedback = useFeedbackStore()

// Persist selectedKeyId and activeTab to localStorage
const savedKeyIdRaw = storage.get<number | string | null>('clientinstall_keyid', null)
const savedKeyId = typeof savedKeyIdRaw === 'number' ? savedKeyIdRaw : null
const savedTab = storage.get<string>('clientinstall_tab', 'claude-code')

const selectedKeyId = ref<number | null>(savedKeyId)
const activeTab = ref(savedTab)

const tabOptions = [
  { label: 'Claude Code', value: 'claude-code' },
  { label: 'OpenClaw', value: 'openclaw' },
]

const activeTabLabel = computed(() =>
  tabOptions.find(t => t.value === activeTab.value)?.label || ''
)

const currentCommand = computed(() => {
  const keyId = selectedKeyId.value ?? (keyStore.keys[0]?.id ?? 0)
  return installService.buildCommand(activeTab.value as any, String(keyId))
})

// Auto-select first key if none selected
onMounted(async () => {
  if (keyStore.keys.length === 0) {
    await keyStore.fetchKeys()
  }
  if (!selectedKeyId.value && keyStore.keys.length > 0) {
    selectedKeyId.value = keyStore.keys[0].id
  }
})

// Watch for key changes: if selected key was deleted, fall back to first available
watch(() => keyStore.keys, (keys) => {
  if (selectedKeyId.value != null && !keys.find((k: any) => k.id === selectedKeyId.value)) {
    selectedKeyId.value = keys[0]?.id ?? null
  }
}, { deep: true })

// Persist selections
watch(selectedKeyId, (v) => { storage.set('clientinstall_keyid', v) })
watch(activeTab, (v) => { storage.set('clientinstall_tab', v) })

const handleCopy = () => {
  navigator.clipboard.writeText(currentCommand.value)
  feedback.success('命令已复制到剪贴板')
}
</script>

<style scoped>
.install-empty {
  text-align: center;
  padding: 64px 40px;
}
.install-empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.6; }
.install-empty h3 { font-size: 18px; font-weight: 700; color: var(--color-text); margin-bottom: 12px; }
.install-empty p { font-size: 14px; color: var(--color-text-secondary); max-width: 400px; margin: 0 auto; line-height: 1.7; }

.section-h3 { font-size: 16px; font-weight: 700; margin-bottom: 16px; color: var(--color-text); }

.key-selector-section { margin-bottom: 24px; }
.key-chips { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; }
.key-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  white-space: nowrap;
  flex-shrink: 0;
  height: 36px;
}
.key-chip:hover { border-color: var(--color-primary); }
.key-chip.active { border-color: var(--color-primary); background: rgba(79,70,229,.04); }
.key-chip-icon { font-size: 16px; }
.key-chip-group { margin-left: auto; }

.deploy-section { margin-bottom: 24px; }

.command-block {
  margin-top: 24px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.command-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
}
.command-label { font-size: 13px; font-weight: 600; color: var(--color-text-secondary); }
.command-code {
  padding: 20px;
  background: #1F2937;
  color: #E5E7EB;
  font-family: monospace;
  font-size: 13px;
  line-height: 1.7;
  overflow-x: auto;
  white-space: pre;
  margin: 0;
}
</style>
