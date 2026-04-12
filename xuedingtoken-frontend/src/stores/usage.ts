import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'

export interface UsageRecord {
  id: number
  api_key_id: number
  model_name: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
  cost: number
  latency_ms: number
  requested_at: string
}

export const useUsageStore = defineStore('usage', () => {
  const records = ref<UsageRecord[]>([])
  const dateRange = ref('近 7 天')
  const granularity = ref('按天')
  const filterKey = ref('全部密钥')

  async function fetchUsage(params?: { api_key_id?: number; date_from?: string; date_to?: string }) {
    records.value = await api.get<UsageRecord[]>('/usage', params)
  }

  function setDateRange(v: string) { dateRange.value = v }
  function setGranularity(v: string) { granularity.value = v }
  function setFilterKey(v: string) { filterKey.value = v }

  return { records, dateRange, granularity, filterKey, fetchUsage, setDateRange, setGranularity, setFilterKey }
})
