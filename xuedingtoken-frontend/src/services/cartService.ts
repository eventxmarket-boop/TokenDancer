// Deprecated: use cartStore directly
export const cartService = {
  addItem(_item: any) { return Promise.resolve() },
  removeItem(_id: number) { return Promise.resolve() },
  updateQuantity(_id: number, _qty: number) { return Promise.resolve() },
  applyCoupon(_code: string) { return Promise.resolve() },
  clear() { return Promise.resolve() },
}
