import { ref, computed } from 'vue'

const theme = ref(localStorage.getItem('theme') || 'light')

export function useTheme() {
  const isDark = computed(() => theme.value === 'dark')
  const label = computed(() => (isDark.value ? '深色' : '浅色'))

  function apply() {
    document.documentElement.setAttribute('data-theme', theme.value)
    localStorage.setItem('theme', theme.value)
  }

  function toggle() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    apply()
  }

  apply()
  return { theme, isDark, label, toggle }
}
