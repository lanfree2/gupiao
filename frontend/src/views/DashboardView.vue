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
const selectedPeriod = ref('')

const periodLabels = computed(() => periods.value.map((p) => p.label))

const channelPeriodRows = computed(() => {
  if (!data.value || !selectedPeriod.value) return []
  return data.value.channel_period_stats.map((ch) => {
    const p = ch.periods.find((x) => x.label === selectedPeriod.value)
    return {
      name: ch.name,
      color: ch.color,
      record_count: ch.record_count,
      win_rate: p?.win_rate ?? null,
      avg_return: p?.avg_return ?? null,
      sample: p?.sample ?? 0,
    }
  })
})

async function load() {
  loading.value = true
  try {
    const [dash, ps] = await Promise.all([
      api.dashboard() as Promise<DashboardOut>,
      api.periods() as Promise<PeriodOut[]>,
    ])
    data.value = dash
    periods.value = ps
    if (!selectedPeriod.value && ps.length) {
      selectedPeriod.value = ps[0].label
    }
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
        <p class="desc">按周期对比各渠道胜率与收益</p>
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

      <div class="card">
        <div class="card-head">
          <h3>渠道周期分析</h3>
          <select v-model="selectedPeriod" class="form-control period-select">
            <option v-for="p in periods" :key="p.id" :value="p.label">{{ p.label }}</option>
          </select>
        </div>
        <div class="card-body">
          <template v-if="channelPeriodRows.length">
            <p class="dim section-desc">当前周期：<strong>{{ selectedPeriod }}</strong> · 各渠道胜率对比</p>
            <div v-for="ch in channelPeriodRows" :key="ch.name" class="bar-row">
              <span class="ch-name">
                <span class="tag" :style="{ '--tag-c': tagColor(ch.color) }">{{ ch.name }}</span>
              </span>
              <div class="bar">
                <i v-if="ch.win_rate != null" :style="{ width: `${ch.win_rate}%`, background: tagColor(ch.color) }" />
              </div>
              <span class="pctv">{{ ch.win_rate != null ? `${Math.round(ch.win_rate)}%` : '—' }}</span>
            </div>

            <p class="dim section-desc" style="margin-top:20px">各渠道平均收益（{{ selectedPeriod }}）</p>
            <div v-for="ch in channelPeriodRows" :key="`ar-${ch.name}`" class="bar-row">
              <span class="ch-name">
                <span class="tag" :style="{ '--tag-c': tagColor(ch.color) }">{{ ch.name }}</span>
              </span>
              <div class="bar">
                <i
                  v-if="ch.avg_return != null"
                  :style="{ width: `${Math.min(Math.abs(ch.avg_return) * 10, 100)}%`, background: tagColor(ch.color) }"
                />
              </div>
              <span
                class="pctv"
                :style="ch.avg_return != null ? { color: ch.avg_return >= 0 ? 'var(--up)' : 'var(--down)' } : {}"
              >{{ fmtPctVal(ch.avg_return) }}</span>
            </div>
            <p class="dim period-foot">{{ channelPeriodRows.map((c) => `${c.name} ${c.sample}样本`).join(' · ') }}</p>
          </template>
          <p v-else class="dim">暂无渠道数据</p>
        </div>
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
.period-select { min-width: 140px; padding: 8px 10px; font-size: 13px; }
.section-desc { margin: 0 0 12px; font-size: 13px; }
.ch-name { min-width: 100px; }
.period-foot { margin-top: 14px; font-size: 12px; }
.bar-row .tag { font-size: 12px; }
</style>
