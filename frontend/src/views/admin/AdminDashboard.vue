<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, chipClass, fmtPct } from '@/api/client'
import { tagColor } from '@/utils/colors'
import { fmtDateShort, fmtPrice } from '@/utils/format'
import type { RecommendationOut } from '@/types/api'

interface AdminDashboard {
  user_count: number
  record_count: number
  stock_count: number
  win_rate: number | null
  recent: (RecommendationOut & { user_nickname?: string; user_phone?: string })[]
}

const router = useRouter()
const data = ref<AdminDashboard | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    data.value = await api.adminDashboard() as AdminDashboard
  } finally {
    loading.value = false
  }
})

function openRec(id: number) {
  router.push(`/recommendations/${id}?from=admin`)
}
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>运营总览</h2>
        <p class="desc">全站用户与推荐数据概览</p>
      </div>
    </div>

    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <template v-else-if="data">
      <div class="admin-kpi-grid">
        <div class="stat"><span class="label">注册用户</span><div class="num">{{ data.user_count }}</div></div>
        <div class="stat"><span class="label">推荐记录</span><div class="num">{{ data.record_count }}</div></div>
        <div class="stat"><span class="label">涉及股票</span><div class="num">{{ data.stock_count }}</div></div>
        <div class="stat s-up"><span class="label">全站胜率</span><div class="num">{{ data.win_rate != null ? `${Math.round(data.win_rate)}%` : '—' }}</div></div>
      </div>

      <div class="card">
        <div class="card-head"><h3>最近录入</h3></div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>代码</th>
                <th>名称</th>
                <th>用户</th>
                <th>渠道</th>
                <th>推荐日</th>
                <th class="num">推荐价</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in data.recent" :key="r.id" class="clickable" @click="openRec(r.id)">
                <td><span class="code">{{ r.stock_code }}</span></td>
                <td>{{ r.stock_name }}</td>
                <td><span class="user-badge">{{ r.user_nickname }}</span></td>
                <td><span class="tag" :style="{ '--tag-c': tagColor(r.channel_color) }">{{ r.channel_name }}</span></td>
                <td class="td-date">{{ fmtDateShort(r.recommend_date) }}</td>
                <td class="price-cell">{{ fmtPrice(r.recommend_price) }}</td>
              </tr>
              <tr v-if="!data.recent.length">
                <td colspan="6"><div class="empty"><strong>暂无记录</strong></div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
