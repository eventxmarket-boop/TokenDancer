export interface ConfirmOpts {
  title?: string
  message?: string
  confirmText?: string
  cancelText?: string
  danger?: boolean
}

export interface GlobalConfirmInstance {
  open: (opts?: ConfirmOpts) => Promise<boolean>
}
