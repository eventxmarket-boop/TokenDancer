/// <reference types="vite/client" />

declare module '*.vue' {
  const component: any
  export default component
}

declare module 'vue' {
  export type Ref<T = any> = { value: T }
  export type InjectionKey<T> = symbol & { __type?: T }
  export function createApp(...args: any[]): any
  export function ref<T = any>(value?: T): Ref<T>
  export function reactive<T extends object>(value: T): T
  export function computed<T>(getter: () => T): Ref<T>
  export function onMounted(fn: (...args: any[]) => any): void
  export function onUnmounted(fn: (...args: any[]) => any): void
  export function watch(source: any, cb: (...args: any[]) => any, options?: any): void
  export function provide<T>(key: InjectionKey<T> | string, value: T): void
  export function inject<T>(key: InjectionKey<T> | string): T | undefined
}

declare module 'pinia' {
  export const createPinia: any
  export const defineStore: any
}

declare module 'vue-router' {
  export const createRouter: any
  export const createWebHistory: any
  export const useRoute: any
  export const useRouter: any
}

declare module 'chart.js' {
  export const Chart: any
  export const LineController: any
  export const LineElement: any
  export const PointElement: any
  export const LinearScale: any
  export const CategoryScale: any
  export const Tooltip: any
  export const Legend: any
  export const Filler: any
}
