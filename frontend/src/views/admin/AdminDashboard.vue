<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { api } from '@/api/client'
import { tagColor } from '@/utils/colors'
import { fmtDateShort, fmtPctVal, fmtPrice } from '@/utils/format'
import type { RecommendationOut } from '@/types/api'

interface PeriodStat {
  label: string
  sample: number
  win_rate: number | null
  avg_return: number | null
}

interface UserRank {
  user_id: number
  nickname: string
  phone: string
  record_count: number
  channel_count: number
  stock_count: number
  win_rate: number | null
  avg_return: number | null
  pending_nodes: number
}

interface ChannelRank {
  channel_id: number
  name: string
  color: string
  user_id: number
  user_nickname: string
  record_count: number
  win_rate: number | null
  avg_return: number | null
}

interface AdminDashboard {
  user_count: number
  record_count: number
  stock_count: number
  channel_count: number
  win_rate: number | null
  avg_return: number | null
  pending_nodes: number
  period_stats: PeriodStat[]
  user_rank: UserRank[]
  channel_rank: ChannelRank[]
  recent: (RecommendationOut & { user_nickname?: string; user_phone?: string })[]
}

const router = useRouter()
const data = ref<AdminDashboard | null>(null)
const loading = ref(true)
const selectedPeriod = ref('')

const periodRows = computed(() => data.value?.period_stats ?? [])

onMounted(async () => {
  try {
    data.value = await api.adminDashboard() as AdminDashboard
    if (data.value.period_stats.length) {
      selectedPeriod.value = data.value.period_stats[0].label
    }
  } finally {
    loading.value = false
  }
})

function openRec(id: number) {
  router.push(`/recommendations/${id}?from=admin`)
}

const selectedPeriodStat = computed(() =>
  periodRows.value.find((p) => p.label === selectedPeriod.value) || null,
)
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>运营总览</h2>
        <p class="desc">全站多维度业绩：用户 / 渠道 / 周期</p>
      </div>
    </div>

    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <template v-else-if="data">
      <div class="admin-kpi-grid">
        <div class="stat"><span class="label">注册用户</span><div class="num">{{ data.user_count }}</div><div class="foot">普通用户数</div></div>
        <div class="stat"><span class="label">自选记录</span><div class="num">{{ data.record_count }}</div><div class="foot">全站录入条数</div></div>
        <div class="stat"><span class="label">涉及股票</span><div class="num">{{ data.stock_count }}</div><div class="foot">{{ data.channel_count }} 个渠道</div></div>
        <div class="stat s-up"><span class="label">全站胜率</span><div class="num">{{ data.win_rate != null ? `${Math.round(data.win_rate)}%` : '—' }}</div><div class="foot">已到期节点上涨占比</div></div>
        <div class="stat s-up"><span class="label">平均收益</span><div class="num up">{{ fmtPctVal(data.avg_return) }}</div><div class="foot">全部已到期节点均值</div></div>
        <div class="stat s-warn"><span class="label">待抓取节点</span><div class="num warn">{{ data.pending_nodes }}</div><div class="foot">已到期未完成抓取</div></div>
      </div>

      <div class="card">
        <div class="card-head">
          <h3>各周期全站表现</h3>
          <select v-if="periodRows.length" v-model="selectedPeriod" class="form-control period-select">
            <option v-for="p in periodRows" :key="p.label" :value="p.label">{{ p.label }}</option>
          </select>
        </div>
        <div class="card-body">
          <template v-if="selectedPeriodStat">
            <div class="period-kpi">
              <div><span class="dim">样本</span><strong>{{ selectedPeriodStat.sample }}</strong></div>
              <div><span class="dim">胜率</span><strong>{{ selectedPeriodStat.win_rate != null ? `${Math.round(selectedPeriodStat.win_rate)}%` : '—' }}</strong></div>
              <div><span class="dim">均收益</span><strong :class="selectedPeriodStat.avg_return != null ? (selectedPeriodStat.avg_return >= 0 ? 'up' : 'down') : ''">{{ fmtPctVal(selectedPeriodStat.avg_return) }}</strong></div>
            </div>
            <div class="period-bars">
              <div v-for="p in periodRows" :key="p.label" class="bar-row">
                <span class="ch-name">{{ p.label }}</span>
                <div class="bar">
                  <i v-if="p.win_rate != null" :style="{ width: `${p.win_rate}%`, background: 'var(--accent)' }" />
                </div>
                <span class="pctv">{{ p.win_rate != null ? `${Math.round(p.win_rate)}%` : '—' }}</span>
                <span class="pctv" :class="p.avg_return != null ? (p.avg_return >= 0 ? 'up' : 'down') : ''">{{ fmtPctVal(p.avg_return) }}</span>
              </div>
            </div>
          </template>
          <p v-else class="dim">暂无周期数据</p>
        </div>
      </div>

      <div class="grid-2">
        <div class="card only-table">
          <div class="card-head">
            <h3>用户业绩排行</h3>
            <RouterLink to="/admin/users">全部用户 →</RouterLink>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>用户</th>
                  <th class="num">自选</th>
                  <th class="num">胜率</th>
                  <th class="num">均收益</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="u in data.user_rank"
                  :key="u.user_id"
                  class="clickable"
                  @click="router.push(`/admin/users/${u.user_id}`)"
                >
                  <td>
                    <strong>{{ u.nickname }}</strong>
                    <div class="mono dim tiny">{{ u.phone }}</div>
                  </td>
                  <td class="num-cell">{{ u.record_count }}</td>
                  <td class="num-cell">{{ u.win_rate != null ? `${Math.round(u.win_rate)}%` : '—' }}</td>
                  <td class="num-cell" :class="u.avg_return != null ? (u.avg_return >= 0 ? 'up' : 'down') : ''">{{ fmtPctVal(u.avg_return) }}</td>
                </tr>
                <tr v-if="!data.user_rank.length">
                  <td colspan="4"><div class="empty"><strong>暂无用户业绩</strong></div></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card only-table">
          <div class="card-head">
            <h3>渠道业绩排行</h3>
            <RouterLink to="/admin/channels">全部渠道 →</RouterLink>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>渠道</th>
                  <th>所属用户</th>
                  <th class="num">自选</th>
                  <th class="num">胜率</th>
                  <th class="num">均收益</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="ch in data.channel_rank"
                  :key="ch.channel_id"
                  class="clickable"
                  @click="router.push(`/admin/channels/${ch.channel_id}`)"
                >
                  <td><span class="tag" :style="{ '--tag-c': tagColor(ch.color) }">{{ ch.name }}</span></td>
                  <td>
                    <a class="linkish" @click.stop="router.push(`/admin/users/${ch.user_id}`)">{{ ch.user_nickname }}</a>
                  </td>
                  <td class="num-cell">{{ ch.record_count }}</td>
                  <td class="num-cell">{{ ch.win_rate != null ? `${Math.round(ch.win_rate)}%` : '—' }}</td>
                  <td class="num-cell" :class="ch.avg_return != null ? (ch.avg_return >= 0 ? 'up' : 'down') : ''">{{ fmtPctVal(ch.avg_return) }}</td>
                </tr>
                <tr v-if="!data.channel_rank.length">
                  <td colspan="5"><div class="empty"><strong>暂无渠道业绩</strong></div></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-head">
          <h3>最近录入</h3>
          <RouterLink to="/admin/records">全部记录 →</RouterLink>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>代码</th>
                <th>名称</th>
                <th>用户</th>
                <th>渠道</th>
                <th>自选日</th>
                <th class="num">自选价</th>
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

<style scoped>
.period-select { min-width: 120px; padding: 8px 10px; font-size: 13px; }
.period-kpi { display: flex; gap: 24px; margin-bottom: 16px; flex-wrap: wrap; }
.period-kpi > div { display: flex; flex-direction: column; gap: 4px; }
.period-bars .ch-name { min-width: 64px; }
.tiny { font-size: 12px; margin-top: 2px; }
.linkish { color: var(--accent); cursor: pointer; text-decoration: none; }
.linkish:hover { text-decoration: underline; }
.admin-kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; margin-bottom: 18px; }
</style>
