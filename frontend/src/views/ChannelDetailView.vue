<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { api } from '@/api/client'
import RecTable from '@/components/RecTable.vue'
import { tagColor } from '@/utils/colors'
import { fmtPctVal } from '@/utils/format'
import type { ChannelStatsOut, RecommendationOut } from '@/types/api'

interface ChannelDetail {
  channel: ChannelStatsOut
  stats: { record_count: number; win_rate: number | null; avg_return: number | null; stock_count: number }
  period_stats: { label: string; sample: number; win_rate: number | null; avg_return: number | null }[]
  records: RecommendationOut[]
}

const route = useRoute()
const detail = ref<ChannelDetail | null>(null)
const loading = ref(true)

const channelId = computed(() => Number(route.params.id))

async function load() {
  loading.value = true
  try {
    detail.value = await api.channelDetail(channelId.value) as ChannelDetail
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <template v-else-if="detail">
      <div class="crumb">
        <RouterLink to="/channels">我的渠道</RouterLink> / <span>{{ detail.channel.name }}</span>
      </div>
      <div class="cd-header">
        <div class="cd-color-dot" :style="{ background: tagColor(detail.channel.color) }" />
        <h2>{{ detail.channel.name }}</h2>
        <div class="cd-desc">{{ detail.channel.description || '—' }}</div>
      </div>

      <div class="stats">
        <div class="stat">
          <span class="label">推荐数</span>
          <div class="num">{{ detail.stats.record_count }}</div>
        </div>
        <div class="stat">
          <span class="label">涉及股票</span>
          <div class="num">{{ detail.stats.stock_count }}</div>
        </div>
        <div class="stat s-up">
          <span class="label">综合胜率</span>
          <div class="num">{{ detail.stats.win_rate != null ? `${Math.round(detail.stats.win_rate)}%` : '—' }}</div>
        </div>
        <div class="stat s-green">
          <span class="label">平均收益</span>
          <div class="num green">{{ fmtPctVal(detail.stats.avg_return) }}</div>
        </div>
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-head"><h3>各周期胜率</h3></div>
          <div class="card-body">
            <div v-for="ps in detail.period_stats" :key="ps.label" class="bar-row">
              <span>{{ ps.label }}</span>
              <div class="bar">
                <i v-if="ps.win_rate != null" :style="{ width: `${ps.win_rate}%`, background: tagColor(detail.channel.color) }" />
              </div>
              <span class="pctv">
                {{ ps.win_rate != null ? `${Math.round(ps.win_rate)}%` : '—' }}
                <small v-if="ps.sample" style="color:var(--t3);margin-left:4px">({{ ps.sample }})</small>
              </span>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-head"><h3>各周期平均收益</h3></div>
          <div class="card-body">
            <div v-for="ps in detail.period_stats" :key="ps.label" class="bar-row">
              <span>{{ ps.label }}</span>
              <div class="bar">
                <i
                  v-if="ps.avg_return != null"
                  :style="{ width: `${Math.min(Math.abs(ps.avg_return) * 10, 100)}%`, background: tagColor(detail.channel.color) }"
                />
              </div>
              <span class="pctv">{{ fmtPctVal(ps.avg_return) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card only-table">
        <div class="card-head"><h3>该渠道全部推荐</h3></div>
        <RecTable :rows="detail.records" from="tracking" />
      </div>

      <RouterLink to="/channels" class="btn btn-ghost">← 返回渠道列表</RouterLink>
    </template>
  </div>
</template>
