import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'

export interface DashboardData {
  balance: number
  available_balance: number
  api_key_count: number
  today_requests: number
  today_cost: number
  today_tokens: number
  total_tokens: number
  rpm: number
  tpm: number
  avg_latency_ms: number
}

export const useDashboardStore = defineStore('dashboard', () => {
  const data = ref<DashboardData | null>(null)

  async function fetchDashboard() {
    data.value = await api.get<DashboardData>('/dashboard')
  }

  return { data, fetchDashboard }
})
