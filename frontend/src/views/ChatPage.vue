<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  clearChatSession,
  loadChatSession,
  loadLatestPersonaSession,
  sendChatMessage,
} from '@/services/chatService'
import { loadPersona, type Persona } from '@/services/personaService'
import { stripThinkBlocks } from '@/utils/sanitizeMessage'
import { renderMarkdown } from '@/utils/markdown'

type ChatMessage = {
  role: 'assistant' | 'user'
  content: string
}

const route = useRoute()
const persona = ref<Persona | null>(null)
const personaLoading = ref(true)
const personaError = ref('')
const personaMissing = ref(false)
const messages = ref<ChatMessage[]>([])
const messagesContainerRef = ref<HTMLElement | null>(null)
const draft = ref('')
const sending = ref(false)
const chatError = ref('')
const sessionId = ref('')

const personaId = computed(() => String(route.params.id || ''))
const sessionRouteId = computed(() => String(route.query.session_id || '').trim())
const conversationMessages = computed(() =>
  messages.value.filter((message) => message.role === 'user' || message.role === 'assistant'),
)
const shouldShowRecommendedQuestions = computed(() => conversationMessages.value.length === 0)

const sessionStorageKey = (slug: string) => `persona-chat-session:${slug}`
const sessionIndexKey = 'persona-chat-session-index'

const renderAssistantMessage = (content: string) => renderMarkdown(stripThinkBlocks(content || ''))

const scrollToBottom = async (behavior: ScrollBehavior = 'smooth') => {
  await nextTick()
  const el = messagesContainerRef.value
  if (!el) {
    return
  }

  el.scrollTo({
    top: el.scrollHeight,
    behavior,
  })
}

const readSessionIndex = (): Record<string, string> => {
  try {
    const raw = localStorage.getItem(sessionIndexKey)
    if (!raw) {
      return {}
    }
    const parsed = JSON.parse(raw) as Record<string, unknown>
    return Object.entries(parsed).reduce<Record<string, string>>((acc, [key, value]) => {
      if (typeof value === 'string' && value.trim()) {
        acc[key] = value
      }
      return acc
    }, {})
  } catch {
    return {}
  }
}

const writeSessionIndex = (value: Record<string, string>) => {
  localStorage.setItem(sessionIndexKey, JSON.stringify(value))
}

const resetConversation = () => {
  messages.value = []
  draft.value = ''
  chatError.value = ''
  sending.value = false
}

const setConversationMessages = async (nextMessages: ChatMessage[], behavior: ScrollBehavior = 'auto') => {
  messages.value = nextMessages
  await scrollToBottom(behavior)
}

const loadConversation = async (id: string) => {
  personaLoading.value = true
  personaError.value = ''
  personaMissing.value = false
  persona.value = null
  resetConversation()
  sessionId.value = ''

  try {
    const loaded = await loadPersona(id)
    if (!loaded) {
      personaMissing.value = true
      return
    }

    persona.value = loaded
    const routeSessionId = sessionRouteId.value
    const storedSessionId = sessionStorage.getItem(sessionStorageKey(loaded.slug)) || ''
    const sessionIndex = readSessionIndex()
    sessionId.value = routeSessionId || storedSessionId || sessionIndex[loaded.slug] || ''

    if (!sessionId.value) {
      const latestSession = await loadLatestPersonaSession(loaded.slug)
      if (latestSession) {
        rememberSession(loaded.slug, latestSession.session_id)
        await setConversationMessages(
          latestSession.messages.map((message) => ({
            role: message.role,
            content: stripThinkBlocks(message.content || ''),
          })),
          'auto',
        )
        return
      }
    }

    if (sessionId.value) {
      const session = await loadChatSession(sessionId.value)
      if (session && session.persona_slug === loaded.slug) {
        rememberSession(loaded.slug, session.session_id)
        await setConversationMessages(
          session.messages.map((message) => ({
            role: message.role,
            content: stripThinkBlocks(message.content || ''),
          })),
          'auto',
        )
        return
      }
      rememberSession(loaded.slug, '')
    }

    const latestSession = await loadLatestPersonaSession(loaded.slug)
    if (latestSession) {
      rememberSession(loaded.slug, latestSession.session_id)
      await setConversationMessages(
        latestSession.messages.map((message) => ({
          role: message.role,
          content: stripThinkBlocks(message.content || ''),
        })),
        'auto',
      )
    }
  } catch (error) {
    personaError.value = error instanceof Error ? error.message : '加载人格详情失败'
  } finally {
    personaLoading.value = false
  }
}

onMounted(() => {
  void loadConversation(personaId.value)
})

watch([personaId, sessionRouteId], ([id]) => {
  void loadConversation(id)
})

const rememberSession = (slug: string, value: string) => {
  sessionId.value = value
  const sessionIndex = readSessionIndex()
  if (value) {
    sessionStorage.setItem(sessionStorageKey(slug), value)
    sessionIndex[slug] = value
  } else {
    sessionStorage.removeItem(sessionStorageKey(slug))
    delete sessionIndex[slug]
  }
  writeSessionIndex(sessionIndex)
}

const sendMessage = async (preset?: string) => {
  const text = (preset ?? draft.value).trim()
  if (!persona.value || !text || sending.value) {
    return
  }

  if (!preset) {
    draft.value = ''
  }

  chatError.value = ''
  messages.value.push({ role: 'user', content: text })
  sending.value = true

  await scrollToBottom('smooth')

  try {
    const result = await sendChatMessage({
      personaSlug: persona.value.slug,
      sessionId: sessionId.value || null,
      message: text,
    })
    rememberSession(persona.value.slug, result.session_id)
    messages.value.push({ role: 'assistant', content: stripThinkBlocks(result.reply || '') })
    await scrollToBottom('smooth')
  } catch (error) {
    chatError.value = error instanceof Error ? error.message : '当前模型服务不可用，请稍后再试。'
  } finally {
    sending.value = false
  }
}

const clearConversation = async () => {
  if (!persona.value || sending.value) {
    return
  }

  chatError.value = ''

  if (sessionId.value) {
    try {
      const cleared = await clearChatSession(sessionId.value)
      rememberSession(persona.value.slug, cleared.session_id)
    } catch (error) {
      chatError.value = error instanceof Error ? error.message : '清空上下文失败，请稍后再试。'
      return
    }
  }

  messages.value = []
  draft.value = ''
}
</script>

<template>
  <section v-if="personaLoading" class="empty-state">
    <div class="section-card">
      <p class="eyebrow">加载中</p>
      <h2>正在读取人格与聊天配置…</h2>
    </div>
  </section>

  <section v-else-if="personaError" class="empty-state">
    <div class="section-card">
      <p class="eyebrow">加载失败</p>
      <h2>人格信息暂时不可用</h2>
      <p class="state-copy">{{ personaError }}</p>
      <RouterLink class="primary-btn" to="/">返回首页</RouterLink>
    </div>
  </section>

  <section v-else-if="personaMissing || !persona" class="empty-state">
    <div class="section-card">
      <p class="eyebrow">未找到</p>
      <h2>没有找到这个人格。</h2>
      <p class="state-copy">请确认链接是否存在。</p>
      <RouterLink class="primary-btn" to="/">返回首页</RouterLink>
    </div>
  </section>

  <section v-else class="chat-layout">
    <article class="chat-panel">
      <div class="chat-head">
        <div>
          <p class="eyebrow">正在对话</p>
          <h2>{{ persona.name }}</h2>
        </div>
        <button class="ghost-btn" type="button" :disabled="sending" @click="clearConversation">
          清空上下文
        </button>
      </div>

      <p v-if="chatError" class="state-copy" style="color: #c85d4c;">
        {{ chatError }}
      </p>

      <div ref="messagesContainerRef" class="chat-feed">
        <div v-if="!messages.length && !sending" class="mini-panel">
          <p class="side-title">还没有开始聊天</p>
          <p>你可以先点一个推荐问题，或者直接输入自己的问题。</p>
        </div>

        <div v-for="(message, index) in messages" :key="index" class="message-row" :class="message.role">
          <div class="message-bubble">
            <span class="message-role">{{ message.role === 'assistant' ? persona.name : '你' }}</span>
            <div
              v-if="message.role === 'assistant'"
              class="message-markdown"
              v-html="renderAssistantMessage(message.content)"
            />
            <p v-else>{{ message.content }}</p>
          </div>
        </div>

        <div v-if="sending" class="message-row assistant">
          <div class="message-bubble">正在整理回答…</div>
        </div>
      </div>

      <div v-if="shouldShowRecommendedQuestions" class="quick-questions">
        <button
          v-for="question in persona.recommendedQuestions.slice(0, 3)"
          :key="question"
          class="chip-btn"
          type="button"
          @click="sendMessage(question)"
        >
          {{ question }}
        </button>
      </div>

      <form class="chat-composer" @submit.prevent="sendMessage()">
        <textarea
          v-model="draft"
          rows="3"
          placeholder="把你的问题写在这里，先从最现实的那一层开始聊。"
        ></textarea>
        <div class="composer-actions">
          <RouterLink class="secondary-btn" :to="`/character/${persona.id}`">返回详情</RouterLink>
          <button class="primary-btn" type="submit" :disabled="sending">发送</button>
        </div>
      </form>
    </article>

    <aside class="chat-side">
      <div class="mini-panel">
        <p class="eyebrow">当前人格</p>
        <p class="side-title">{{ persona.category }}</p>
        <p>{{ persona.profile }}</p>
      </div>
      <div v-if="shouldShowRecommendedQuestions" class="mini-panel">
        <p class="eyebrow">适合提问</p>
        <ul class="question-list">
          <li v-for="question in persona.recommendedQuestions" :key="question">{{ question }}</li>
        </ul>
      </div>
    </aside>
  </section>
</template>
