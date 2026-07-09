<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api, chipClass, fmtPct } from '@/api/client'
import { tagColor } from '@/utils/colors'
import { fmtDateShort, fmtPctVal, fmtPrice } from '@/utils/format'
import type { RecommendationOut } from '@/types/api'

interface StockDetail {
  stock_code: string
  stock_name: string
  count: number
  user_count: number
  win_rate: number | null
  avg_return: number | null
  period_stats: { label: string; sample: number; win_rate: number | null; avg_return: number | null }[]
  records: (RecommendationOut & { user_nickname?: string; user_id?: number })[]
}

const route = useRoute()
const router = useRouter()
const detail = ref<StockDetail | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    detail.value = await api.adminStock(String(route.params.code)) as StockDetail
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page">
    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <template v-else-if="detail">
      <div class="crumb">
        <RouterLink to="/admin/stocks">全站股票</RouterLink> / <span>{{ detail.stock_name }}</span>
      </div>
      <div class="title-row">
        <div>
          <h3>{{ detail.stock_name }} <span class="code">{{ detail.stock_code }}</span></h3>
        </div>
        <span class="meta">被自选 {{ detail.count }} 次 · {{ detail.user_count }} 位用户</span>
      </div>

      <div class="stats">
        <div class="stat s-up">
          <span class="label">综合胜率</span>
          <div class="num">{{ detail.win_rate != null ? `${Math.round(detail.win_rate)}%` : '—' }}</div>
        </div>
        <div class="stat s-green">
          <span class="label">平均收益</span>
          <div class="num green">{{ fmtPctVal(detail.avg_return) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-head"><h3>各周期表现</h3></div>
        <div class="card-body">
          <table class="period-matrix">
            <thead>
              <tr>
                <th>周期</th>
                <th>样本</th>
                <th>胜率</th>
                <th>均收益</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ps in detail.period_stats" :key="ps.label">
                <td>{{ ps.label }}</td>
                <td>{{ ps.sample }}</td>
                <td>{{ ps.win_rate != null ? `${Math.round(ps.win_rate)}%` : '—' }}</td>
                <td :class="ps.avg_return != null ? (ps.avg_return >= 0 ? 'pm-up' : 'pm-down') : 'pm-dim'">
                  {{ fmtPctVal(ps.avg_return) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-head"><h3>全部自选记录</h3></div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>用户</th>
                <th>渠道</th>
                <th>自选日</th>
                <th class="num">自选价</th>
                <th v-for="n in detail.records[0]?.nodes ?? []" :key="n.label" class="num">{{ n.label }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="r in detail.records"
                :key="r.id"
                class="clickable"
                @click="router.push(`/recommendations/${r.id}?from=admin`)"
              >
                <td><span class="user-badge">{{ r.user_nickname }}</span></td>
                <td><span class="tag" :style="{ '--tag-c': tagColor(r.channel_color) }">{{ r.channel_name }}</span></td>
                <td class="td-date">{{ fmtDateShort(r.recommend_date) }}</td>
                <td class="price-cell">{{ fmtPrice(r.recommend_price) }}</td>
                <td v-for="node in r.nodes" :key="node.id" class="num-cell">
                  <span v-if="node.pct_change != null" class="chip" :class="chipClass(node.pct_change)">{{ fmtPct(node.pct_change) }}</span>
                  <span v-else class="chip flat">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <RouterLink to="/admin/stocks" class="btn btn-ghost">← 返回股票列表</RouterLink>
    </template>
  </div>
</template>
