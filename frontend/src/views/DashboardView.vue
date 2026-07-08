<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/api/client'
import RecTable from '@/components/RecTable.vue'
import { tagColor } from '@/utils/colors'
import { fmtPctVal } from '@/utils/format'
import type { DashboardOut } from '@/types/api'

const data = ref<DashboardOut | null>(null)
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    data.value = await api.dashboard() as DashboardOut
  } finally {
    loading.value = false
  }
}

function onDeleted(id: number) {
  if (data.value) {
    data.value.recent = data.value.recent.filter((r) => r.id !== id)
    data.value.tracking_count = Math.max(0, data.value.tracking_count - 1)
  }
  load()
}

const recentPeriods = computed(() => {
  const first = data.value?.recent[0]
  if (!first?.nodes.length) return []
  const nodes = first.nodes
  const pick = [0, Math.min(2, nodes.length - 1), nodes.length - 1].filter((v, i, a) => a.indexOf(v) === i)
  return pick.map((i) => nodes[i].label)
})

const recentRows = computed(() => {
  if (!data.value) return []
  return data.value.recent.map((r) => {
    const nodes = r.nodes
    const pick = [0, Math.min(2, nodes.length - 1), nodes.length - 1].filter((v, i, a) => a.indexOf(v) === i)
    return { ...r, nodes: pick.map((i) => nodes[i]) }
  })
})

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>我的总览</h2>
        <p class="desc">我录入的推荐与渠道表现</p>
      </div>
      <RouterLink to="/add" class="btn btn-primary">＋ 录入推荐</RouterLink>
    </div>

    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <template v-else-if="data">
      <div class="stats">
        <div class="stat">
          <span class="label">我的追踪</span>
          <div class="num">{{ data.tracking_count }}</div>
          <div class="foot">当前追踪中的推荐数</div>
        </div>
        <div class="stat">
          <span class="label">综合胜率</span>
          <div class="num">{{ data.win_rate != null ? `${Math.round(data.win_rate)}%` : '—' }}</div>
          <div class="foot">已到期节点中上涨占比</div>
        </div>
        <div class="stat s-up">
          <span class="label">平均收益</span>
          <div class="num up">{{ fmtPctVal(data.avg_return) }}</div>
          <div class="foot">全部已到期节点均值</div>
        </div>
        <div class="stat s-warn">
          <span class="label">待到期节点</span>
          <div class="num warn">{{ data.pending_nodes }}</div>
          <div class="foot">到期后自动抓取收盘价</div>
        </div>
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-head"><h3>渠道胜率对比</h3></div>
          <div class="card-body">
            <template v-if="data.channel_win_rates.length">
              <div v-for="ch in data.channel_win_rates" :key="ch.name" class="bar-row">
                <span>{{ ch.name }}</span>
                <div class="bar">
                  <i v-if="ch.win_rate != null" :style="{ width: `${ch.win_rate}%`, background: tagColor(ch.color) }" />
                </div>
                <span class="pctv">{{ ch.win_rate != null ? `${Math.round(ch.win_rate)}%` : '—' }}</span>
              </div>
            </template>
            <p v-else class="dim">暂无数据</p>
          </div>
        </div>
        <div class="card">
          <div class="card-head"><h3>渠道平均收益对比</h3></div>
          <div class="card-body">
            <template v-if="data.channel_avg_returns.length">
              <div v-for="ch in data.channel_avg_returns" :key="ch.name" class="bar-row">
                <span>{{ ch.name }}</span>
                <div class="bar">
                  <i
                    v-if="ch.avg_return != null"
                    :style="{ width: `${Math.min(Math.abs(ch.avg_return) * 10, 100)}%`, background: tagColor(ch.color) }"
                  />
                </div>
                <span class="pctv" :style="ch.avg_return != null ? { color: ch.avg_return >= 0 ? 'var(--up)' : 'var(--down)' } : {}">
                  {{ fmtPctVal(ch.avg_return) }}
                </span>
              </div>
            </template>
            <p v-else class="dim">暂无数据</p>
          </div>
        </div>
      </div>

      <div class="card only-table">
        <div class="card-head">
          <h3>最近录入</h3>
          <RouterLink to="/tracking">全部 →</RouterLink>
        </div>
        <RecTable :rows="recentRows" :periods="recentPeriods" from="tracking" empty-title="暂无记录" empty-desc="录入第一条推荐" @deleted="onDeleted" />
      </div>
    </template>
  </div>
</template>
