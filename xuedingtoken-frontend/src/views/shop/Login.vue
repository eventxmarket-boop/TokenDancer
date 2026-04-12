<template>
  <div class="auth-page">
    <div class="auth-topbar">
      <router-link to="/" class="back-home">← 返回首页</router-link>
      <span class="auth-topbar-title">个人中心</span>
    </div>

    <div class="auth-card-wrapper">
      <div class="auth-card card">
        <div class="auth-logo">{{ APP_BRAND_NAME }}</div>
        <h2 class="auth-title">用户登录</h2>
        <p class="auth-sub">欢迎回来，继续你的订单流程</p>

        <form @submit.prevent class="auth-form">
          <div class="form-group">
            <label class="label">邮箱</label>
            <div class="input-with-icon">
              <span class="input-icon">📧</span>
              <input class="input input-padded" type="email" placeholder="请输入邮箱" v-model="email" />
            </div>
          </div>

          <div class="form-group">
            <label class="label">密码</label>
            <div class="input-with-icon">
              <span class="input-icon">🔒</span>
              <input class="input input-padded" type="password" placeholder="请输入密码" v-model="password" />
            </div>
          </div>

          <div class="form-row">
            <label class="checkbox-label">
              <input type="checkbox" v-model="rememberMe" checked />
              <span>记住我</span>
            </label>
            <a class="forgot-link" @click.prevent="showForgotHint = true">忘记密码？</a>
          </div>

          <button class="btn btn-primary w-full btn-lg auth-submit" :disabled="loading" @click="handleLogin">
            <span v-if="loading">登录中...</span>
            <span v-else>登录</span>
          </button>
        </form>

        <div class="auth-footer-link">
          还没有账号？<router-link to="/auth/register" class="link-primary">立即注册</router-link>
        </div>

        <!-- 忘记密码弹窗 -->
        <div v-if="showForgotHint" class="modal-mask" @click.self="showForgotHint = false">
          <div class="modal-box">
            <h3 class="modal-title">忘记密码</h3>
            <p class="modal-msg">当前版本暂未开放自助找回，请联系管理员重置密码。</p>
            <div class="modal-actions">
              <button class="btn-outline" @click="showForgotHint = false">知道了</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useFeedbackStore } from '@/stores/feedback'
import { APP_BRAND_NAME } from '@/constants/branding'

const router = useRouter()
const auth = useAuthStore()
const feedback = useFeedbackStore()

const email = ref('')
const password = ref('')
const rememberMe = ref(true)
const loading = ref(false)
const showForgotHint = ref(false)

const handleLogin = async () => {
  if (!email.value.trim() || !password.value) {
    feedback.error('请输入邮箱和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    feedback.success('登录成功')
    const redirect = (router.currentRoute.value.query.redirect as string) || '/main/dashboard'
    router.push(redirect)
  } catch (e: any) {
    feedback.error(e.message || '登录失败')
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
  color: var(--color-nav-text);
  padding: 0 24px;
  height: 56px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.back-home {
  color: rgba(255,255,255,0.8);
  font-size: 14px;
  transition: color 0.2s;
}
.back-home:hover { color: #fff; }
.auth-topbar-title {
  font-size: 14px;
  color: rgba(255,255,255,0.6);
}
.auth-card-wrapper {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 60px;
}
.auth-card {
  width: 100%;
  max-width: 420px;
  padding: 40px;
}
.auth-logo {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  text-align: center;
  margin-bottom: 8px;
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
.input-with-icon {
  position: relative;
}
.input-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
}
.input-padded {
  padding-left: 40px;
}
.form-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-text-secondary);
  cursor: pointer;
}
.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}
.forgot-link {
  font-size: 14px;
  color: var(--color-primary);
}
.auth-submit {
  margin-top: 8px;
}
.auth-footer-link {
  text-align: center;
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-top: 24px;
}
.link-primary {
  color: var(--color-primary);
  font-weight: 500;
}
.link-primary:hover { text-decoration: underline; }

/* Modal */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-box {
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  padding: 32px;
  max-width: 420px;
  width: 90%;
}
.modal-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 16px;
}
.modal-msg {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: 24px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
.btn-outline {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text);
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-outline:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

@media (max-width: 640px) {
  .auth-topbar {
    padding: 0 14px;
    gap: 10px;
  }
  .auth-card-wrapper {
    padding: 24px 14px 40px;
  }
  .auth-card {
    max-width: none;
    padding: 24px 18px;
  }
  .auth-title {
    font-size: 22px;
  }
  .auth-sub {
    margin-bottom: 24px;
  }
  .form-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  .modal-mask {
    padding: 12px;
    align-items: flex-end;
  }
  .modal-box {
    width: 100%;
    max-width: none;
    padding: 20px;
    border-radius: 18px 18px 0 0;
  }
}
</style>
