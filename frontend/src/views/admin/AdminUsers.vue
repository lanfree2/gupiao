<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '@/api/client'
import { toast } from '@/utils/toast'

interface AdminUser {
  id: number
  phone: string
  nickname: string
  invite_code: string | null
  inviter_id: number | null
  inviter_nickname: string | null
  invitee_count: number
  created_at: string
}

const q = ref('')
const users = ref<AdminUser[]>([])
const loading = ref(false)
const smsRequired = ref(false)
const savingSettings = ref(false)

const showBind = ref(false)
const bindUserId = ref<number | null>(null)
const bindInviteCode = ref('')
const bindInviterId = ref('')
const binding = ref(false)

async function loadUsers() {
  loading.value = true
  try {
    users.value = await api.adminUsers(q.value.trim() || undefined) as AdminUser[]
  } finally {
    loading.value = false
  }
}

async function loadSettings() {
  const s = await api.adminSettings()
  smsRequired.value = s.register_sms_required
}

async function saveSettings() {
  savingSettings.value = true
  try {
    await api.adminSaveSettings({ register_sms_required: smsRequired.value })
    toast('设置已保存')
  } catch (e) {
    toast(e instanceof Error ? e.message : '保存失败')
  } finally {
    savingSettings.value = false
  }
}

function openBind(user: AdminUser) {
  bindUserId.value = user.id
  bindInviteCode.value = ''
  bindInviterId.value = user.inviter_id ? String(user.inviter_id) : ''
  showBind.value = true
}

async function submitBind() {
  if (!bindUserId.value) return
  binding.value = true
  try {
    const body: { inviter_id?: number | null; invite_code?: string | null } = {}
    if (bindInviteCode.value.trim()) {
      body.invite_code = bindInviteCode.value.trim().toUpperCase()
    } else if (bindInviterId.value.trim()) {
      body.inviter_id = Number(bindInviterId.value)
    } else {
      body.inviter_id = null
      body.invite_code = null
    }
    const res = await api.adminBindInviter(bindUserId.value, body)
    toast(res.message)
    showBind.value = false
    await loadUsers()
  } catch (e) {
    toast(e instanceof Error ? e.message : '绑定失败')
  } finally {
    binding.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadUsers(), loadSettings()])
})
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>用户与邀请</h2>
        <p class="desc">管理用户邀请关系与注册设置</p>
      </div>
    </div>

    <div class="card" style="max-width:520px">
      <div class="card-head"><h3>注册设置</h3></div>
      <div class="card-body">
        <label class="agree">
          <input v-model="smsRequired" type="checkbox">
          <span>注册时必须短信验证码（关闭则仅需手机号+密码）</span>
        </label>
        <button type="button" class="btn btn-primary" :disabled="savingSettings" @click="saveSettings">
          {{ savingSettings ? '保存中…' : '保存设置' }}
        </button>
      </div>
    </div>

    <div class="filters">
      <input v-model="q" type="text" placeholder="搜索手机号 / 昵称 / 邀请码 / 邀请人…" @keyup.enter="loadUsers">
      <button type="button" class="btn btn-ghost" @click="loadUsers">搜索</button>
    </div>

    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <div v-else class="card only-table">
      <div class="card-head"><h3>用户列表（{{ users.length }}）</h3></div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>昵称</th>
              <th>手机号</th>
              <th>邀请码</th>
              <th>邀请人</th>
              <th class="num">受邀人数</th>
              <th class="action"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.nickname }}</td>
              <td class="mono">{{ u.phone }}</td>
              <td class="mono">{{ u.invite_code || '—' }}</td>
              <td>{{ u.inviter_nickname || '—' }}</td>
              <td class="num-cell">{{ u.invitee_count }}</td>
              <td class="action">
                <button type="button" class="btn btn-sm btn-ghost" @click="openBind(u)">绑定邀请人</button>
              </td>
            </tr>
            <tr v-if="!users.length">
              <td colspan="6"><div class="empty"><strong>暂无用户</strong></div></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="modal-bg" :class="{ open: showBind }" @click.self="showBind = false">
      <div class="modal">
        <h3>绑定邀请人</h3>
        <p class="modal-desc">填写邀请人用户 ID 或邀请码；两项都留空则解除绑定。</p>
        <div class="form-group">
          <label>邀请人用户 ID</label>
          <input v-model="bindInviterId" class="form-control mono" type="number" placeholder="例如 2">
        </div>
        <div class="form-group">
          <label>或邀请码</label>
          <input v-model="bindInviteCode" class="form-control mono" placeholder="8 位邀请码">
        </div>
        <div class="modal-foot">
          <button type="button" class="btn btn-ghost" @click="showBind = false">取消</button>
          <button type="button" class="btn btn-primary" :disabled="binding" @click="submitBind">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-desc { color: var(--t2); font-size: 13px; margin: -12px 0 16px; line-height: 1.6; }
</style>
