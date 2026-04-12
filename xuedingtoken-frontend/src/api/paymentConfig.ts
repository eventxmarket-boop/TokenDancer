import { api } from '@/api/client'

export const publicPaymentConfigApi = {
  get: () => api.get<Record<string, any>>('/payment-config/public'),
}
