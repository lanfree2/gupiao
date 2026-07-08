<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '@/api/client'
import RecTable from '@/components/RecTable.vue'
import { tagColor } from '@/utils/colors'
import { fmtPctVal } from '@/utils/format'
import { toast } from '@/utils/toast'
import type { ChannelStatsOut, RecommendationOut } from '@/types/api'

interface InviteeRow {
  id: number
  nickname: string
  phone_masked: string
  record_count: number
  channel_count: number
  created_at: string
}

const inviteCode = ref('')
const invitePath = ref('')
const inviteeCount = ref(0)
const invitees = ref<InviteeRow[]>([])
const loading = ref(true)
const selectedId = ref<number | null>(null)
const channels = ref<ChannelStatsOut[]>([])
const records = ref<RecommendationOut[]>([])
const detailLoading = ref(false)

const inviteUrl = computed(() => {
  if (!invitePath.value) return ''
  const base = window.location.origin
  return `${base}${invitePath.value}`
})

async function load() {
  loading.value = true
  try {
    const [me, list] = await Promise.all([
      api.inviteMe(),
      api.invitees() as Promise<InviteeRow[]>,
    ])
    inviteCode.value = me.invite_code
    invitePath.value = me.invite_path
    inviteeCount.value = me.invitee_count
    invitees.value = list
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
  detailLoading.value = true
  try {
    const [chs, recs] = await Promise.all([
      api.inviteeChannels(row.id) as Promise<ChannelStatsOut[]>,
      api.inviteeRecommendations(row.id) as Promise<RecommendationOut[]>,
    ])
    channels.value = chs
    records.value = recs
  } catch (e) {
    toast(e instanceof Error ? e.message : '加载失败')
    selectedId.value = null
  } finally {
    detailLoading.value = false
  }
}

const selectedInvitee = computed(() => invitees.value.find((x) => x.id === selectedId.value))

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>我的邀请</h2>
        <p class="desc">分享邀请链接，查看受邀用户的渠道与推荐数据</p>
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

      <div class="grid-2">
        <div class="card only-table">
          <div class="card-head"><h3>受邀用户（{{ invitees.length }}）</h3></div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>昵称</th>
                  <th>手机</th>
                  <th class="num">渠道</th>
                  <th class="num">推荐</th>
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
                  <td class="num-cell">{{ row.channel_count }}</td>
                  <td class="num-cell">{{ row.record_count }}</td>
                </tr>
                <tr v-if="!invitees.length">
                  <td colspan="4"><div class="empty"><strong>暂无受邀用户</strong><span>分享上方链接邀请好友注册</span></div></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <h3>{{ selectedInvitee ? `${selectedInvitee.nickname} 的数据` : '选择用户查看' }}</h3>
          </div>
          <div v-if="!selectedId" class="card-body"><p class="dim">点击左侧用户查看其渠道与推荐</p></div>
          <div v-else-if="detailLoading" class="empty"><strong>加载中…</strong></div>
          <template v-else>
            <div class="card-body">
              <h4 class="sub-title">渠道（{{ channels.length }}）</h4>
              <div v-if="channels.length" class="channel-mini-list">
                <div v-for="ch in channels" :key="ch.id" class="channel-mini">
                  <span class="tag" :style="{ '--tag-c': tagColor(ch.color) }">{{ ch.name }}</span>
                  <span class="dim">{{ ch.record_count }} 条 · 胜率 {{ ch.win_rate != null ? `${Math.round(ch.win_rate)}%` : '—' }} · 均收益 {{ fmtPctVal(ch.avg_return) }}</span>
                </div>
              </div>
              <p v-else class="dim">暂无渠道</p>
            </div>
            <div class="card only-table" style="margin:0;border:0;box-shadow:none">
              <div class="card-head" style="border-top:1px solid var(--border)"><h3>推荐记录（{{ records.length }}）</h3></div>
              <RecTable :rows="records" :show-delete="false" :show-action="false" from="invite" empty-title="暂无推荐" />
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
tr.active { background: var(--accent-dim); }
.sub-title { margin: 0 0 10px; font-size: 14px; }
.channel-mini-list { display: flex; flex-direction: column; gap: 10px; }
.channel-mini { display: flex; flex-direction: column; gap: 4px; }
</style>
