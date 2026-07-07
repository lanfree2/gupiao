<script setup lang="ts">
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/utils/theme'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const { label, toggle } = useTheme()

function navActive(path: string) {
  return route.path.startsWith(path)
}

function exitAdmin() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="layout">
    <aside class="sidebar admin-side">
      <div class="brand">
        <div class="brand-title">荐迹 <span class="admin-pill">ADMIN</span></div>
        <small>平台运营 · 全站数据</small>
      </div>
      <nav class="nav">
        <div class="nav-section">管理菜单</div>
        <RouterLink to="/admin/dashboard" class="nav-link" :class="{ active: navActive('/admin/dashboard') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
          运营总览
        </RouterLink>
        <RouterLink to="/admin/stocks" class="nav-link" :class="{ active: navActive('/admin/stocks') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 20h18M7 16l4-8 4 5 4-10"/></svg>
          全站股票
        </RouterLink>
        <RouterLink to="/admin/channels" class="nav-link" :class="{ active: navActive('/admin/channels') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          全站渠道
        </RouterLink>
        <RouterLink to="/admin/records" class="nav-link" :class="{ active: navActive('/admin/records') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h10"/></svg>
          推荐记录
        </RouterLink>
        <div class="theme-switch">
          <span>{{ label }}</span>
          <div class="theme-toggle" role="button" tabindex="0" @click="toggle" @keyup.enter="toggle" />
        </div>
        <div class="admin-exit">
          <button type="button" @click="exitAdmin">退出管理后台</button>
        </div>
      </nav>
    </aside>

    <main class="main">
      <div class="main-inner">
        <RouterView />
      </div>
    </main>
  </div>
</template>
