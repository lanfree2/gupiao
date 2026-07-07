import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import { installToast } from '@/utils/toast'

const theme = localStorage.getItem('theme') || 'light'
document.documentElement.setAttribute('data-theme', theme)
installToast()

createApp(App).use(createPinia()).use(router).mount('#app')
