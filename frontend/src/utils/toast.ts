import { ref } from 'vue'

const message = ref('')
const visible = ref(false)
let timer: ReturnType<typeof setTimeout> | null = null

export function useToastState() {
  return { message, visible }
}

export function toast(msg: string) {
  message.value = msg
  visible.value = true
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => {
    visible.value = false
  }, 2400)
}

declare global {
  interface Window {
    toast?: (msg: string) => void
  }
}

export function installToast() {
  window.toast = toast
}
