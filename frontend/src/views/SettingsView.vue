<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/api/client'
import { toast } from '@/utils/toast'

const oldPassword = ref('')
const newPassword = ref('')
const confirm = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
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
    await api.changePassword({
      old_password: oldPassword.value,
      new_password: newPassword.value,
    })
    toast('密码已修改')
    oldPassword.value = ''
    newPassword.value = ''
    confirm.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : '修改失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>账户设置</h2>
        <p class="desc">修改登录密码</p>
      </div>
      <RouterLink to="/dashboard" class="btn btn-ghost">返回总览</RouterLink>
    </div>
    <div class="card" style="max-width:480px">
      <div class="card-head"><h3>修改密码</h3></div>
      <div class="card-body">
        <div class="form-group">
          <label>当前密码</label>
          <input v-model="oldPassword" class="form-control" type="password">
        </div>
        <div class="form-group">
          <label>新密码</label>
          <input v-model="newPassword" class="form-control" type="password" placeholder="至少 6 位">
        </div>
        <div class="form-group">
          <label>确认新密码</label>
          <input v-model="confirm" class="form-control" type="password">
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="button" class="btn btn-primary" :disabled="loading" @click="submit">保存修改</button>
      </div>
    </div>
  </div>
</template>
