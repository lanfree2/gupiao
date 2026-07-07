<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/api/client'
import RecTable from '@/components/RecTable.vue'
import type { ChannelStatsOut, RecommendationOut } from '@/types/api'

const rows = ref<RecommendationOut[]>([])
const channels = ref<ChannelStatsOut[]>([])
const q = ref('')
const channelId = ref('')
const loading = ref(true)

const filtered = computed(() => {
  let list = rows.value
  if (channelId.value) {
    const id = Number(channelId.value)
    list = list.filter((r) => r.channel_id === id)
  }
  if (q.value.trim()) {
    const ql = q.value.trim()
    list = list.filter((r) => r.stock_code.includes(ql) || r.stock_name.includes(ql))
  }
  return list
})

async function load() {
  loading.value = true
  try {
    const params = q.value.trim() ? `?q=${encodeURIComponent(q.value.trim())}` : ''
    const [recs, chs] = await Promise.all([
      api.recommendations(params) as Promise<RecommendationOut[]>,
      api.channels() as Promise<ChannelStatsOut[]>,
    ])
    rows.value = recs
    channels.value = chs
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(q, () => load())
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>我的追踪</h2>
        <p class="desc">我录入的全部推荐记录</p>
      </div>
      <RouterLink to="/add" class="btn btn-primary">＋ 录入推荐</RouterLink>
    </div>

    <div class="filters">
      <input v-model="q" type="text" placeholder="搜索代码 / 名称…">
      <select v-model="channelId">
        <option value="">全部渠道</option>
        <option v-for="ch in channels" :key="ch.id" :value="String(ch.id)">{{ ch.name }}</option>
      </select>
      <span class="dim">共 {{ filtered.length }} 条</span>
    </div>

    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <div v-else class="card only-table">
      <RecTable :rows="filtered" from="tracking" empty-title="未找到记录" @deleted="load" />
    </div>
    <p class="foot-note">点击查看详情 · 红涨绿跌</p>
  </div>
</template>
