import { useUsageStore } from '@/stores/usage'

export interface UsageRecord {
  id: number
  keyName: string
  model: string
  inputTokens: number
  outputTokens: number
  cost: string
  latency: string
  time: string
}

export const usageMockRecords: UsageRecord[] = [
  { id: 1, keyName: 'my-key', model: 'claude-3-opus', inputTokens: 12400, outputTokens: 3800, cost: '$0.0812', latency: '820ms', time: '2026-04-09 14:23' },
  { id: 2, keyName: 'my-key', model: 'claude-3-sonnet', inputTokens: 5600, outputTokens: 2100, cost: '$0.0385', latency: '640ms', time: '2026-04-09 10:15' },
  { id: 3, keyName: 'my-key', model: 'claude-3-haiku', inputTokens: 2800, outputTokens: 900, cost: '$0.0111', latency: '410ms', time: '2026-04-08 16:40' },
  { id: 4, keyName: 'my-key', model: 'claude-3-opus', inputTokens: 8900, outputTokens: 2700, cost: '$0.0580', latency: '750ms', time: '2026-04-08 11:20' },
  { id: 5, keyName: 'test-key', model: 'claude-3-sonnet', inputTokens: 4300, outputTokens: 1600, cost: '$0.0295', latency: '590ms', time: '2026-04-07 15:05' },
]

export const usageService = {
  fetchRecords() {
    return usageMockRecords
  },

  getFiltered(keyFilter: string) {
    if (keyFilter === '全部密钥') return usageMockRecords
    return usageMockRecords.filter(r => r.keyName === keyFilter)
  },

  calcStats(records: UsageRecord[]) {
    return {
      totalRequests: records.length,
      totalInput: records.reduce((s, r) => s + r.inputTokens, 0),
      totalOutput: records.reduce((s, r) => s + r.outputTokens, 0),
      totalTokens: records.reduce((s, r) => s + r.inputTokens + r.outputTokens, 0),
      totalCost: records.reduce((s, r) => s + parseFloat(r.cost.replace('$', '')), 0).toFixed(4),
      avgLatency: records.length
        ? Math.round(records.reduce((s, r) => s + parseInt(r.latency), 0) / records.length) + 'ms'
        : '0ms',
    }
  },

  exportCSV(records: UsageRecord[]) {
    if (records.length === 0) return
    const headers = ['时间', 'API密钥', '模型', '输入Token', '输出Token', '总Token', '费用', '延迟']
    const rows = records.map(r => [
      r.time, r.keyName, r.model,
      r.inputTokens, r.outputTokens,
      r.inputTokens + r.outputTokens,
      r.cost, r.latency,
    ])
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n')
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'usage_' + new Date().toISOString().slice(0, 10) + '.csv'
    a.click()
    URL.revokeObjectURL(url)
  },

  setDateRange(v: string) { useUsageStore().setDateRange(v) },
  setGranularity(v: string) { useUsageStore().setGranularity(v) },
  setFilterKey(v: string) { useUsageStore().setFilterKey(v) },
}
