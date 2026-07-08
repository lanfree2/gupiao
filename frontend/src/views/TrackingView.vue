<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { api } from '@/api/client'
import RecTable from '@/components/RecTable.vue'
import type { ChannelStatsOut, RecommendationOut } from '@/types/api'

const route = useRoute()
const rows = ref<RecommendationOut[]>([])
const channels = ref<ChannelStatsOut[]>([])
const q = ref('')
const channelId = ref('')
const loading = ref(true)

const filtered = computed(() => {
  let list = [...rows.value]
  if (channelId.value) {
    const id = Number(channelId.value)
    list = list.filter((r) => r.channel_id === id)
  }
  if (q.value.trim()) {
    const ql = q.value.trim().toLowerCase()
    list = list.filter(
      (r) =>
        r.stock_code.includes(ql) ||
        r.stock_name.toLowerCase().includes(ql) ||
        r.channel_name.toLowerCase().includes(ql),
    )
  }
  return list.sort((a, b) => b.recommend_date.localeCompare(a.recommend_date))
})

async function load() {
  loading.value = true
  try {
    const [recs, chs] = await Promise.all([
      api.recommendations() as Promise<RecommendationOut[]>,
      api.channels() as Promise<ChannelStatsOut[]>,
    ])
    rows.value = recs
    channels.value = chs
  } finally {
    loading.value = false
  }
}

function onDeleted(id: number) {
  rows.value = rows.value.filter((r) => r.id !== id)
  load()
}

onMounted(() => {
  const ch = route.query.channel
  if (typeof ch === 'string' && ch) channelId.value = ch
  load()
})

watch(
  () => route.query.channel,
  (ch) => {
    channelId.value = typeof ch === 'string' ? ch : ''
  },
)
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
      <div class="card-head">
        <h3>历史推荐记录</h3>
        <RouterLink v-if="!filtered.length && rows.length" to="/add" class="btn btn-sm btn-primary">录入推荐</RouterLink>
      </div>
      <RecTable
        :rows="filtered"
        from="tracking"
        :empty-title="rows.length ? '未找到匹配记录' : '暂无历史记录'"
        :empty-desc="rows.length ? '试试调整筛选条件' : '录入第一条推荐后开始追踪'"
        @deleted="onDeleted"
      />
    </div>
    <p class="foot-note">点击查看详情 · 红涨绿跌</p>
  </div>
</template>
