<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, chipClass, fmtPct } from '@/api/client'
import { tagColor } from '@/utils/colors'
import { fmtDateShort, fmtPrice, isDueDateReached, sortNodesByDueDate } from '@/utils/format'
import { toast } from '@/utils/toast'
import type { RecommendationOut } from '@/types/api'

const props = withDefaults(
  defineProps<{
    rows: RecommendationOut[]
    periods?: string[]
    showAction?: boolean
    showDelete?: boolean
    from?: string
    emptyTitle?: string
    emptyDesc?: string
  }>(),
  {
    periods: () => [],
    showAction: true,
    showDelete: true,
    from: 'tracking',
    emptyTitle: '暂无记录',
    emptyDesc: '',
  },
)

const emit = defineEmits<{ deleted: [id: number] }>()

const router = useRouter()
const deletingId = ref<number | null>(null)

const nodeLabels = computed(() => {
  if (props.periods.length) return props.periods
  const first = props.rows[0]
  return first?.nodes.map((n) => n.label) ?? []
})

const miniLabelIndices = computed(() => {
  const pl = nodeLabels.value.length
  if (!pl) return []
  return [...new Set([0, Math.min(2, pl - 1), pl - 1])]
})

function latestDoneNode(row: RecommendationOut) {
  const sorted = sortNodesByDueDate(row.nodes)
  for (let i = sorted.length - 1; i >= 0; i--) {
    const n = sorted[i]
    if (isDueDateReached(n.due_date) && n.status === 'done' && n.pct_change != null) {
      return n
    }
  }
  return null
}

function heroClass(pct: number | null | undefined) {
  if (pct == null) return 'flat'
  if (pct > 0) return 'up'
  if (pct < 0) return 'down'
  return 'flat'
}

function openDetail(id: number) {
  router.push({ path: `/recommendations/${id}`, query: { from: props.from } })
}

async function deleteRow(row: RecommendationOut) {
  if (!confirm(`确定删除「${row.stock_name}」？`)) return
  deletingId.value = row.id
  try {
    const res = await api.deleteRec(row.id)
    toast(res.message || '自选记录已删除')
    emit('deleted', row.id)
  } catch (e) {
    toast(e instanceof Error ? e.message : '删除失败')
  } finally {
    deletingId.value = null
  }
}

function nodeForLabel(row: RecommendationOut, label: string) {
  return row.nodes.find((n) => n.label === label)
}

function nodePct(row: RecommendationOut, label: string) {
  const n = nodeForLabel(row, label)
  if (!n || !isDueDateReached(n.due_date) || n.status !== 'done' || n.pct_change == null) return null
  return n.pct_change
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
          <th>自选日</th>
          <th class="num">自选价</th>
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
          <td v-for="label in nodeLabels" :key="label" class="num-cell">
            <span
              v-if="nodePct(row, label) != null"
              class="chip"
              :class="chipClass(nodePct(row, label))"
              :style="chipAlpha(nodePct(row, label))"
            >{{ fmtPct(nodePct(row, label)!) }}</span>
            <span v-else class="chip flat">—</span>
          </td>
          <td v-if="showAction" class="action">
            <button class="btn btn-sm btn-ghost" @click.stop="openDetail(row.id)">详情</button>
            <button
              v-if="showDelete && from !== 'admin'"
              class="btn btn-sm btn-danger"
              :disabled="deletingId === row.id"
              @click.stop="deleteRow(row)"
            >{{ deletingId === row.id ? '删除中…' : '删除' }}</button>
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

  <div class="mcards">
    <div v-if="!rows.length" class="empty">
      <strong>{{ emptyTitle }}</strong>
      <span v-if="emptyDesc">{{ emptyDesc }}</span>
    </div>
    <template v-else>
      <div
        v-for="row in rows"
        :key="`card-${row.id}`"
        class="mcard"
        @click="openDetail(row.id)"
      >
        <div class="mcard-top">
          <div class="nm">
            <span class="code">{{ row.stock_code }}</span>{{ row.stock_name }}
          </div>
          <div class="mcard-hero" :class="heroClass(latestDoneNode(row)?.pct_change)">
            <template v-if="latestDoneNode(row)">
              <small>{{ latestDoneNode(row)!.label }}</small>{{ fmtPct(latestDoneNode(row)!.pct_change!) }}
            </template>
            <template v-else>追踪中</template>
          </div>
        </div>
        <div class="mcard-meta">
          <span class="tag" :style="{ '--tag-c': tagColor(row.channel_color) }">{{ row.channel_name }}</span>
          <span class="mono">{{ fmtDateShort(row.recommend_date) }}</span>
          <span class="mono">¥{{ fmtPrice(row.recommend_price) }}</span>
        </div>
        <div v-if="miniLabelIndices.length" class="mcard-nodes">
          <span
            v-for="idx in miniLabelIndices"
            :key="`${row.id}-${idx}`"
            class="mini"
            :class="heroClass(nodePct(row, nodeLabels[idx]))"
          >
            <i>{{ nodeLabels[idx] }}</i>
            {{ nodePct(row, nodeLabels[idx]) != null ? fmtPct(nodePct(row, nodeLabels[idx])!) : '—' }}
          </span>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.action {
  white-space: nowrap;
}
.action .btn + .btn {
  margin-left: 6px;
}
</style>
