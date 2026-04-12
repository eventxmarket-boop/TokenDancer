import { api } from '@/api/client'

export interface OrderItem {
  id: number
  product_id: number
  product_name: string
  quantity: number
  unit_price: number
  subtotal: number
  created_at: string
}

export interface OrderListItem {
  id: number
  order_no: string
  status: string
  total_amount: number
  payment_method: string | null
  user_email?: string
  user_id?: number
  created_at: string
}

export interface OrderDetail extends OrderListItem {
  coupon_code: string | null
  items: OrderItem[]
  updated_at: string | null
}

export const ordersApi = {
  list: () => api.get<OrderListItem[]>('/orders'),
  get: (id: number) => api.get<OrderDetail>(`/orders/${id}`),
  create: (payload: { coupon_code?: string }) =>
    api.post<OrderDetail>('/orders', payload),
}
