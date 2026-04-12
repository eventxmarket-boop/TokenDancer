<template>
  <router-view />
  <BaseToast />
  <GlobalConfirm ref="confirmRef" />
</template>

<script setup lang="ts">
import { ref, provide, onMounted } from 'vue'
import BaseToast from '@/components/common/BaseToast.vue'
import GlobalConfirm from '@/components/common/GlobalConfirm.vue'
import { CONFIRM_KEY } from '@/stores/feedback'
import { useAuthStore } from '@/stores/auth'

const confirmRef = ref<InstanceType<typeof GlobalConfirm> | null>(null)
provide(CONFIRM_KEY, confirmRef)

const auth = useAuthStore()
onMounted(async () => {
  if (auth.token) {
    const ok = await auth.fetchMe()
    if (!ok) {
      // token invalid — already cleared in fetchMe
      // Redirect to login to avoid sitting on a blank page
      window.location.href = '/auth/login'
    }
  }
})
</script>
