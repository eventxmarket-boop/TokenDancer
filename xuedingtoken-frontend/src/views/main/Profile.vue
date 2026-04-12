<template>
  <MainLayout title="账户中心" subtitle="管理您的账户信息与安全">
    <!-- Loading -->
    <div v-if="loading" class="loading-wrap">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- Error -->
    <div v-else-if="loadError" class="error-wrap card">
      <p>{{ loadError }}</p>
      <button class="btn btn-outline btn-sm mt-4" @click="fetchProfile">重试</button>
    </div>

    <template v-else>
      <!-- Balance overview -->
      <div class="balance-card card">
        <div class="balance-main">
          <div class="balance-label">账户余额</div>
          <div class="balance-amount">¥{{ typeof profile.balance === 'number' ? profile.balance.toFixed(2) : profile.balance }}</div>
          <div class="balance-sub">可用：¥{{ typeof profile.available_balance === 'number' ? profile.available_balance.toFixed(2) : profile.available_balance }}</div>
        </div>
        <div class="balance-actions">
          <router-link to="/main/billing" class="btn-outline-sm">💰 充值</router-link>
          <router-link to="/main/subscriptions" class="btn-outline-sm">📋 订阅</router-link>
        </div>
      </div>

      <!-- Quick navigation -->
      <div class="quick-nav">
        <router-link to="/main/subscriptions" class="quick-nav-item">
          <span class="qn-icon">📋</span><span class="qn-label">我的订阅</span>
        </router-link>
        <router-link to="/main/billing" class="quick-nav-item">
          <span class="qn-icon">💰</span><span class="qn-label">账单中心</span>
        </router-link>
        <router-link to="/orders" class="quick-nav-item">
          <span class="qn-icon">📦</span><span class="qn-label">我的订单</span>
        </router-link>
        <router-link to="/main/keys" class="quick-nav-item">
          <span class="qn-icon">🔑</span><span class="qn-label">API Keys</span>
        </router-link>
        <router-link to="/help" class="quick-nav-item">
          <span class="qn-icon">❓</span><span class="qn-label">帮助中心</span>
        </router-link>
      </div>

      <!-- Account info card -->
      <div class="info-card card">
        <div class="info-header">
          <h3 class="section-h3">基本信息</h3>
          <span :class="['badge', profile.status === 'active' ? 'badge-success' : 'badge-danger']">
            {{ profile.status === 'active' ? '活跃' : profile.status }}
          </span>
        </div>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">用户名</span>
            <span class="info-value">{{ profile.username }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">邮箱</span>
            <span class="info-value">{{ profile.email }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">注册时间</span>
            <span class="info-value">{{ formatDate(profile.created_at) }}</span>
          </div>
        </div>
        <div class="info-contact">
          如有需要，请前往 <router-link to="/help" class="inline-link">帮助中心</router-link> 或联系 <a href="mailto:support@demoplat.io" class="inline-link">support@demoplat.io</a>
        </div>
      </div>

      <!-- Edit profile -->
      <div class="edit-card card">
        <h3 class="section-h3">编辑个人资料</h3>
        <div class="form-row-profile">
          <div class="form-group">
            <label class="label">用户名</label>
            <input class="input" v-model="editUsername" placeholder="请输入用户名" />
          </div>
        </div>
        <button class="btn btn-primary" @click="handleUpdateProfile" :disabled="saving">
          {{ saving ? '保存中...' : '更新资料' }}
        </button>
      </div>

      <!-- Change password -->
      <div class="password-card card">
        <h3 class="section-h3">修改密码</h3>
        <div class="form-stack">
          <div class="form-group">
            <label class="label">当前密码</label>
            <input class="input" type="password" v-model="currentPwd" placeholder="请输入当前密码" />
          </div>
          <div class="form-group">
            <label class="label">新密码</label>
            <input class="input" type="password" v-model="newPwd" placeholder="请输入新密码（至少8位）" @input="validatePwd" />
            <span v-if="pwdError" class="field-error">{{ pwdError }}</span>
          </div>
          <div class="form-group">
            <label class="label">确认新密码</label>
            <input class="input" type="password" v-model="confirmPwd" placeholder="请再次输入新密码" @input="validatePwd" />
            <span v-if="confirmError" class="field-error">{{ confirmError }}</span>
          </div>
        </div>
        <button class="btn btn-primary" @click="handleChangePassword"
          :disabled="!!pwdError || !!confirmError || changingPwd">
          {{ changingPwd ? '修改中...' : '修改密码' }}
        </button>
      </div>

      <!-- 2FA -->
      <div class="auth2-card card">
        <h3 class="section-h3">两步验证 (2FA)</h3>
        <p class="auth2-desc">使用 Google Authenticator 或类似应用扫描下方二维码，获取验证码进行二次验证。</p>
        <div class="auth2-content">
          <div class="auth2-icon">🔐</div>
          <div class="auth2-info">
            <p class="auth2-tag">功能未开放</p>
            <p class="auth2-hint">该功能正在开发中，敬请期待</p>
          </div>
        </div>
      </div>
    </template>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import MainLayout from '@/components/main/MainLayout.vue'
import { profileApi, type UserProfile } from '@/api/profile'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()
const loading = ref(false)
const saving = ref(false)
const changingPwd = ref(false)
const loadError = ref<string | null>(null)

const profile = reactive<UserProfile>({
  username: '',
  email: '',
  status: 'active',
  balance: 0,
  available_balance: 0,
  created_at: '',
})

const editUsername = ref('')
const currentPwd = ref('')
const newPwd = ref('')
const confirmPwd = ref('')
const pwdError = ref('')
const confirmError = ref('')

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const fetchProfile = async () => {
  loading.value = true
  loadError.value = null
  try {
    const data = await profileApi.get()
    Object.assign(profile, data)
    editUsername.value = data.username
  } catch (e: any) {
    loadError.value = e.message || '加载失败'
    feedback.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const handleUpdateProfile = async () => {
  if (!editUsername.value.trim()) return
  saving.value = true
  try {
    const data = await profileApi.update({ username: editUsername.value })
    Object.assign(profile, data)
    feedback.success('资料已更新')
  } catch (e: any) {
    feedback.error(e.message || '更新失败')
  } finally {
    saving.value = false
  }
}

const handleChangePassword = async () => {
  validatePwd()
  if (pwdError.value || confirmError.value) return
  if (!currentPwd.value) {
    feedback.warning('请输入当前密码')
    return
  }
  if (newPwd.value !== confirmPwd.value) {
    confirmError.value = '两次输入的密码不一致'
    return
  }
  changingPwd.value = true
  try {
    await profileApi.changePassword(currentPwd.value, newPwd.value)
    feedback.success('密码修改成功')
    currentPwd.value = ''
    newPwd.value = ''
    confirmPwd.value = ''
  } catch (e: any) {
    feedback.error(e.message || '修改失败')
  } finally {
    changingPwd.value = false
  }
}

const validatePwd = () => {
  pwdError.value = ''
  confirmError.value = ''
  if (newPwd.value.length > 0 && newPwd.value.length < 8) {
    pwdError.value = '密码长度不能少于8位'
  }
  if (confirmPwd.value && confirmPwd.value !== newPwd.value) {
    confirmError.value = '两次输入的密码不一致'
  }
}

onMounted(fetchProfile)
</script>

<style scoped>
.loading-wrap { text-align: center; padding: 64px 0; color: var(--color-text-secondary); }
.loading-spinner { width: 36px; height: 36px; border: 3px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 12px; }
@keyframes spin { to { transform: rotate(360deg); } }
.error-wrap { text-align: center; padding: 64px 0; }
.balance-card { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; padding: 24px 28px; background: linear-gradient(135deg, #1a1a2e 0%, #2d1b4e 100%); border-radius: 12px; }
.balance-main { display: flex; flex-direction: column; gap: 4px; }
.balance-label { font-size: 13px; color: rgba(255,255,255,0.6); }
.balance-amount { font-size: 32px; font-weight: 800; color: #fff; }
.balance-sub { font-size: 13px; color: rgba(255,255,255,0.6); }
.balance-actions { display: flex; gap: 10px; }
.btn-outline-sm { padding: 8px 16px; background: rgba(255,255,255,0.15); color: #fff; border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600; transition: background 0.2s; white-space: nowrap; }
.btn-outline-sm:hover { background: rgba(255,255,255,0.25); }
.quick-nav { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.quick-nav-item { display: flex; align-items: center; gap: 8px; padding: 10px 16px; background: #fff; border: 1px solid var(--color-border); border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600; color: #333; transition: all 0.2s; flex: 1; min-width: 120px; justify-content: center; }
.quick-nav-item:hover { border-color: #aa3bff; color: #aa3bff; background: #fafafa; }
.qn-icon { font-size: 18px; }
.qn-label { font-size: 13px; }
.info-card, .edit-card, .password-card, .auth2-card { margin-bottom: 24px; }
.section-h3 { font-size: 16px; font-weight: 700; margin-bottom: 20px; color: var(--color-text); }
.info-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.info-header .section-h3 { margin-bottom: 0; }
.info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-label { font-size: 12px; color: var(--color-text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
.info-value { font-size: 15px; font-weight: 500; color: var(--color-text); }
.info-contact { font-size: 13px; color: var(--color-text-secondary); padding-top: 16px; border-top: 1px solid var(--color-border); }
.form-row-profile { margin-bottom: 20px; }
.form-stack { display: flex; flex-direction: column; gap: 16px; margin-bottom: 20px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.field-error { font-size: 12px; color: var(--color-danger); margin-top: 2px; }
.auth2-desc { font-size: 14px; color: var(--color-text-secondary); margin-bottom: 20px; }
.auth2-content { display: flex; align-items: center; gap: 20px; background: var(--color-bg-secondary); border-radius: var(--radius-md); padding: 20px; }
.auth2-icon { font-size: 40px; }
.auth2-tag { font-size: 16px; font-weight: 700; color: var(--color-warning); margin-bottom: 4px; }
.auth2-hint { font-size: 13px; color: var(--color-text-secondary); }
.inline-link { color: #aa3bff; text-decoration: none; }
.inline-link:hover { text-decoration: underline; }
</style>
