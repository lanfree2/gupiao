<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, chipClass, fmtPct } from '@/api/client'
import { tagColor } from '@/utils/colors'
import { fmtDateShort, fmtPrice } from '@/utils/format'
import type { RecommendationOut } from '@/types/api'

const router = useRouter()
const route = useRoute()
const q = ref('')
const scope = ref<'all' | 'stock' | 'channel' | 'user'>('all')
const rows = ref<RecommendationOut[]>([])
const loading = ref(false)

const scopes = [
  { key: 'all' as const, label: '全部' },
  { key: 'stock' as const, label: '按股票' },
  { key: 'channel' as const, label: '按渠道' },
  { key: 'user' as const, label: '按用户' },
]

async function load() {
  loading.value = true
  try {
    rows.value = await api.adminRecords(q.value.trim() || undefined, scope.value) as RecommendationOut[]
  } finally {
    loading.value = false
  }
}

let timer: ReturnType<typeof setTimeout> | null = null
watch([q, scope], () => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(load, 300)
})

onMounted(() => {
  const qq = route.query.q
  const qs = route.query.scope
  if (typeof qq === 'string' && qq.trim()) q.value = qq.trim()
  if (qs === 'stock' || qs === 'channel' || qs === 'user' || qs === 'all') scope.value = qs
  load()
})
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>自选记录</h2>
        <p class="desc">全站所有用户的自选记录</p>
      </div>
    </div>

    <div class="search-hero">
      <input v-model="q" type="text" placeholder="搜索代码、名称、渠道或用户…">
      <div class="search-tabs">
        <button
          v-for="s in scopes"
          :key="s.key"
          type="button"
          class="search-tab"
          :class="{ active: scope === s.key }"
          @click="scope = s.key"
        >{{ s.label }}</button>
      </div>
    </div>

    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <div v-else class="card">
      <div class="card-head"><h3>{{ q ? `搜索结果（${rows.length} 条）` : `全部记录（${rows.length} 条）` }}</h3></div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>代码</th>
              <th>名称</th>
              <th>渠道</th>
              <th>自选日</th>
              <th class="num">自选价</th>
              <th v-for="n in rows[0]?.nodes ?? []" :key="n.label" class="num">{{ n.label }}</th>
              <th class="action"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in rows"
              :key="r.id"
              class="clickable"
              @click="router.push(`/recommendations/${r.id}?from=admin`)"
            >
              <td><span class="code">{{ r.stock_code }}</span></td>
              <td>{{ r.stock_name }}</td>
              <td><span class="tag" :style="{ '--tag-c': tagColor(r.channel_color) }">{{ r.channel_name }}</span></td>
              <td class="td-date">{{ fmtDateShort(r.recommend_date) }}</td>
              <td class="price-cell">{{ fmtPrice(r.recommend_price) }}</td>
              <td v-for="node in r.nodes" :key="node.id" class="num-cell">
                <span v-if="node.pct_change != null" class="chip" :class="chipClass(node.pct_change)">{{ fmtPct(node.pct_change) }}</span>
                <span v-else class="chip flat">—</span>
              </td>
              <td class="action"><button type="button" class="btn btn-sm btn-ghost" @click.stop="router.push(`/recommendations/${r.id}?from=admin`)">详情</button></td>
            </tr>
            <tr v-if="!rows.length">
              <td :colspan="6 + (rows[0]?.nodes.length ?? 0)"><div class="empty"><strong>未找到记录</strong></div></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
