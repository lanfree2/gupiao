import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/LoginView.vue') },
    { path: '/admin/login', component: () => import('@/views/AdminLoginView.vue') },
    { path: '/forgot-password', component: () => import('@/views/ForgotPasswordView.vue') },
    {
      path: '/',
      component: () => import('@/layouts/UserLayout.vue'),
      meta: { auth: true },
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', component: () => import('@/views/DashboardView.vue') },
        { path: 'tracking', component: () => import('@/views/TrackingView.vue') },
        { path: 'search', component: () => import('@/views/SearchView.vue') },
        { path: 'add', component: () => import('@/views/AddView.vue') },
        { path: 'channels', component: () => import('@/views/ChannelsView.vue') },
        { path: 'channels/:id', component: () => import('@/views/ChannelDetailView.vue') },
        { path: 'recommendations/:id', component: () => import('@/views/DetailView.vue') },
        { path: 'settings', component: () => import('@/views/SettingsView.vue') },
        { path: 'invites', component: () => import('@/views/InvitesView.vue') },
      ],
    },
    {
      path: '/admin',
      component: () => import('@/layouts/AdminLayout.vue'),
      meta: { auth: true, admin: true },
      children: [
        { path: '', redirect: '/admin/dashboard' },
        { path: 'dashboard', component: () => import('@/views/admin/AdminDashboard.vue') },
        { path: 'stocks', component: () => import('@/views/admin/AdminStocks.vue') },
        { path: 'stocks/:code', component: () => import('@/views/admin/AdminStockDetail.vue') },
        { path: 'channels', component: () => import('@/views/admin/AdminChannels.vue') },
        { path: 'channels/:id', component: () => import('@/views/admin/AdminChannelDetail.vue') },
        { path: 'records', component: () => import('@/views/admin/AdminRecords.vue') },
        { path: 'users', component: () => import('@/views/admin/AdminUsers.vue') },
        { path: 'users/:id', component: () => import('@/views/admin/AdminUserDetail.vue') },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.auth && !auth.token) return '/login'
  if (auth.token && !auth.user) {
    try { await auth.loadUser() } catch { auth.logout(); return '/login' }
  }
  if (to.meta.admin && !auth.isAdmin) return '/dashboard'
  return true
})

export default router
