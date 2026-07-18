<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { fmtPctVal } from '@/utils/format'

interface StockAgg {
  stock_code: string
  stock_name: string
  count: number
  user_count: number
  period_avgs: (number | null)[]
  period_labels: string[]
  win_rate: number | null
  avg_return: number | null
}

const router = useRouter()
const q = ref('')
const rows = ref<StockAgg[]>([])
const loading = ref(true)

const periodLabels = computed(() => rows.value[0]?.period_labels ?? [])

async function load() {
  loading.value = true
  try {
    rows.value = await api.adminStocks(q.value.trim() || undefined) as StockAgg[]
  } finally {
    loading.value = false
  }
}

let timer: ReturnType<typeof setTimeout> | null = null
watch(q, () => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(load, 300)
})

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>全站股票</h2>
        <p class="desc">按代码聚合的自选与各周期平均收益</p>
      </div>
    </div>

    <div class="filters">
      <input v-model="q" type="text" placeholder="搜索代码 / 名称…">
      <span class="dim">共 {{ rows.length }} 只</span>
    </div>

    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <div v-else class="card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>代码</th>
              <th>名称</th>
              <th class="num">自选次数</th>
              <th class="num">用户数</th>
              <th class="num">胜率</th>
              <th class="num">均收益</th>
              <th v-for="label in periodLabels" :key="label" class="num">{{ label }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="s in rows"
              :key="s.stock_code"
              class="clickable"
              @click="router.push(`/admin/stocks/${s.stock_code}`)"
            >
              <td><span class="code">{{ s.stock_code }}</span></td>
              <td>{{ s.stock_name }}</td>
              <td class="num-cell">{{ s.count }}</td>
              <td class="num-cell">{{ s.user_count }}</td>
              <td class="num-cell">{{ s.win_rate != null ? `${Math.round(s.win_rate)}%` : '—' }}</td>
              <td class="num-cell" :class="s.avg_return != null ? (s.avg_return >= 0 ? 'up' : 'down') : ''">{{ fmtPctVal(s.avg_return) }}</td>
              <td v-for="(avg, i) in s.period_avgs" :key="i" class="num-cell">{{ fmtPctVal(avg) }}</td>
            </tr>
            <tr v-if="!rows.length">
              <td :colspan="6 + periodLabels.length"><div class="empty"><strong>暂无数据</strong></div></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
