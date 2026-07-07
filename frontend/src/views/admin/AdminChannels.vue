<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { tagColor } from '@/utils/colors'
import { fmtPctVal } from '@/utils/format'

interface AdminChannel {
  user_id: number
  user_nickname: string
  channel_id: number
  name: string
  color: string
  description: string
  record_count: number
  win_rate: number | null
  avg_return: number | null
}

const router = useRouter()
const q = ref('')
const rows = ref<AdminChannel[]>([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    rows.value = await api.adminChannels(q.value.trim() || undefined) as AdminChannel[]
  } finally {
    loading.value = false
  }
}

let timer: ReturnType<typeof setTimeout> | null = null
watch(q, () => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(load, 300)
})

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>全站渠道</h2>
        <p class="desc">用户 × 渠道维度的业绩统计</p>
      </div>
    </div>

    <div class="filters">
      <input v-model="q" type="text" placeholder="搜索用户 / 渠道名…">
      <span class="dim">共 {{ rows.length }} 个</span>
    </div>

    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <div v-else class="channel-grid">
      <div
        v-for="ch in rows"
        :key="ch.channel_id"
        class="ch-card"
        :style="{ '--ch-color': tagColor(ch.color) }"
        @click="router.push(`/admin/channels/${ch.channel_id}`)"
      >
        <div class="ch-name">{{ ch.name }}</div>
        <div class="admin-channel-cell">
          <span class="user-badge">{{ ch.user_nickname }}</span>
          <span class="owner">用户 ID {{ ch.user_id }}</span>
        </div>
        <div class="ch-desc">{{ ch.description || '—' }}</div>
        <div class="ch-stats-row">
          <span>追踪 <strong>{{ ch.record_count }}</strong> 只</span>
          <span>胜率 <strong>{{ ch.win_rate != null ? `${Math.round(ch.win_rate)}%` : '—' }}</strong></span>
          <span>均收益 <strong :class="ch.avg_return != null ? (ch.avg_return >= 0 ? 'up' : 'down') : ''">{{ fmtPctVal(ch.avg_return) }}</strong></span>
        </div>
        <div class="ch-foot"><span style="font-size:12px;color:var(--t3)">点击查看详情 →</span></div>
      </div>
      <div v-if="!rows.length" class="empty" style="grid-column:1/-1"><strong>暂无渠道</strong></div>
    </div>
  </div>
</template>
