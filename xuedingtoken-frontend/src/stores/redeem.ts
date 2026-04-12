import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'

export interface RedeemRecord {
  id: number
  code: string
  status: string
  message: string | null
  balance_delta: number
  created_at: string
}

export interface RedeemResult {
  success: boolean
  message: string
  balance_delta: number
}

export const useRedeemStore = defineStore('redeem', () => {
  const history = ref<RedeemRecord[]>([])

  async function fetchHistory() {
    history.value = await api.get<RedeemRecord[]>('/redeem/history')
  }

  async function redeem(code: string): Promise<RedeemResult> {
    const res = await api.post<RedeemResult>('/redeem', { code })
    await fetchHistory()
    return res
  }

  return { history, fetchHistory, redeem }
})
