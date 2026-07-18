<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api } from '@/api/client'
import RecTable from '@/components/RecTable.vue'
import { tagColor } from '@/utils/colors'
import { fmtPctVal } from '@/utils/format'
import type { DashboardOut, PeriodOut, RecommendationOut } from '@/types/api'

interface UserInfo {
  id: number
  nickname: string
  phone: string
  invite_code: string | null
  created_at: string
}

interface UserDash extends DashboardOut {
  user: UserInfo
  periods: PeriodOut[]
}

const route = useRoute()
const router = useRouter()
const data = ref<UserDash | null>(null)
const loading = ref(true)
const selectedPeriod = ref('')
const error = ref('')

const userId = computed(() => Number(route.params.id))

const periodLabels = computed(() => (data.value?.periods || []).map((p) => p.label))

const channelPeriodRows = computed(() => {
  if (!data.value || !selectedPeriod.value) return []
  return data.value.channel_period_stats.map((ch) => {
    const p = ch.periods.find((x) => x.label === selectedPeriod.value)
    return {
      id: (ch as { id?: number }).id,
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
  if (!userId.value) return
  loading.value = true
  error.value = ''
  try {
    data.value = await api.adminUserDashboard(userId.value) as UserDash
    if (!selectedPeriod.value && data.value.periods?.length) {
      selectedPeriod.value = data.value.periods[0].label
    } else if (!selectedPeriod.value && data.value.period_stats.length) {
      selectedPeriod.value = data.value.period_stats[0].label
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
    data.value = null
  } finally {
    loading.value = false
  }
}

watch(userId, load)
onMounted(load)

function openChannel(ch: { id?: number }) {
  if (ch.id) router.push(`/admin/channels/${ch.id}`)
}
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <p class="crumb">
          <RouterLink to="/admin/users">用户与邀请</RouterLink> / <span>用户业绩</span>
        </p>
        <h2 v-if="data">{{ data.user.nickname }}</h2>
        <p v-if="data" class="desc mono">{{ data.user.phone }} · 邀请码 {{ data.user.invite_code || '—' }}</p>
      </div>
      <button type="button" class="btn btn-ghost" @click="router.push('/admin/users')">返回列表</button>
    </div>

    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <div v-else-if="error" class="empty"><strong>{{ error }}</strong></div>
    <template v-else-if="data">
      <div class="stats">
        <div class="stat">
          <span class="label">自选追踪</span>
          <div class="num">{{ data.tracking_count }}</div>
          <div class="foot">该用户当前自选数</div>
        </div>
        <div class="stat">
          <span class="label">综合胜率</span>
          <div class="num">{{ data.win_rate != null ? `${Math.round(data.win_rate)}%` : '—' }}</div>
          <div class="foot">已到期节点上涨占比</div>
        </div>
        <div class="stat s-up">
          <span class="label">平均收益</span>
          <div class="num up">{{ fmtPctVal(data.avg_return) }}</div>
          <div class="foot">全部已到期节点均值</div>
        </div>
        <div class="stat s-warn">
          <span class="label">待抓取节点</span>
          <div class="num warn">{{ data.pending_nodes }}</div>
          <div class="foot">到期后自动抓取收盘价</div>
        </div>
      </div>

      <div class="card">
        <div class="card-head">
          <h3>各周期表现</h3>
        </div>
        <div class="card-body">
          <div v-if="data.period_stats.length" class="period-grid">
            <div v-for="p in data.period_stats" :key="p.label" class="period-card">
              <strong>{{ p.label }}</strong>
              <div class="dim">样本 {{ p.sample }}</div>
              <div>胜率 {{ p.win_rate != null ? `${Math.round(p.win_rate)}%` : '—' }}</div>
              <div :class="p.avg_return != null ? (p.avg_return >= 0 ? 'up' : 'down') : ''">均收益 {{ fmtPctVal(p.avg_return) }}</div>
            </div>
          </div>
          <p v-else class="dim">暂无周期数据</p>
        </div>
      </div>

      <div class="card">
        <div class="card-head">
          <h3>渠道周期分析</h3>
          <select v-model="selectedPeriod" class="form-control period-select">
            <option v-for="p in (data.periods.length ? data.periods : data.period_stats)" :key="p.label" :value="p.label">
              {{ p.label }}
            </option>
          </select>
        </div>
        <div class="card-body">
          <template v-if="channelPeriodRows.length">
            <p class="dim section-desc">当前周期：<strong>{{ selectedPeriod }}</strong> · 各渠道胜率对比</p>
            <div
              v-for="ch in channelPeriodRows"
              :key="ch.name"
              class="bar-row clickable-row"
              @click="openChannel(ch)"
            >
              <span class="ch-name">
                <span class="tag" :style="{ '--tag-c': tagColor(ch.color) }">{{ ch.name }}</span>
              </span>
              <div class="bar">
                <i v-if="ch.win_rate != null" :style="{ width: `${ch.win_rate}%`, background: tagColor(ch.color) }" />
              </div>
              <span class="pctv">{{ ch.win_rate != null ? `${Math.round(ch.win_rate)}%` : '—' }}</span>
            </div>

            <p class="dim section-desc" style="margin-top:20px">各渠道平均收益（{{ selectedPeriod }}）</p>
            <div
              v-for="ch in channelPeriodRows"
              :key="`ar-${ch.name}`"
              class="bar-row clickable-row"
              @click="openChannel(ch)"
            >
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
            <p class="dim period-foot">{{ channelPeriodRows.map((c) => `${c.name} ${c.sample}样本`).join(' · ') }} · 点击渠道可看详情</p>
          </template>
          <p v-else class="dim">该用户暂无渠道数据</p>
        </div>
      </div>

      <div class="card only-table">
        <div class="card-head">
          <h3>最近自选</h3>
          <RouterLink :to="`/admin/records?q=${encodeURIComponent(data.user.nickname)}&scope=user`">全部记录 →</RouterLink>
        </div>
        <RecTable
          :rows="data.recent as RecommendationOut[]"
          :periods="periodLabels"
          :show-delete="false"
          from="admin"
          empty-title="暂无记录"
        />
      </div>
    </template>
  </div>
</template>

<style scoped>
.crumb { font-size: 13px; color: var(--t3); margin: 0 0 6px; }
.crumb a { color: var(--accent); text-decoration: none; }
.period-select { min-width: 140px; padding: 8px 10px; font-size: 13px; }
.section-desc { margin: 0 0 12px; font-size: 13px; }
.ch-name { min-width: 100px; }
.period-foot { margin-top: 14px; font-size: 12px; }
.period-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
.period-card { padding: 12px; border: 1px solid var(--border); border-radius: var(--r-sm); background: var(--surface-2); display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
.clickable-row { cursor: pointer; }
.clickable-row:hover { opacity: 0.9; }
</style>
