<template>
  <div class="fp-page">
    <div class="fp-card">
      <div class="fp-header">
        <h1>找回密码</h1>
        <p>输入您注册时使用的邮箱地址</p>
      </div>

      <div v-if="sent" class="fp-success">
        <div class="success-icon">📧</div>
        <h2>找回链接已发送</h2>
        <p>我们已将密码重置说明发送到 <strong>{{ form.email }}</strong></p>
        <p class="hint">如果没有收到邮件，请检查垃圾箱或联系支持。</p>
        <div class="fp-actions">
          <router-link to="/auth/login" class="btn-primary">返回登录</router-link>
          <router-link to="/help" class="btn-outline">联系支持</router-link>
        </div>
      </div>

      <form v-else class="fp-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>邮箱地址</label>
          <input
            v-model="form.email"
            type="email"
            class="form-input"
            placeholder="admin@example.com"
            :disabled="loading"
            required
          />
        </div>
        <div v-if="error" class="form-error">{{ error }}</div>
        <button type="submit" class="btn-submit" :disabled="loading">
          {{ loading ? '发送中…' : '发送找回邮件' }}
        </button>
        <div class="fp-alt">
          想起密码了？
          <router-link to="/auth/login">直接登录</router-link>
        </div>
      </form>

      <div class="fp-support">
        <span>遇到问题？</span>
        <router-link to="/help">帮助中心</router-link>
        <span>·</span>
        <router-link to="/docs-center">文档中心</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { api } from '@/api/client'

const loading = ref(false)
const sent = ref(false)
const error = ref('')
const form = reactive({ email: '' })

const handleSubmit = async () => {
  error.value = ''
  if (!form.email.trim()) { error.value = '请输入邮箱地址'; return }
  loading.value = true
  try {
    await api.post('/auth/forgot-password', { email: form.email })
    sent.value = true
  } catch (e: any) {
    error.value = e?.detail || e?.message || '发送失败，请稍后重试'
  } finally { loading.value = false }
}
</script>

<style scoped>
.fp-page { min-height: 100vh; background: #f5f5f7; display: flex; align-items: center; justify-content: center; padding: 24px; }
.fp-card { background: #fff; border-radius: 16px; padding: 40px; width: 100%; max-width: 420px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }
.fp-header { text-align: center; margin-bottom: 32px; }
.fp-header h1 { font-size: 24px; font-weight: 700; color: #1a1a2e; margin-bottom: 8px; }
.fp-header p { font-size: 14px; color: #888; }
.fp-form { display: flex; flex-direction: column; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 14px; font-weight: 600; color: #333; }
.form-input { padding: 10px 14px; border: 1px solid #e5e4e7; border-radius: 8px; font-size: 15px; outline: none; transition: border-color 0.2s; }
.form-input:focus { border-color: #aa3bff; }
.form-input:disabled { background: #f9f9f9; }
.form-error { color: #ff4d4f; font-size: 13px; background: #fff1f0; padding: 8px 12px; border-radius: 6px; }
.btn-submit { padding: 12px; background: #aa3bff; color: #fff; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: opacity 0.2s; }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }
.fp-alt { text-align: center; font-size: 13px; color: #888; }
.fp-alt a { color: #aa3bff; text-decoration: none; margin-left: 4px; }
.fp-support { text-align: center; font-size: 12px; color: #aaa; margin-top: 24px; display: flex; gap: 8px; justify-content: center; align-items: center; }
.fp-support a { color: #888; text-decoration: none; }
.fp-support a:hover { color: #aa3bff; }
.fp-success { text-align: center; }
.success-icon { font-size: 56px; margin-bottom: 16px; }
.fp-success h2 { font-size: 20px; font-weight: 700; color: #1a1a2e; margin-bottom: 12px; }
.fp-success p { font-size: 14px; color: #555; line-height: 1.6; }
.fp-success .hint { font-size: 12px; color: #aaa; margin-top: 8px; }
.fp-actions { display: flex; gap: 12px; margin-top: 24px; justify-content: center; }
.btn-primary { padding: 10px 20px; background: #aa3bff; color: #fff; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: 600; }
.btn-outline { padding: 10px 20px; background: #fff; color: #aa3bff; border: 1px solid #aa3bff; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: 600; }
</style>
