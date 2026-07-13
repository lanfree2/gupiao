<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/utils/theme'
import { toast } from '@/utils/toast'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { label, toggle } = useTheme()

const tab = ref<'login' | 'register'>('login')
const phone = ref('')
const password = ref('')
const regPhone = ref('')
const regPass = ref('')
const regPass2 = ref('')
const regInvite = ref('')
const smsEnabled = ref(false)
const agree = ref(false)
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  try {
    const cfg = await api.registerConfig()
    smsEnabled.value = cfg.sms.enabled
  } catch { /* ignore */ }
  const invite = route.query.invite
  if (typeof invite === 'string' && invite.trim()) {
    regInvite.value = invite.trim().toUpperCase()
    tab.value = 'register'
  }
  if (route.query.tab === 'register') tab.value = 'register'
})

watch(() => route.query.invite, (v) => {
  if (typeof v === 'string' && v.trim()) {
    regInvite.value = v.trim().toUpperCase()
    tab.value = 'register'
  }
})

async function doLogin() {
  error.value = ''
  loading.value = true
  try {
    const res = await api.login({ phone: phone.value.trim(), password: password.value })
    auth.setSession(res.access_token, res.user)
    if (res.user.role === 'admin') {
      router.push('/admin/dashboard')
    } else {
      router.push('/dashboard')
    }
    toast('登录成功')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败'
  } finally {
    loading.value = false
  }
}

async function doRegister() {
  error.value = ''
  if (!/^1\d{10}$/.test(regPhone.value.trim())) {
    error.value = '请输入正确的手机号'
    return
  }
  if (regPass.value.length < 6) {
    error.value = '密码至少 6 位'
    return
  }
  if (regPass.value !== regPass2.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  if (!agree.value) {
    error.value = '请先勾选同意用户协议'
    return
  }
  loading.value = true
  try {
    const body: Record<string, string> = {
      phone: regPhone.value.trim(),
      password: regPass.value,
    }
    if (regInvite.value.trim()) body.invite_code = regInvite.value.trim().toUpperCase()
    const res = await api.register(body)
    auth.setSession(res.access_token, res.user)
    toast('注册成功')
    router.push('/dashboard')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <div class="login-hero">
      <div class="login-hero-inner">
        <div class="login-kicker">JIALINGBAI · TRACK EVERY CALL</div>
        <h1>每一条荐股，<br>都留下<em>可验证的足迹</em></h1>
        <p>把各个渠道的股票自选录进来，系统自动追踪走势。时间久了，哪个消息来源靠谱，数据自己会说话。</p>
        <div class="login-feats">
          <div class="login-feat"><span class="no">01</span><div><strong>我的渠道分类</strong><span>按自己的消息来源建组，独立统计每个渠道的胜率</span></div></div>
          <div class="login-feat"><span class="no">02</span><div><strong>多周期自动追踪</strong><span>自定义追踪周期，节点到期自动抓取涨跌幅</span></div></div>
          <div class="login-feat"><span class="no">03</span><div><strong>渠道横向对比</strong><span>各渠道胜率、平均收益、历史走势一目了然</span></div></div>
        </div>
      </div>
    </div>
    <div class="login-panel">
      <div class="login-box">
        <div class="auth-brand"><div class="bt">嘉岭佰</div><small>自选来源 · 走势验证</small></div>
        <div class="auth-tabs">
          <button type="button" class="auth-tab" :class="{ active: tab === 'login' }" @click="tab = 'login'">登录</button>
          <button type="button" class="auth-tab" :class="{ active: tab === 'register' }" @click="tab = 'register'">注册</button>
        </div>

        <div v-if="tab === 'login'">
          <h2>登录您的账户</h2>
          <p class="sub">管理自选记录与渠道分析</p>
          <div class="field"><label>手机号</label><input v-model="phone" type="tel" maxlength="11" placeholder="请输入手机号"></div>
          <div class="field"><label>密码</label><input v-model="password" type="password" placeholder="请输入密码"></div>
          <p v-if="error" class="error">{{ error }}</p>
          <button type="button" class="btn btn-primary btn-block" :disabled="loading" @click="doLogin">进入系统</button>
          <p class="auth-switch">
            还没有账号？<a @click.prevent="tab = 'register'">立即注册</a>
            <template v-if="smsEnabled"> · <RouterLink to="/forgot-password">忘记密码</RouterLink></template>
            <template v-else> · <span class="dim">忘记密码请联系管理员</span></template>
          </p>
        </div>

        <div v-else class="register-panel">
          <h2>创建新账户</h2>
          <p class="sub">用手机号注册，一分钟开始追踪</p>
          <div class="field">
            <label>手机号</label>
            <input v-model="regPhone" type="tel" inputmode="numeric" autocomplete="tel" placeholder="请输入 11 位手机号" maxlength="11">
          </div>
          <div class="field">
            <label>设置密码</label>
            <input v-model="regPass" type="password" autocomplete="new-password" placeholder="至少 6 位" minlength="6">
          </div>
          <div class="field">
            <label>确认密码</label>
            <input v-model="regPass2" type="password" autocomplete="new-password" placeholder="再次输入密码" minlength="6">
          </div>
          <div v-if="regInvite" class="field">
            <label>邀请码</label>
            <input v-model="regInvite" class="mono" readonly>
          </div>
          <label class="agree">
            <input v-model="agree" type="checkbox">
            <span>我已阅读并同意《用户协议》与《隐私政策》</span>
          </label>
          <p v-if="error" class="error">{{ error }}</p>
          <button type="button" class="btn btn-primary btn-block" :disabled="loading" @click="doRegister">注册并进入</button>
          <p class="auth-switch">已有账号？<a @click.prevent="tab = 'login'">直接登录</a></p>
        </div>

        <div class="login-theme">
          <span>{{ label === '深色' ? '深色模式' : '浅色模式' }}</span>
          <div class="theme-toggle" role="button" tabindex="0" @click="toggle" @keyup.enter="toggle" />
        </div>
        <p class="login-admin-link"><RouterLink to="/admin/login">管理员入口 →</RouterLink></p>
      </div>
    </div>
  </div>
</template>
