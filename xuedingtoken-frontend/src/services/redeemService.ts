// Deprecated: use redeemStore directly
export const redeemService = {
  redeem(_code: string) {
    return Promise.resolve({ ok: false, msg: 'deprecated' })
  },
}
