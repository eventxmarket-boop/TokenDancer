import { defineStore } from 'pinia'
import { ref } from 'vue'
import { storage } from '@/utils/storage'

export const useProfileStore = defineStore('profile', () => {
  const profile = ref(storage.get('profile', {
    username: 'demo_user',
    email: 'user@example.com',
    status: 'active',
    memberSince: '2026年4月',
    balance: '$0.00',
    concurrentLimit: 10,
    twoFAOpen: false,
  }))

  const updateProfile = (data: Partial<typeof profile.value>) => {
    Object.assign(profile.value, data)
    save()
  }

  const changePassword = () => {
    // mock：只清理状态，不做真实验证
    return Promise.resolve(true)
  }

  const save = () => { storage.set('profile', profile.value) }

  return { profile, updateProfile, changePassword }
})
