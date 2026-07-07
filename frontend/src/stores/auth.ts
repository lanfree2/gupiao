import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, type User } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<User | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function loadUser() {
    if (!token.value) return
    user.value = await api.me()
  }

  function setSession(t: string, u: User) {
    token.value = t
    user.value = u
    localStorage.setItem('token', t)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, isLoggedIn, isAdmin, loadUser, setSession, logout }
})
