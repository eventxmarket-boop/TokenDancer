import { api } from '@/api/client'

export interface PaymentIntentResponse {
  payment_id: string
  order_id: number
  amount: number
  currency: string
  status: string
  checkout_url?: string
  client_secret?: string
  payment_url?: string
}

export interface PaymentStatus {
  order_id: number
  payment_id: string | null
  status: string
  paid_at: string | null
}

export const paymentsApi = {
  create: (orderId: number, paymentMethod: string) =>
    api.post<PaymentIntentResponse>('/payments/create', { order_id: orderId, payment_method: paymentMethod }),

  status: (orderId: number) => api.get<PaymentStatus>(`/payments/${orderId}/status`),
}
