<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '@/api/client'
import RecTable from '@/components/RecTable.vue'
import { tagColor } from '@/utils/colors'
import { fmtPctVal } from '@/utils/format'
import { toast } from '@/utils/toast'
import type { ChannelStatsOut, PeriodOut, RecommendationOut } from '@/types/api'

interface InviteeRow {
  id: number
  nickname: string
  phone_masked: string
  record_count: number
  channel_count: number
  created_at: string
  note: string
}

const inviteCode = ref('')
const invitePath = ref('')
const inviteeCount = ref(0)
const invitees = ref<InviteeRow[]>([])
const loading = ref(true)
const config = ref({ view_users: true, view_channels: true })

const selectedId = ref<number | null>(null)
const selectedChannelId = ref<number | null>(null)
const noteDraft = ref('')
const savingNote = ref(false)

const channels = ref<ChannelStatsOut[]>([])
const records = ref<RecommendationOut[]>([])
const detailLoading = ref(false)

const inviteUrl = computed(() => {
  if (!invitePath.value) return ''
  return `${window.location.origin}${invitePath.value}`
})

const selectedInvitee = computed(() => invitees.value.find((x) => x.id === selectedId.value))
const selectedChannel = computed(() => channels.value.find((x) => x.id === selectedChannelId.value))

async function load() {
  loading.value = true
  try {
    const cfg = await api.inviteConfig()
    config.value = cfg
    const me = await api.inviteMe()
    inviteCode.value = me.invite_code
    invitePath.value = me.invite_path
    inviteeCount.value = me.invitee_count
    if (cfg.view_channels) {
      invitees.value = await api.invitees() as InviteeRow[]
    } else {
      invitees.value = []
    }
  } catch (e) {
    toast(e instanceof Error ? e.message : '加载失败')
  } finally {
    loading.value = false
  }
}

async function copyLink() {
  if (!inviteUrl.value) return
  try {
    await navigator.clipboard.writeText(inviteUrl.value)
    toast('邀请链接已复制')
  } catch {
    toast('复制失败，请手动复制')
  }
}

async function selectInvitee(row: InviteeRow) {
  selectedId.value = row.id
  selectedChannelId.value = null
  noteDraft.value = row.note || ''
  records.value = []
  if (!config.value.view_channels) {
    channels.value = []
    return
  }
  detailLoading.value = true
  try {
    channels.value = await api.inviteeChannels(row.id) as ChannelStatsOut[]
  } catch (e) {
    toast(e instanceof Error ? e.message : '加载失败')
    selectedId.value = null
  } finally {
    detailLoading.value = false
  }
}

async function selectChannel(ch: ChannelStatsOut) {
  if (!selectedId.value) return
  selectedChannelId.value = ch.id
  detailLoading.value = true
  try {
    records.value = await api.inviteeChannelRecs(selectedId.value, ch.id) as RecommendationOut[]
  } catch (e) {
    toast(e instanceof Error ? e.message : '加载失败')
    selectedChannelId.value = null
  } finally {
    detailLoading.value = false
  }
}

async function saveNote() {
  if (!selectedId.value) return
  savingNote.value = true
  try {
    const res = await api.saveInviteeNote(selectedId.value, noteDraft.value)
    toast(res.message)
    const row = invitees.value.find((x) => x.id === selectedId.value)
    if (row) row.note = noteDraft.value
  } catch (e) {
    toast(e instanceof Error ? e.message : '保存失败')
  } finally {
    savingNote.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>我的邀请</h2>
        <p class="desc">分享邀请链接；查看受邀用户需管理员单独开通权限</p>
      </div>
    </div>

    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <template v-else>
      <div class="card">
        <div class="card-head"><h3>邀请链接</h3></div>
        <div class="card-body invite-box">
          <div class="invite-code">邀请码：<strong class="mono">{{ inviteCode }}</strong></div>
          <div class="invite-link mono">{{ inviteUrl }}</div>
          <button type="button" class="btn btn-primary" @click="copyLink">复制邀请链接</button>
          <p class="form-hint">好友通过链接注册后，将自动绑定为您的受邀用户（已邀请 {{ inviteeCount }} 人）</p>
        </div>
      </div>

      <div v-if="!config.view_channels" class="card">
        <div class="card-body">
          <p class="dim">您可分享上方邀请链接。查看受邀用户、备注与渠道数据需管理员在后台为您开通权限。</p>
        </div>
      </div>

      <div v-else class="grid-2 invite-grid">
        <div class="card only-table">
          <div class="card-head"><h3>受邀用户（{{ invitees.length }}）</h3></div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>昵称</th>
                  <th>手机</th>
                  <th>备注</th>
                  <th class="num">渠道</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in invitees"
                  :key="row.id"
                  class="clickable"
                  :class="{ active: selectedId === row.id }"
                  @click="selectInvitee(row)"
                >
                  <td>{{ row.nickname }}</td>
                  <td class="mono">{{ row.phone_masked }}</td>
                  <td class="note-cell">{{ row.note || '—' }}</td>
                  <td class="num-cell">{{ row.channel_count }}</td>
                </tr>
                <tr v-if="!invitees.length">
                  <td colspan="4"><div class="empty"><strong>暂无受邀用户</strong><span>分享上方链接邀请好友注册</span></div></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card invite-detail">
          <div class="card-head">
            <h3>{{ selectedInvitee ? selectedInvitee.nickname : '受邀用户详情' }}</h3>
          </div>
          <div v-if="!selectedId" class="card-body"><p class="dim">点击左侧用户，设置备注并查看其渠道</p></div>
          <template v-else>
            <div class="card-body note-block">
              <label class="sub-title">用户备注</label>
              <textarea v-model="noteDraft" class="form-control" rows="2" placeholder="给该用户写备注，方便识别" />
              <button type="button" class="btn btn-sm btn-primary" :disabled="savingNote" @click="saveNote">
                {{ savingNote ? '保存中…' : '保存备注' }}
              </button>
            </div>

            <div v-if="detailLoading && !selectedChannelId" class="empty"><strong>加载中…</strong></div>
            <div v-else class="card-body">
              <h4 class="sub-title">渠道（{{ channels.length }}）</h4>
              <div v-if="channels.length" class="channel-mini-list">
                <button
                  v-for="ch in channels"
                  :key="ch.id"
                  type="button"
                  class="channel-mini"
                  :class="{ active: selectedChannelId === ch.id }"
                  @click="selectChannel(ch)"
                >
                  <span class="tag" :style="{ '--tag-c': tagColor(ch.color) }">{{ ch.name }}</span>
                  <span class="dim">{{ ch.record_count }} 条 · 胜率 {{ ch.win_rate != null ? `${Math.round(ch.win_rate)}%` : '—' }} · 均收益 {{ fmtPctVal(ch.avg_return) }}</span>
                </button>
              </div>
              <p v-else class="dim">该用户暂无渠道</p>
            </div>

            <div v-if="selectedChannel" class="card only-table channel-records">
              <div class="card-head">
                <h3>{{ selectedChannel.name }} · 自选记录（{{ records.length }}）</h3>
              </div>
              <RecTable
                :rows="records"
                :show-delete="false"
                :show-action="false"
                from="invite"
                empty-title="该渠道暂无自选"
              />
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.invite-box { display: flex; flex-direction: column; gap: 12px; }
.invite-code { font-size: 14px; }
.invite-link { word-break: break-all; font-size: 13px; color: var(--t2); padding: 10px 12px; background: var(--surface-2); border-radius: var(--r-sm); border: 1px solid var(--border); }
.invite-grid { align-items: stretch; }
tr.active { background: var(--accent-dim); }
.note-cell { max-width: 120px; overflow: hidden; text-overflow: ellipsis; }
.sub-title { margin: 0 0 10px; font-size: 14px; font-weight: 600; display: block; }
.note-block { display: flex; flex-direction: column; gap: 10px; border-bottom: 1px solid var(--border); }
.channel-mini-list { display: flex; flex-direction: column; gap: 8px; }
.channel-mini { display: flex; flex-direction: column; gap: 4px; align-items: flex-start; text-align: left; padding: 10px 12px; border: 1px solid var(--border); border-radius: var(--r-sm); background: var(--surface); cursor: pointer; width: 100%; }
.channel-mini:hover, .channel-mini.active { background: var(--accent-dim); border-color: var(--accent); }
.channel-records { margin: 0; border-top: 1px solid var(--border); box-shadow: none; }
</style>
