import { api } from '@/api/client'

export const adminSystemApi = {
  // 支付事件
  paymentEvents: (params?: {
    provider?: string
    processed_result?: string
    verify_result?: string
    limit?: number
    offset?: number
  }) => api.get<{ total: number; records: any[] }>('/admin/payment-events/', params),
}
