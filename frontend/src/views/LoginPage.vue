<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { loginWithAuth } from '@/stores/auth'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const error = ref('')
const form = reactive({
  username_or_email: '',
  password: '',
})

const redirectTarget = computed(() => {
  const raw = String(route.query.redirect || '').trim()
  return raw || '/me'
})

async function submit() {
  if (loading.value) {
    return
  }

  const identity = form.username_or_email.trim()
  const password = form.password.trim()
  if (!identity || !password) {
    error.value = '请输入用户名/邮箱和密码'
    return
  }

  loading.value = true
  error.value = ''

  try {
    await loginWithAuth({
      username_or_email: identity,
      password,
    })
    await router.replace(redirectTarget.value)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="auth-page">
    <div class="section-card auth-card">
      <div class="auth-card__head">
        <p class="eyebrow">登录</p>
        <h1>欢迎回来</h1>
      </div>

      <form class="auth-form" @submit.prevent="submit">
        <label class="form-field">
          <span>用户名 / 邮箱</span>
          <input v-model="form.username_or_email" class="field-input" type="text" placeholder="输入用户名或邮箱" />
        </label>

        <label class="form-field">
          <span>密码</span>
          <input v-model="form.password" class="field-input" type="password" placeholder="输入密码" />
        </label>

        <p v-if="error" class="state-copy">{{ error }}</p>

        <div class="auth-actions">
          <button class="primary-btn" type="submit" :disabled="loading">
            {{ loading ? '登录中…' : '登录' }}
          </button>
          <RouterLink class="secondary-btn" :to="{ path: '/register', query: route.query }">去注册</RouterLink>
        </div>
      </form>
    </div>
  </section>
</template>
