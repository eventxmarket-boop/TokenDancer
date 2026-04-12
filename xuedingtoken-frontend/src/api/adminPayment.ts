import { api } from '@/api/client'

export type PaymentConfigPayload = Record<string, any>

export const adminPaymentConfigApi = {
  get: () => api.get<PaymentConfigPayload>('/admin/payment-config/'),
  update: (data: PaymentConfigPayload) => api.put<PaymentConfigPayload>('/admin/payment-config/', data),
  repairOrder: (orderId: number) => api.post<{ success: boolean; message: string; status?: string }>(`/admin/payment-config/orders/${orderId}/repair`, {}),
}
