<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api, chipClass, fmtPct } from '@/api/client'
import { tagColor } from '@/utils/colors'
import { fmtDateShort, fmtPrice } from '@/utils/format'
import type { RecommendationOut } from '@/types/api'

const route = useRoute()
const router = useRouter()
const rec = ref<RecommendationOut | null>(null)
const loading = ref(true)

const backPath = computed(() => {
  const from = route.query.from as string
  if (from === 'admin') return '/admin/records'
  if (from === 'search') return '/search'
  return '/tracking'
})

async function load() {
  loading.value = true
  try {
    rec.value = await api.getRec(Number(route.params.id)) as RecommendationOut
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <template v-else-if="rec">
      <div class="crumb">
        <a @click.prevent="router.push(backPath)">返回</a> / <span>{{ rec.stock_name }}</span>
      </div>
      <div class="title-row">
        <div>
          <h3>{{ rec.stock_name }} <span class="code">{{ rec.stock_code }}</span></h3>
          <div class="detail-badge-row">
            <span class="user-badge mine">我的推荐</span>
            <span class="tag" :style="{ '--tag-c': tagColor(rec.channel_color) }">{{ rec.channel_name }}</span>
          </div>
        </div>
        <span class="meta">{{ rec.recommend_date }} · ¥{{ fmtPrice(rec.recommend_price) }}</span>
      </div>

      <div class="card rail-card">
        <div class="rail">
          <div
            v-for="node in rec.nodes"
            :key="node.id"
            class="rail-node"
            :class="{ done: node.status === 'done' }"
          >
            <div class="rail-dot" />
            <div class="rl">{{ node.label }}</div>
            <div class="rd">{{ fmtDateShort(node.due_date) }}</div>
            <div
              v-if="node.status === 'done' && node.pct_change != null"
              class="rv"
              :class="chipClass(node.pct_change)"
            >{{ fmtPct(node.pct_change) }}</div>
            <div v-else class="rv pend">{{ node.status === 'pending' ? '待到期' : '—' }}</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-head"><h3>追踪节点明细</h3></div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>节点</th>
                <th>天数</th>
                <th>到期日</th>
                <th>状态</th>
                <th class="num">收盘价</th>
                <th class="num">涨跌幅</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="node in rec.nodes" :key="node.id">
                <td>{{ node.label }}</td>
                <td class="mono">{{ node.days }}天</td>
                <td class="td-date">{{ node.due_date }}</td>
                <td>{{ node.status === 'done' ? '已完成' : '待到期' }}</td>
                <td class="price-cell">{{ node.close_price != null ? fmtPrice(node.close_price) : '—' }}</td>
                <td class="num-cell">
                  <span
                    v-if="node.pct_change != null"
                    class="chip"
                    :class="chipClass(node.pct_change)"
                  >{{ fmtPct(node.pct_change) }}</span>
                  <span v-else class="chip flat">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="rec.reason" class="card">
        <div class="card-head"><h3>推荐理由</h3></div>
        <div class="card-body"><p>{{ rec.reason }}</p></div>
      </div>

      <RouterLink :to="backPath" class="btn btn-ghost">← 返回列表</RouterLink>
    </template>
  </div>
</template>
