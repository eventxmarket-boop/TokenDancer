import { api } from '@/api/client'

export const subscriptionsApi = {
  list: () => api.get<any[]>('/subscriptions/me'),
  active: () => api.get<any>('/subscriptions/me/active'),
  tokenGrants: () => api.get<any[]>('/subscriptions/me/token-grants'),
}

export const billingApi = {
  summary: () => api.get<any>('/billing/summary'),
  ledger: () => api.get<any[]>('/billing/ledger'),
}
