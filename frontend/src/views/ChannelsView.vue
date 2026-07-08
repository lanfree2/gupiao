<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { api } from '@/api/client'
import { tagColor } from '@/utils/colors'
import { fmtPctVal } from '@/utils/format'
import { toast } from '@/utils/toast'
import PeriodSettingsModal from '@/components/PeriodSettingsModal.vue'
import type { ChannelStatsOut, PeriodOut, RecommendationOut } from '@/types/api'
import RecTable from '@/components/RecTable.vue'

const router = useRouter()
const channels = ref<ChannelStatsOut[]>([])
const records = ref<RecommendationOut[]>([])
const channelFilter = ref('')
const loading = ref(true)
const showModal = ref(false)
const editId = ref<number | null>(null)
const formName = ref('')
const formColor = ref('blue')
const formDesc = ref('')
const saving = ref(false)
const deleting = ref(false)
const errorMsg = ref('')
const showPeriodModal = ref(false)
const periods = ref<PeriodOut[]>([])

const colors = ['blue', 'green', 'orange', 'purple', 'gray']

const filteredRecords = computed(() => {
  if (!channelFilter.value) return records.value
  const id = Number(channelFilter.value)
  return records.value.filter((r) => r.channel_id === id)
})

function recordCountForChannel(channelId: number) {
  return records.value.filter((r) => r.channel_id === channelId).length
}

async function load() {
  loading.value = true
  try {
    const [chs, ps, recs] = await Promise.all([
      api.channels() as Promise<ChannelStatsOut[]>,
      api.periods() as Promise<PeriodOut[]>,
      api.recommendations() as Promise<RecommendationOut[]>,
    ])
    channels.value = chs
    periods.value = ps
    records.value = recs.sort((a, b) => b.recommend_date.localeCompare(a.recommend_date))
  } finally {
    loading.value = false
  }
}

function onDeleted(id: number) {
  records.value = records.value.filter((r) => r.id !== id)
  load()
}

function openChannelRecords(ch: ChannelStatsOut) {
  channelFilter.value = String(ch.id)
  document.getElementById('channel-records')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function openCreate() {
  editId.value = null
  formName.value = ''
  formColor.value = 'blue'
  formDesc.value = ''
  showModal.value = true
}

function openEdit(ch: ChannelStatsOut) {
  editId.value = ch.id
  formName.value = ch.name
  formColor.value = ch.color
  formDesc.value = ch.description
  errorMsg.value = ''
  showModal.value = true
}

async function saveChannel() {
  if (!formName.value.trim()) return
  saving.value = true
  errorMsg.value = ''
  try {
    const body = { name: formName.value.trim(), color: formColor.value, description: formDesc.value }
    if (editId.value) {
      await api.updateChannel(editId.value, body)
    } else {
      await api.createChannel(body)
    }
    showModal.value = false
    await load()
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

async function deleteChannel() {
  if (!editId.value) return
  if (!confirm('确定删除该渠道？仅无推荐记录的渠道可删除。')) return
  deleting.value = true
  errorMsg.value = ''
  try {
    const res = await api.deleteChannel(editId.value)
    toast(res.message || '渠道已删除')
    showModal.value = false
    await load()
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '删除失败'
    toast(errorMsg.value)
  } finally {
    deleting.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>我的渠道</h2>
        <p class="desc">管理您的消息来源分类 · 点击渠道卡片查看详细统计</p>
      </div>
      <div class="topbar-btns">
        <button type="button" class="btn btn-ghost" @click="showPeriodModal = true">⚙ 周期设置</button>
        <button type="button" class="btn btn-primary" @click="openCreate">＋ 新建渠道</button>
      </div>
    </div>
    <p class="page-intro">每张卡片展示该渠道的快速摘要，点击进入后可查看完整的统计分析。</p>

    <div v-if="loading" class="empty"><strong>加载中…</strong></div>
    <div v-else class="channel-grid">
      <div
        v-for="ch in channels"
        :key="ch.id"
        class="ch-card"
        :style="{ '--ch-color': tagColor(ch.color) }"
        @click="router.push(`/channels/${ch.id}`)"
      >
        <div class="ch-name">{{ ch.name }}</div>
        <div class="ch-desc">{{ ch.description || '—' }}</div>
        <div class="ch-stats-row">
          <span>追踪 <strong>{{ ch.record_count }}</strong> 只</span>
          <span>胜率 <strong>{{ ch.win_rate != null ? `${Math.round(ch.win_rate)}%` : '—' }}</strong></span>
          <span>均收益 <strong :class="ch.avg_return != null ? (ch.avg_return >= 0 ? 'up' : 'down') : ''">{{ fmtPctVal(ch.avg_return) }}</strong></span>
        </div>
        <div class="ch-foot">
          <span style="font-size:12px;color:var(--t3)">
            {{ recordCountForChannel(ch.id) }} 条历史记录 ·
            <a href="#" @click.prevent.stop="openChannelRecords(ch)">查看记录</a>
          </span>
          <span class="ch-actions">
            <button type="button" class="btn btn-sm btn-ghost" @click.stop="router.push(`/channels/${ch.id}`)">统计</button>
            <button type="button" class="btn btn-sm btn-ghost" @click.stop="openEdit(ch)">编辑</button>
          </span>
        </div>
      </div>
      <button type="button" class="ch-add" @click="openCreate">
        <span style="font-size:26px">＋</span>
        <span>添加新渠道</span>
      </button>
    </div>

    <div id="channel-records" class="card only-table records-section">
      <div class="card-head">
        <h3>历史推荐记录（{{ filteredRecords.length }}）</h3>
        <div class="head-filters">
          <select v-model="channelFilter" class="form-control channel-filter">
            <option value="">全部渠道</option>
            <option v-for="ch in channels" :key="ch.id" :value="String(ch.id)">{{ ch.name }}</option>
          </select>
        </div>
      </div>
      <RecTable
        :rows="filteredRecords"
        from="tracking"
        :empty-title="records.length ? '该渠道暂无记录' : '暂无历史记录'"
        empty-desc="录入推荐后，记录会按渠道归类展示在这里"
        @deleted="onDeleted"
      />
    </div>

    <div class="modal-bg" :class="{ open: showModal }" @click.self="showModal = false">
      <div class="modal">
        <h3>{{ editId ? '编辑渠道' : '新建渠道' }}</h3>
        <div class="form-group">
          <label>渠道名称</label>
          <input v-model="formName" class="form-control">
        </div>
        <div class="form-group">
          <label>颜色</label>
          <select v-model="formColor" class="form-control">
            <option v-for="c in colors" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>描述</label>
          <input v-model="formDesc" class="form-control">
        </div>
        <p v-if="errorMsg" class="form-error">{{ errorMsg }}</p>
        <div class="modal-foot">
          <button
            v-if="editId"
            type="button"
            class="btn btn-danger"
            :disabled="deleting || saving"
            @click="deleteChannel"
          >删除渠道</button>
          <span style="flex:1" />
          <button type="button" class="btn btn-ghost" @click="showModal = false">取消</button>
          <button type="button" class="btn btn-primary" :disabled="saving || deleting" @click="saveChannel">保存</button>
        </div>
      </div>
    </div>

    <PeriodSettingsModal
      v-model:open="showPeriodModal"
      :periods="periods"
      @saved="(ps) => { periods = ps }"
    />
  </div>
</template>

<style scoped>
.records-section { margin-top: 8px; }
.head-filters { display: flex; gap: 8px; align-items: center; }
.channel-filter { min-width: 160px; padding: 8px 10px; font-size: 13px; }
.ch-foot a { color: var(--accent); text-decoration: none; }
.ch-foot a:hover { text-decoration: underline; }
</style>
