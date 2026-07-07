<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api, chipClass, fmtPct } from '@/api/client'
import { tagColor } from '@/utils/colors'
import { fmtDateShort, fmtPctVal, fmtPrice } from '@/utils/format'
import type { RecommendationOut } from '@/types/api'

interface AdminChannelDetail {
  channel: { id: number; name: string; color: string; description: string; user_id: number; user_nickname: string }
  stats: { record_count: number; win_rate: number | null; avg_return: number | null; stock_count: number }
  period_stats: { label: string; sample: number; wins: number; win_rate: number | null; avg_return: number | null; max_up: number | null; max_down: number | null }[]
  records: RecommendationOut[]
}

const route = useRoute()
const router = useRouter()
const detail = ref<AdminChannelDetail | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    detail.value = await api.adminChannel(Number(route.params.id)) as AdminChannelDetail
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
        <RouterLink to="/admin/channels">全站渠道</RouterLink> / <span>{{ detail.channel.name }}</span>
      </div>
      <div class="cd-header">
        <div class="cd-color-dot" :style="{ background: tagColor(detail.channel.color) }" />
        <h2>{{ detail.channel.name }}</h2>
        <div class="cd-desc">{{ detail.channel.user_nickname }} · {{ detail.channel.description || '—' }}</div>
      </div>

      <div class="stats">
        <div class="stat"><span class="label">推荐数</span><div class="num">{{ detail.stats.record_count }}</div></div>
        <div class="stat"><span class="label">涉及股票</span><div class="num">{{ detail.stats.stock_count }}</div></div>
        <div class="stat s-up"><span class="label">胜率</span><div class="num">{{ detail.stats.win_rate != null ? `${Math.round(detail.stats.win_rate)}%` : '—' }}</div></div>
        <div class="stat s-green"><span class="label">均收益</span><div class="num green">{{ fmtPctVal(detail.stats.avg_return) }}</div></div>
      </div>

      <div class="card">
        <div class="card-head"><h3>分周期业绩矩阵</h3></div>
        <div class="card-body">
          <table class="period-matrix">
            <thead>
              <tr>
                <th>周期</th>
                <th>样本</th>
                <th>胜场</th>
                <th>胜率</th>
                <th>均收益</th>
                <th>最大涨</th>
                <th>最大跌</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ps in detail.period_stats" :key="ps.label">
                <td>{{ ps.label }}</td>
                <td>{{ ps.sample }}</td>
                <td>{{ ps.wins }}</td>
                <td>{{ ps.win_rate != null ? `${Math.round(ps.win_rate)}%` : '—' }}</td>
                <td :class="ps.avg_return != null ? (ps.avg_return >= 0 ? 'pm-up' : 'pm-down') : 'pm-dim'">{{ fmtPctVal(ps.avg_return) }}</td>
                <td class="pm-up">{{ fmtPctVal(ps.max_up) }}</td>
                <td class="pm-down">{{ fmtPctVal(ps.max_down) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-head"><h3>全部推荐</h3></div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>代码</th>
                <th>名称</th>
                <th>推荐日</th>
                <th class="num">推荐价</th>
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
                <td><span class="code">{{ r.stock_code }}</span></td>
                <td>{{ r.stock_name }}</td>
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

      <RouterLink to="/admin/channels" class="btn btn-ghost">← 返回渠道列表</RouterLink>
    </template>
  </div>
</template>
