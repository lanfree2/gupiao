<script setup lang="ts">
import { ref, watch } from 'vue'
import { api } from '@/api/client'
import RecTable from '@/components/RecTable.vue'
import type { RecommendationOut } from '@/types/api'

const q = ref('')
const scope = ref<'all' | 'stock' | 'channel'>('all')
const rows = ref<RecommendationOut[]>([])
const loading = ref(false)

const scopes = [
  { key: 'all' as const, label: '全部' },
  { key: 'stock' as const, label: '按股票' },
  { key: 'channel' as const, label: '按渠道' },
]

async function search() {
  loading.value = true
  try {
    rows.value = await api.search(q.value.trim(), scope.value) as RecommendationOut[]
  } finally {
    loading.value = false
  }
}

function onDeleted(id: number) {
  rows.value = rows.value.filter((r) => r.id !== id)
  search()
}

let timer: ReturnType<typeof setTimeout> | null = null
watch([q, scope], () => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(search, 300)
})

search()
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>搜索</h2>
        <p class="desc">在我的全部记录中搜索股票代码、名称或渠道</p>
      </div>
    </div>

    <div class="search-hero">
      <input v-model="q" type="text" placeholder="搜索代码、名称或渠道名…">
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

    <div class="card only-table">
      <div class="card-head">
        <h3>{{ q ? `搜索结果（${rows.length} 条）` : `我的全部记录（${rows.length} 条）` }}</h3>
      </div>
      <div v-if="loading" class="empty"><strong>搜索中…</strong></div>
      <RecTable v-else :rows="rows" from="search" empty-title="未找到匹配记录" empty-desc="试试换个关键词" @deleted="onDeleted" />
    </div>
  </div>
</template>
