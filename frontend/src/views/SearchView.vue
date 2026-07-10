<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '@/api/client'
import RecTable from '@/components/RecTable.vue'
import { tagColor } from '@/utils/colors'
import type { ChannelStatsOut, PeriodOut, RecommendationOut } from '@/types/api'

const q = ref('')
const scope = ref<'all' | 'stock' | 'channel'>('all')
const channelId = ref<number | ''>('')
const rows = ref<RecommendationOut[]>([])
const channels = ref<ChannelStatsOut[]>([])
const periods = ref<PeriodOut[]>([])
const loading = ref(false)
const errorMsg = ref('')

const scopes = [
  { key: 'all' as const, label: '全部' },
  { key: 'stock' as const, label: '按股票' },
  { key: 'channel' as const, label: '按渠道' },
]

const periodLabels = computed(() => periods.value.map((p) => p.label))

const searchPlaceholder = computed(() => {
  if (scope.value === 'stock') return '输入股票代码或名称，如 600519、贵州茅台'
  if (scope.value === 'channel') return '输入渠道名称，或点击下方渠道'
  return '搜索代码、名称或渠道名…'
})

const listTitle = computed(() => {
  if (loading.value) return '搜索中…'
  if (scope.value === 'stock' && !q.value.trim()) return '按股票搜索'
  if (scope.value === 'channel' && !q.value.trim() && !channelId.value) return '按渠道搜索'
  if (q.value.trim() || channelId.value) return `搜索结果（${rows.value.length} 条）`
  return `我的全部记录（${rows.value.length} 条）`
})

const emptyTitle = computed(() => {
  if (scope.value === 'stock' && !q.value.trim()) return '请输入股票代码或名称'
  if (scope.value === 'channel' && !q.value.trim() && !channelId.value) return '请选择或输入渠道'
  return '未找到匹配记录'
})

const emptyDesc = computed(() => {
  if (scope.value === 'stock' && !q.value.trim()) return '支持代码、名称模糊搜索'
  if (scope.value === 'channel' && !q.value.trim() && !channelId.value) return '点击上方渠道标签可快速筛选'
  return '试试换个关键词或切换搜索范围'
})

async function search() {
  loading.value = true
  errorMsg.value = ''
  try {
    rows.value = (await api.search(
      q.value.trim(),
      scope.value,
      channelId.value ? Number(channelId.value) : undefined,
    )) as RecommendationOut[]
  } catch (e) {
    rows.value = []
    errorMsg.value = e instanceof Error ? e.message : '搜索失败'
  } finally {
    loading.value = false
  }
}

function pickChannel(ch: ChannelStatsOut) {
  scope.value = 'channel'
  channelId.value = ch.id
  q.value = ch.name
  search()
}

function setScope(next: 'all' | 'stock' | 'channel') {
  scope.value = next
  if (next !== 'channel') {
    channelId.value = ''
  }
}

function onDeleted(id: number) {
  rows.value = rows.value.filter((r) => r.id !== id)
  search()
}

watch(q, (val) => {
  if (channelId.value) {
    const ch = channels.value.find((c) => c.id === channelId.value)
    if (ch && val.trim() !== ch.name) channelId.value = ''
  }
})

let timer: ReturnType<typeof setTimeout> | null = null
watch([q, scope, channelId], () => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(search, 300)
})

onMounted(async () => {
  try {
    const [chs, ps] = await Promise.all([
      api.channels() as Promise<ChannelStatsOut[]>,
      api.periods() as Promise<PeriodOut[]>,
    ])
    channels.value = chs
    periods.value = ps
  } catch {
    /* 渠道/周期加载失败不阻塞搜索 */
  }
  search()
})
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>搜索</h2>
        <p class="desc">
          <template v-if="scope === 'all'">在我的全部记录中搜索股票代码、名称或渠道</template>
          <template v-else-if="scope === 'stock'">仅搜索股票代码与名称</template>
          <template v-else>仅搜索渠道名称</template>
        </p>
      </div>
    </div>

    <div class="search-hero">
      <input v-model="q" type="text" :placeholder="searchPlaceholder">
      <div class="search-tabs">
        <button
          v-for="s in scopes"
          :key="s.key"
          type="button"
          class="search-tab"
          :class="{ active: scope === s.key }"
          @click="setScope(s.key)"
        >{{ s.label }}</button>
      </div>
      <div v-if="scope === 'channel' && channels.length" class="channel-picks">
        <span class="dim">快速选择：</span>
        <button
          v-for="ch in channels"
          :key="ch.id"
          type="button"
          class="channel-pick"
          :class="{ active: channelId === ch.id }"
          @click="pickChannel(ch)"
        >
          <i :style="{ background: tagColor(ch.color) }" />
          {{ ch.name }}
        </button>
      </div>
    </div>

    <div class="card only-table">
      <div class="card-head">
        <h3>{{ listTitle }}</h3>
      </div>
      <p v-if="errorMsg" class="form-error page-error">{{ errorMsg }}</p>
      <div v-if="loading" class="empty"><strong>搜索中…</strong></div>
      <RecTable
        v-else
        :rows="rows"
        :periods="periodLabels"
        from="search"
        :empty-title="emptyTitle"
        :empty-desc="emptyDesc"
        @deleted="onDeleted"
      />
    </div>
  </div>
</template>

<style scoped>
.channel-picks {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
}
.channel-pick {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--border-strong);
  background: var(--surface);
  color: var(--t2);
  font-size: 13px;
  cursor: pointer;
}
.channel-pick i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.channel-pick.active {
  border-color: var(--accent);
  background: var(--accent-dim);
  color: var(--accent);
}
</style>
