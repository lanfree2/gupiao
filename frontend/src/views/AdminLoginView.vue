<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { toast } from '@/utils/toast'

const router = useRouter()
const auth = useAuthStore()
const phone = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const res = await api.login({ phone: phone.value.trim(), password: password.value })
    if (res.user.role !== 'admin') {
      error.value = '该账号不是管理员'
      auth.logout()
      return
    }
    auth.setSession(res.access_token, res.user)
    toast('登录成功')
    router.push('/admin/dashboard')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <div class="login-hero">
      <div class="login-hero-inner">
        <div class="login-kicker">ADMIN · PLATFORM OVERVIEW</div>
        <h1>全站数据<br><em>一览运营全貌</em></h1>
        <p>查看所有用户的自选记录、渠道分类与各周期历史业绩，用于平台运营分析与质量监控。</p>
        <div class="login-feats">
          <div class="login-feat"><span class="no">01</span><div><strong>全站股票</strong><span>按代码聚合，查看被自选次数与各周期表现</span></div></div>
          <div class="login-feat"><span class="no">02</span><div><strong>全站渠道</strong><span>用户 × 渠道维度，独立统计每个来源的业绩</span></div></div>
          <div class="login-feat"><span class="no">03</span><div><strong>分周期业绩</strong><span>1周至3月各节点胜率、均收益、样本量</span></div></div>
        </div>
      </div>
    </div>
    <div class="login-panel">
      <div class="login-box">
        <div class="auth-brand"><div class="bt">嘉岭佰</div><small>管理后台</small></div>
        <h2>管理员登录</h2>
        <p class="sub">仅限平台运营人员访问</p>
        <div class="field"><label>管理员手机号</label><input v-model="phone" type="tel"></div>
        <div class="field"><label>密码</label><input v-model="password" type="password"></div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="button" class="btn btn-primary btn-block" :disabled="loading" @click="submit">进入管理后台</button>
        <p class="auth-switch"><RouterLink to="/login">← 返回用户登录</RouterLink></p>
      </div>
    </div>
  </div>
</template>
