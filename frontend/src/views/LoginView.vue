<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/utils/theme'
import { toast } from '@/utils/toast'

const router = useRouter()
const auth = useAuthStore()
const { label, toggle } = useTheme()

const tab = ref<'login' | 'register'>('login')
const phone = ref('13888888888')
const password = ref('demo123456')
const regPhone = ref('')
const regCode = ref('')
const regPass = ref('')
const agree = ref(false)
const error = ref('')
const loading = ref(false)
const mockHint = ref('')
const codeCooldown = ref(0)
let codeTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  try {
    const cfg = await api.smsConfig()
    if (cfg.mock_hint) mockHint.value = cfg.mock_hint
  } catch { /* ignore */ }
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

async function sendCode() {
  const p = regPhone.value.trim()
  if (!/^1\d{10}$/.test(p)) {
    toast('请输入正确的 11 位手机号')
    return
  }
  try {
    await api.sendSms(p, 'register')
    toast('验证码已发送')
    codeCooldown.value = 60
    if (codeTimer) clearInterval(codeTimer)
    codeTimer = setInterval(() => {
      codeCooldown.value--
      if (codeCooldown.value <= 0 && codeTimer) clearInterval(codeTimer)
    }, 1000)
  } catch (e) {
    toast(e instanceof Error ? e.message : '发送失败')
  }
}

async function doRegister() {
  error.value = ''
  if (!/^1\d{10}$/.test(regPhone.value.trim())) {
    error.value = '请输入正确的手机号'
    return
  }
  if (regCode.value.trim().length !== 6) {
    error.value = '请输入 6 位验证码'
    return
  }
  if (regPass.value.length < 6) {
    error.value = '密码至少 6 位'
    return
  }
  if (!agree.value) {
    error.value = '请先勾选同意用户协议'
    return
  }
  loading.value = true
  try {
    const res = await api.register({
      phone: regPhone.value.trim(),
      code: regCode.value.trim(),
      password: regPass.value,
    })
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
        <div class="login-kicker">JIANJI · TRACK EVERY CALL</div>
        <h1>每一条荐股，<br>都留下<em>可验证的足迹</em></h1>
        <p>把各个渠道的股票推荐录进来，系统自动追踪走势。时间久了，哪个消息来源靠谱，数据自己会说话。</p>
        <div class="login-feats">
          <div class="login-feat"><span class="no">01</span><div><strong>我的渠道分类</strong><span>按自己的消息来源建组，独立统计每个渠道的胜率</span></div></div>
          <div class="login-feat"><span class="no">02</span><div><strong>多周期自动追踪</strong><span>自定义追踪周期，节点到期自动抓取涨跌幅</span></div></div>
          <div class="login-feat"><span class="no">03</span><div><strong>渠道横向对比</strong><span>各渠道胜率、平均收益、历史走势一目了然</span></div></div>
        </div>
      </div>
    </div>
    <div class="login-panel">
      <div class="login-box">
        <div class="auth-brand"><div class="bt">荐迹</div><small>推荐来源 · 走势验证</small></div>
        <div class="auth-tabs">
          <button type="button" class="auth-tab" :class="{ active: tab === 'login' }" @click="tab = 'login'">登录</button>
          <button type="button" class="auth-tab" :class="{ active: tab === 'register' }" @click="tab = 'register'">注册</button>
        </div>

        <div v-if="tab === 'login'">
          <h2>登录您的账户</h2>
          <p class="sub">管理推荐记录与渠道分析 · 演示 13888888888 / demo123456</p>
          <div class="field"><label>手机号</label><input v-model="phone" type="tel" maxlength="11"></div>
          <div class="field"><label>密码</label><input v-model="password" type="password"></div>
          <p v-if="error" class="error">{{ error }}</p>
          <button type="button" class="btn btn-primary btn-block" :disabled="loading" @click="doLogin">进入系统</button>
          <p class="auth-switch">还没有账号？<a @click.prevent="tab = 'register'">立即注册</a> · <RouterLink to="/forgot-password">忘记密码</RouterLink></p>
        </div>

        <div v-else>
          <h2>创建新账户</h2>
          <p class="sub">用手机号注册，一分钟开始追踪</p>
          <div class="field"><label>手机号</label><input v-model="regPhone" type="tel" placeholder="请输入 11 位手机号" maxlength="11"></div>
          <div class="field">
            <label>短信验证码</label>
            <div class="code-row">
              <input v-model="regCode" type="text" placeholder="6 位验证码" maxlength="6">
              <button type="button" class="code-btn" :disabled="codeCooldown > 0" @click="sendCode">
                {{ codeCooldown > 0 ? `${codeCooldown}s` : '获取验证码' }}
              </button>
            </div>
            <p v-if="mockHint" class="form-hint">{{ mockHint }}</p>
          </div>
          <div class="field"><label>设置密码</label><input v-model="regPass" type="password" placeholder="至少 6 位"></div>
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
