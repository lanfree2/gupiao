<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/api/client'
import RecTable from '@/components/RecTable.vue'
import { tagColor } from '@/utils/colors'
import { fmtPctVal } from '@/utils/format'
import type { DashboardOut, PeriodOut } from '@/types/api'

const data = ref<DashboardOut | null>(null)
const periods = ref<PeriodOut[]>([])
const loading = ref(true)

const periodLabels = computed(() => periods.value.map((p) => p.label))

async function load() {
  loading.value = true
  try {
    const [dash, ps] = await Promise.all([
      api.dashboard() as Promise<DashboardOut>,
      api.periods() as Promise<PeriodOut[]>,
    ])
    data.value = dash
    periods.value = ps
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

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>我的总览</h2>
        <p class="desc">按渠道查看各周期表现</p>
      </div>
      <RouterLink to="/add" class="btn btn-primary">＋ 录入自选</RouterLink>
    </div>

    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <template v-else-if="data">
      <div class="stats">
        <div class="stat">
          <span class="label">我的追踪</span>
          <div class="num">{{ data.tracking_count }}</div>
          <div class="foot">当前追踪中的自选数</div>
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

      <div v-if="data.channel_period_stats.length" class="channel-period-grid">
        <div v-for="ch in data.channel_period_stats" :key="ch.name" class="card channel-period-card">
          <div class="card-head">
            <div class="ch-head-left">
              <span class="tag" :style="{ '--tag-c': tagColor(ch.color) }">{{ ch.name }}</span>
              <span class="dim ch-meta">{{ ch.record_count }} 条 · 胜率 {{ ch.win_rate != null ? `${Math.round(ch.win_rate)}%` : '—' }} · 均收益 {{ fmtPctVal(ch.avg_return) }}</span>
            </div>
          </div>
          <div class="card-body">
            <div v-for="p in ch.periods" :key="p.label" class="bar-row">
              <span>{{ p.label }}</span>
              <div class="bar">
                <i
                  v-if="p.avg_return != null"
                  :style="{ width: `${Math.min(Math.abs(p.avg_return) * 10, 100)}%`, background: tagColor(ch.color) }"
                />
              </div>
              <span class="pctv" :style="p.avg_return != null ? { color: p.avg_return >= 0 ? 'var(--up)' : 'var(--down)' } : {}">
                {{ fmtPctVal(p.avg_return) }}
              </span>
            </div>
            <p class="dim period-foot">{{ ch.periods.map((p) => `${p.label} ${p.sample}样本`).join(' · ') }}</p>
          </div>
        </div>
      </div>
      <div v-else class="card">
        <div class="card-body"><p class="dim">暂无渠道数据，先录入自选并创建渠道</p></div>
      </div>

      <div class="card only-table">
        <div class="card-head">
          <h3>最近录入</h3>
          <RouterLink to="/tracking">全部 →</RouterLink>
        </div>
        <RecTable
          :rows="data.recent"
          :periods="periodLabels"
          from="tracking"
          empty-title="暂无记录"
          empty-desc="录入第一条自选"
          @deleted="onDeleted"
        />
      </div>
    </template>
  </div>
</template>

<style scoped>
.channel-period-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 22px;
  margin-bottom: 22px;
}
.channel-period-card { margin-bottom: 0; }
.ch-head-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-start;
}
.ch-meta { font-size: 12px; }
.period-foot { margin-top: 12px; font-size: 12px; }
</style>
