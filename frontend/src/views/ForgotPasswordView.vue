<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { api } from '@/api/client'
import { toast } from '@/utils/toast'

const router = useRouter()
const phone = ref('')
const code = ref('')
const newPassword = ref('')
const confirm = ref('')
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

async function sendCode() {
  const p = phone.value.trim()
  if (!/^1\d{10}$/.test(p)) {
    toast('请输入正确的 11 位手机号')
    return
  }
  try {
    await api.sendSms(p, 'reset_password')
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

async function submit() {
  error.value = ''
  if (!/^1\d{10}$/.test(phone.value.trim())) {
    error.value = '请输入正确的手机号'
    return
  }
  if (code.value.trim().length !== 6) {
    error.value = '请输入 6 位验证码'
    return
  }
  if (newPassword.value.length < 6) {
    error.value = '新密码至少 6 位'
    return
  }
  if (newPassword.value !== confirm.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  loading.value = true
  try {
    await api.resetPasswordSms({
      phone: phone.value.trim(),
      code: code.value.trim(),
      new_password: newPassword.value,
    })
    toast('密码已重置')
    router.push('/login')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '重置失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <div class="login-hero">
      <div class="login-hero-inner">
        <div class="login-kicker">RESET PASSWORD</div>
        <h1>找回<br><em>账户密码</em></h1>
        <p>通过短信验证码验证身份后，设置新密码。</p>
      </div>
    </div>
    <div class="login-panel">
      <div class="login-box">
        <div class="auth-brand"><div class="bt">嘉岭佰</div><small>重置密码</small></div>
        <h2>忘记密码</h2>
        <p class="sub">输入注册手机号并完成短信验证</p>
        <div class="field"><label>手机号</label><input v-model="phone" type="tel" maxlength="11"></div>
        <div class="field">
          <label>短信验证码</label>
          <div class="code-row">
            <input v-model="code" type="text" placeholder="6 位验证码" maxlength="6">
            <button type="button" class="code-btn" :disabled="codeCooldown > 0" @click="sendCode">
              {{ codeCooldown > 0 ? `${codeCooldown}s` : '获取验证码' }}
            </button>
          </div>
          <p v-if="mockHint" class="form-hint">{{ mockHint }}</p>
        </div>
        <div class="field"><label>新密码</label><input v-model="newPassword" type="password" placeholder="至少 6 位"></div>
        <div class="field"><label>确认新密码</label><input v-model="confirm" type="password"></div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="button" class="btn btn-primary btn-block" :disabled="loading" @click="submit">重置密码</button>
        <p class="auth-switch"><RouterLink to="/login">← 返回登录</RouterLink></p>
      </div>
    </div>
  </div>
</template>
