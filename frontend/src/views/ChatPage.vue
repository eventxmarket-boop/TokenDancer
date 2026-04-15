<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { buildMockReply, loadPersona, type Persona } from '@/services/personaService'

type ChatMessage = {
  role: 'assistant' | 'user'
  content: string
}

const route = useRoute()
const persona = ref<Persona | null>(null)
const messages = ref<ChatMessage[]>([])
const draft = ref('')
const sending = ref(false)

const personaId = computed(() => String(route.params.id || ''))

const loadConversation = async (id: string) => {
  persona.value = await loadPersona(id)
  messages.value = persona.value
    ? [{ role: 'assistant', content: `你好，我是 ${persona.value.name}。可以直接问我你最在意的问题。` }]
    : []
}

onMounted(() => {
  void loadConversation(personaId.value)
})

watch(personaId, (id) => {
  void loadConversation(id)
})

const sendMessage = async (preset?: string) => {
  const text = (preset ?? draft.value).trim()
  if (!persona.value || !text || sending.value) {
    return
  }

  if (!preset) {
    draft.value = ''
  }

  messages.value.push({ role: 'user', content: text })
  sending.value = true
  await nextTick()

  window.setTimeout(() => {
    messages.value.push({
      role: 'assistant',
      content: buildMockReply(persona.value as Persona, text),
    })
    sending.value = false
  }, 320)
}

const clearConversation = () => {
  if (!persona.value) {
    return
  }
  messages.value = [{ role: 'assistant', content: `你好，我是 ${persona.value.name}。可以直接问我你最在意的问题。` }]
  draft.value = ''
}
</script>

<template>
  <section v-if="persona" class="chat-layout">
    <article class="chat-panel">
      <div class="chat-head">
        <div>
          <p class="eyebrow">正在对话</p>
          <h2>{{ persona.name }}</h2>
        </div>
        <button class="ghost-btn" type="button" @click="clearConversation">清空上下文</button>
      </div>

      <div class="chat-feed">
        <div v-for="(message, index) in messages" :key="index" class="message-row" :class="message.role">
          <div class="message-bubble">
            <span class="message-role">{{ message.role === 'assistant' ? persona.name : '你' }}</span>
            <p>{{ message.content }}</p>
          </div>
        </div>
        <div v-if="sending" class="message-row assistant">
          <div class="message-bubble">正在整理回答…</div>
        </div>
      </div>

      <div class="quick-questions">
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
          <button class="primary-btn" type="submit">发送</button>
        </div>
      </form>
    </article>

    <aside class="chat-side">
      <div class="mini-panel">
        <p class="eyebrow">当前人格</p>
        <p class="side-title">{{ persona.category }}</p>
        <p>{{ persona.profile }}</p>
      </div>
      <div class="mini-panel">
        <p class="eyebrow">适合提问</p>
        <ul class="question-list">
          <li v-for="question in persona.recommendedQuestions" :key="question">{{ question }}</li>
        </ul>
      </div>
    </aside>
  </section>

  <section v-else class="empty-state">
    <h2>没有找到这个人格。</h2>
    <RouterLink class="primary-btn" to="/">返回首页</RouterLink>
  </section>
</template>
