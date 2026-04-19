import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles/base.css'

const AUTO_SIZE_SELECTOR = [
  'textarea.field-input',
  'textarea.wizard-textarea',
  'textarea.reply-input__textarea',
  'textarea.reply-drawer__textarea',
  '.chat-composer textarea',
  '.howtodo-chat-composer__input',
  'textarea.text-area',
].join(', ')

function autosizeTextarea(element: HTMLTextAreaElement) {
  if (!element.matches(AUTO_SIZE_SELECTOR)) {
    return
  }

  const style = window.getComputedStyle(element)
  const lineHeight = Number.parseFloat(style.lineHeight || '0') || 22
  const verticalPadding = Number.parseFloat(style.paddingTop || '0') + Number.parseFloat(style.paddingBottom || '0')
  const minHeight = Number.parseFloat(style.minHeight || '0') || lineHeight * 2 + verticalPadding
  const maxHeight = Number.parseFloat((element.dataset.autosizeMaxHeight || '').trim() || '0')
  if (element.rows && element.rows > 1) {
    element.rows = 1
  }
  element.style.height = 'auto'
  const nextHeight = Math.max(element.scrollHeight, minHeight)
  element.style.height = maxHeight > 0 ? `${Math.min(nextHeight, maxHeight)}px` : `${nextHeight}px`
  element.style.overflowY = maxHeight > 0 && nextHeight > maxHeight ? 'auto' : 'hidden'
}

function autosizeAllTextareas(root: ParentNode = document) {
  root.querySelectorAll<HTMLTextAreaElement>(AUTO_SIZE_SELECTOR).forEach((element) => {
    autosizeTextarea(element)
  })
}

document.addEventListener(
  'input',
  (event) => {
    const target = event.target as HTMLTextAreaElement | null
    if (target instanceof HTMLTextAreaElement) {
      autosizeTextarea(target)
    }
  },
  true,
)

window.addEventListener('load', () => {
  autosizeAllTextareas()
})

const observer = new MutationObserver(() => {
  autosizeAllTextareas()
})

if (typeof document !== 'undefined' && document.body) {
  observer.observe(document.body, { childList: true, subtree: true })
  requestAnimationFrame(() => autosizeAllTextareas())
} else {
  window.addEventListener('DOMContentLoaded', () => {
    observer.observe(document.body, { childList: true, subtree: true })
    autosizeAllTextareas()
  })
}

createApp(App).use(router).mount('#app')
