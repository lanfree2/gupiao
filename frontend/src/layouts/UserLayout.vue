<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/utils/theme'

const auth = useAuthStore()
const route = useRoute()
const { label, toggle } = useTheme()

const avatarChar = computed(() => (auth.user?.nickname || '用').slice(0, 1))

function navActive(path: string) {
  if (path === '/dashboard') return route.path === '/dashboard'
  return route.path.startsWith(path)
}
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-title">荐迹</div>
        <small>推荐来源 · 走势验证</small>
      </div>
      <nav class="nav">
        <div class="nav-section">主菜单</div>
        <RouterLink to="/dashboard" class="nav-link" :class="{ active: navActive('/dashboard') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
          总览
        </RouterLink>
        <RouterLink to="/tracking" class="nav-link" :class="{ active: navActive('/tracking') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h10"/></svg>
          我的追踪
        </RouterLink>
        <RouterLink to="/add" class="nav-link" :class="{ active: navActive('/add') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/></svg>
          录入推荐
        </RouterLink>
        <RouterLink to="/channels" class="nav-link" :class="{ active: navActive('/channels') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          我的渠道
        </RouterLink>
        <RouterLink to="/search" class="nav-link" :class="{ active: navActive('/search') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
          搜索
        </RouterLink>
        <div class="theme-switch">
          <span>{{ label }}</span>
          <div class="theme-toggle" role="button" tabindex="0" @click="toggle" @keyup.enter="toggle" />
        </div>
      </nav>
      <div class="side-disclaim">本系统仅作个人信息记录与统计参考，不构成任何投资建议。</div>
      <RouterLink to="/settings" class="sidebar-foot">
        <div class="avatar">{{ avatarChar }}</div>
        <div class="avatar-info">
          <strong>{{ auth.user?.nickname || '用户' }}</strong>
          <span>账户设置</span>
        </div>
      </RouterLink>
    </aside>

    <main class="main">
      <div class="mobile-top">
        <div class="bt">荐迹<small>推荐来源 · 走势验证</small></div>
        <button type="button" class="mini-theme" @click="toggle">{{ label === '深色' ? '🌙 深色' : '☀ 浅色' }}</button>
      </div>
      <div class="main-inner">
        <RouterView />
      </div>
      <nav class="bottombar">
        <RouterLink to="/dashboard" class="bnav" :class="{ active: navActive('/dashboard') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
          总览
        </RouterLink>
        <RouterLink to="/tracking" class="bnav" :class="{ active: navActive('/tracking') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h10"/></svg>
          追踪
        </RouterLink>
        <div class="bnav-add-wrap" :class="{ active: navActive('/add') }">
          <RouterLink to="/add" class="bnav-add">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
          </RouterLink>
          <span>录入</span>
        </div>
        <RouterLink to="/channels" class="bnav" :class="{ active: navActive('/channels') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/></svg>
          渠道
        </RouterLink>
        <RouterLink to="/search" class="bnav" :class="{ active: navActive('/search') }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
          搜索
        </RouterLink>
      </nav>
    </main>
  </div>
</template>
