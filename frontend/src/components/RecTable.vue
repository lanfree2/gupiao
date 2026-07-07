<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { chipClass, fmtPct } from '@/api/client'
import { tagColor } from '@/utils/colors'
import { fmtDateShort, fmtPrice } from '@/utils/format'
import type { RecommendationOut } from '@/types/api'

const props = withDefaults(
  defineProps<{
    rows: RecommendationOut[]
    periods?: string[]
    showAction?: boolean
    from?: string
    emptyTitle?: string
    emptyDesc?: string
  }>(),
  {
    periods: () => [],
    showAction: true,
    from: 'tracking',
    emptyTitle: '暂无记录',
    emptyDesc: '',
  },
)

const router = useRouter()

const nodeLabels = computed(() => {
  if (props.periods.length) return props.periods
  const first = props.rows[0]
  return first?.nodes.map((n) => n.label) ?? []
})

function openDetail(id: number) {
  router.push({ path: `/recommendations/${id}`, query: { from: props.from } })
}

function chipAlpha(v: number | null | undefined) {
  if (v == null || v === 0) return undefined
  const a = 0.07 + Math.min(Math.abs(v) / 10, 1) * 0.2
  return { '--a': a.toFixed(2) } as Record<string, string>
}
</script>

<template>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>代码</th>
          <th>名称</th>
          <th>渠道</th>
          <th>推荐日</th>
          <th class="num">推荐价</th>
          <th v-for="label in nodeLabels" :key="label" class="num">{{ label }}</th>
          <th v-if="showAction" class="action"></th>
        </tr>
      </thead>
      <tbody v-if="rows.length">
        <tr
          v-for="row in rows"
          :key="row.id"
          class="clickable"
          @click="openDetail(row.id)"
        >
          <td><span class="code">{{ row.stock_code }}</span></td>
          <td>{{ row.stock_name }}</td>
          <td>
            <span class="tag" :style="{ '--tag-c': tagColor(row.channel_color) }">{{ row.channel_name }}</span>
          </td>
          <td class="td-date">{{ fmtDateShort(row.recommend_date) }}</td>
          <td class="price-cell">{{ fmtPrice(row.recommend_price) }}</td>
          <td v-for="(node, i) in row.nodes" :key="node.id ?? i" class="num-cell">
            <span
              v-if="node.status === 'done' && node.pct_change != null"
              class="chip"
              :class="chipClass(node.pct_change)"
              :style="chipAlpha(node.pct_change)"
            >{{ fmtPct(node.pct_change) }}</span>
            <span v-else class="chip flat">—</span>
          </td>
          <td v-if="showAction" class="action">
            <button class="btn btn-sm btn-ghost" @click.stop="openDetail(row.id)">详情</button>
          </td>
        </tr>
      </tbody>
      <tbody v-else>
        <tr>
          <td :colspan="5 + nodeLabels.length + (showAction ? 1 : 0)">
            <div class="empty">
              <strong>{{ emptyTitle }}</strong>
              <span v-if="emptyDesc">{{ emptyDesc }}</span>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
