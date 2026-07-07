<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { api } from '@/api/client'
import { tagColor } from '@/utils/colors'
import { fmtPctVal } from '@/utils/format'
import type { ChannelStatsOut } from '@/types/api'

const router = useRouter()
const channels = ref<ChannelStatsOut[]>([])
const loading = ref(true)
const showModal = ref(false)
const editId = ref<number | null>(null)
const formName = ref('')
const formColor = ref('blue')
const formDesc = ref('')

const colors = ['blue', 'green', 'orange', 'purple', 'gray']

async function load() {
  loading.value = true
  try {
    channels.value = await api.channels() as ChannelStatsOut[]
  } finally {
    loading.value = false
  }
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
  showModal.value = true
}

async function saveChannel() {
  if (!formName.value.trim()) return
  const body = { name: formName.value.trim(), color: formColor.value, description: formDesc.value }
  if (editId.value) {
    await api.updateChannel(editId.value, body)
  } else {
    await api.createChannel(body)
  }
  showModal.value = false
  await load()
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
          <span style="font-size:12px;color:var(--t3)">点击查看详细统计 →</span>
          <span><button type="button" class="btn btn-sm btn-ghost" @click.stop="openEdit(ch)">编辑</button></span>
        </div>
      </div>
      <button type="button" class="ch-add" @click="openCreate">
        <span style="font-size:26px">＋</span>
        <span>添加新渠道</span>
      </button>
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
        <div class="modal-foot">
          <button type="button" class="btn btn-ghost" @click="showModal = false">取消</button>
          <button type="button" class="btn btn-primary" @click="saveChannel">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
