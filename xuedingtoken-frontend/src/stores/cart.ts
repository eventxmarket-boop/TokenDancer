import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'
import { ordersApi } from '@/api/orders'
import type { OrderDetail } from '@/api/orders'

export interface CartItem {
  id: number
  product_id: number
  quantity: number
  unit_price: number
  created_at: string
}

export interface Cart {
  id: number
  user_id: number
  coupon_code: string | null
  items: CartItem[]
  subtotal: number
  total_quantity: number
  created_at: string
  updated_at: string | null
}

export const useCartStore = defineStore('cart', () => {
  const cart = ref<Cart | null>(null)
  const lastOrder = ref<OrderDetail | null>(null)

  async function fetchCart() {
    cart.value = await api.get<Cart>('/cart')
  }

  async function addItem(productId: number, quantity: number) {
    cart.value = await api.post<Cart>('/cart/items', { product_id: productId, quantity })
  }

  async function updateItem(itemId: number, quantity: number) {
    cart.value = await api.patch<Cart>(`/cart/items/${itemId}`, { quantity })
  }

  async function deleteItem(itemId: number) {
    cart.value = await api.delete<Cart>(`/cart/items/${itemId}`)
  }

  async function setCoupon(couponCode: string) {
    cart.value = await api.patch<Cart>('/cart/coupon', { coupon_code: couponCode })
  }

  async function createOrder(): Promise<OrderDetail> {
    const order = await ordersApi.create({ coupon_code: cart.value?.coupon_code || undefined })
    lastOrder.value = order
    // Refresh cart after order creation
    await fetchCart()
    return order
  }

  const totalItems = computed(() => cart.value?.total_quantity ?? 0)
  const items = computed(() => cart.value?.items ?? [])
  const subtotal = computed(() => cart.value?.subtotal ?? 0)
  const couponCode = computed(() => cart.value?.coupon_code ?? '')
  const discount = computed(() => {
    if (!couponCode.value) return 0
    if (couponCode.value.toUpperCase() === 'SAVE10') return Math.round(subtotal.value * 0.1)
    if (couponCode.value.toUpperCase() === 'FREE') return subtotal.value
    return 0
  })
  const total = computed(() => subtotal.value - discount.value)

  return {
    cart, totalItems, items, subtotal, couponCode, discount, total, lastOrder,
    fetchCart, addItem, updateItem, deleteItem, setCoupon, createOrder
  }
})
