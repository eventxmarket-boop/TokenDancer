<template>
  <div class="auth-page">
    <div class="auth-topbar">
      <router-link to="/" class="back-home">← 返回首页</router-link>
    </div>

    <div class="auth-card-wrapper">
      <div class="auth-card card">
        <h2 class="auth-title">用户注册</h2>
        <p class="auth-sub">使用邮箱注册账号并完成验证</p>

        <form @submit.prevent class="auth-form">
          <div class="form-group">
            <label class="label">用户名</label>
            <input class="input" type="text" placeholder="请输入用户名" v-model="username" />
          </div>

          <div class="form-group">
            <label class="label">邮箱</label>
            <input class="input" type="email" placeholder="请输入邮箱" v-model="email" />
          </div>

          <div class="form-group">
            <label class="label">密码</label>
            <input class="input" type="password" placeholder="请输入密码（至少8位）" v-model="password" />
          </div>

          <label class="checkbox-label terms-label">
            <input type="checkbox" v-model="agreed" />
            <span>我已阅读并同意 <a href="/privacy" target="_blank" class="link-primary">隐私政策</a> 和 <a href="/terms" target="_blank" class="link-primary">服务条款</a></span>
          </label>

          <button class="btn btn-primary w-full btn-lg auth-submit" :disabled="!canSubmit || loading" @click="handleRegister">
            <span v-if="loading">注册中...</span>
            <span v-else>创建账号</span>
          </button>
        </form>

        <div class="auth-footer-link">
          已有账号？<router-link to="/auth/login" class="link-primary">直接登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useFeedbackStore } from '@/stores/feedback'

const router = useRouter()
const auth = useAuthStore()
const feedback = useFeedbackStore()

const username = ref('')
const email = ref('')
const password = ref('')
const agreed = ref(false)
const loading = ref(false)

const canSubmit = computed(() => username.value && email.value && password.value.length >= 8 && agreed.value)

const handleRegister = async () => {
  if (!canSubmit.value) return
  loading.value = true
  try {
    await auth.register(username.value, email.value, password.value)
    feedback.success('注册成功，请登录')
    router.push('/auth/login')
  } catch (e: any) {
    feedback.error(e.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: var(--color-bg-secondary);
}
.auth-topbar {
  background: var(--color-nav-bg);
  padding: 0 24px;
  height: 56px;
  display: flex;
  align-items: center;
}
.back-home {
  color: rgba(255,255,255,0.8);
  font-size: 14px;
  transition: color 0.2s;
}
.back-home:hover { color: #fff; }
.auth-card-wrapper {
  display: flex;
  justify-content: center;
  padding-top: 60px;
}
.auth-card {
  width: 100%;
  max-width: 420px;
  padding: 40px;
}
.auth-title {
  font-size: 24px;
  font-weight: 700;
  text-align: center;
  margin-bottom: 8px;
}
.auth-sub {
  font-size: 14px;
  color: var(--color-text-secondary);
  text-align: center;
  margin-bottom: 32px;
}
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.code-input-row {
  display: flex;
  gap: 8px;
}
.code-input-row .input { flex: 1; }
.code-btn { white-space: nowrap; }
.code-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.terms-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
}
.terms-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  margin-top: 2px;
  flex-shrink: 0;
  cursor: pointer;
}
.link-primary {
  color: var(--color-primary);
  font-weight: 500;
}
.link-primary:hover { text-decoration: underline; }
.auth-submit {
  margin-top: 8px;
}
.auth-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.auth-footer-link {
  text-align: center;
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-top: 24px;
}
</style>
