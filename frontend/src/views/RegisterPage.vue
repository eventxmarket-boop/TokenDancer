<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { registerWithAuth } from '@/stores/auth'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const error = ref('')
const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const redirectTarget = computed(() => {
  const raw = String(route.query.redirect || '').trim()
  return raw || '/me'
})

async function submit() {
  if (loading.value) {
    return
  }

  const username = form.username.trim()
  const email = form.email.trim()
  const password = form.password.trim()
  const confirmPassword = form.confirmPassword.trim()

  if (!username || !email || !password || !confirmPassword) {
    error.value = '请完整填写注册信息'
    return
  }

  if (password !== confirmPassword) {
    error.value = '两次密码不一致'
    return
  }

  loading.value = true
  error.value = ''

  try {
    await registerWithAuth({
      username,
      email,
      password,
    })
    await router.replace(redirectTarget.value)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="auth-page">
    <div class="section-card auth-card">
      <div class="auth-card__head">
        <p class="eyebrow">注册</p>
        <h1>创建账号</h1>
        <p class="hero-text">注册后会自动登录，并保留你的 Seed 与会话。</p>
      </div>

      <form class="auth-form" @submit.prevent="submit">
        <label class="form-field">
          <span>用户名</span>
          <input v-model="form.username" class="field-input" type="text" placeholder="输入用户名" />
        </label>

        <label class="form-field">
          <span>邮箱</span>
          <input v-model="form.email" class="field-input" type="email" placeholder="输入邮箱" />
        </label>

        <label class="form-field">
          <span>密码</span>
          <input v-model="form.password" class="field-input" type="password" placeholder="输入密码" />
        </label>

        <label class="form-field">
          <span>确认密码</span>
          <input v-model="form.confirmPassword" class="field-input" type="password" placeholder="再次输入密码" />
        </label>

        <p v-if="error" class="state-copy">{{ error }}</p>

        <div class="auth-actions">
          <button class="primary-btn" type="submit" :disabled="loading">
            {{ loading ? '注册中…' : '注册' }}
          </button>
          <RouterLink class="secondary-btn" :to="{ path: '/login', query: route.query }">去登录</RouterLink>
        </div>
      </form>
    </div>
  </section>
</template>
