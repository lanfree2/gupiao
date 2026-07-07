<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { toast } from '@/utils/toast'
import type { ChannelStatsOut, PeriodOut } from '@/types/api'

const NEW = '__new__'
const router = useRouter()

const channels = ref<ChannelStatsOut[]>([])
const periods = ref<PeriodOut[]>([])
const stockCode = ref('')
const stockName = ref('')
const channelSel = ref('')
const newChannelName = ref('')
const recommendDate = ref(new Date().toISOString().slice(0, 10))
const recommendPrice = ref('')
const priceHint = ref('')
const reason = ref('')
const error = ref('')
const loading = ref(false)
const nameTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const priceTimer = ref<ReturnType<typeof setTimeout> | null>(null)

const showNewChannel = computed(() => channelSel.value === NEW)
const today = computed(() => new Date().toISOString().slice(0, 10))

const timeline = computed(() =>
  periods.value.map((p) => {
    const d = new Date(recommendDate.value)
    d.setDate(d.getDate() + p.days)
    const due = d.toISOString().slice(0, 10)
    return { label: p.label, days: p.days, due, ready: due <= today.value }
  }),
)

const hasPastNodes = computed(() => timeline.value.some((t) => t.ready))

async function loadMeta() {
  const [chs, ps] = await Promise.all([
    api.channels() as Promise<ChannelStatsOut[]>,
    api.periods() as Promise<PeriodOut[]>,
  ])
  channels.value = chs
  periods.value = ps
  if (chs.length && !channelSel.value) channelSel.value = String(chs[0].id)
}

watch(stockCode, (code) => {
  if (nameTimer.value) clearTimeout(nameTimer.value)
  if (!/^\d{6}$/.test(code.trim())) return
  nameTimer.value = setTimeout(async () => {
    try {
      const res = await api.stockLookup(code.trim()) as { name?: string }
      stockName.value = res.name || '未知'
    } catch {
      stockName.value = '未知'
    }
  }, 400)
})

watch([stockCode, recommendDate], () => {
  if (priceTimer.value) clearTimeout(priceTimer.value)
  const code = stockCode.value.trim()
  if (!/^\d{6}$/.test(code) || !recommendDate.value) {
    priceHint.value = ''
    return
  }
  priceTimer.value = setTimeout(async () => {
    try {
      const res = await api.stockClose(code, recommendDate.value) as { close: number; trade_date: string }
      if (!recommendPrice.value) recommendPrice.value = String(res.close)
      priceHint.value = `推荐日(${res.trade_date})收盘价 ¥${res.close}，留空将自动使用`
    } catch (e) {
      const msg = e instanceof Error ? e.message : ''
      if (msg.includes('代理') || msg.includes('行情源') || msg.includes('503')) {
        priceHint.value = '行情接口暂时不可用（网络/代理问题），请手动填写价格'
      } else {
        priceHint.value = '该日期暂无收盘价数据，请选手动填写或更换日期'
      }
    }
  }, 500)
})

async function submit() {
  error.value = ''
  if (!stockCode.value.trim()) {
    error.value = '请输入股票代码'
    return
  }
  if (channelSel.value === NEW && !newChannelName.value.trim()) {
    error.value = '请输入新渠道名称'
    return
  }
  loading.value = true
  try {
    const body: Record<string, unknown> = {
      stock_code: stockCode.value.trim(),
      stock_name: stockName.value,
      recommend_date: recommendDate.value,
      reason: reason.value,
    }
    const price = Number(recommendPrice.value)
    if (price > 0) body.recommend_price = price
    if (channelSel.value === NEW) {
      body.new_channel_name = newChannelName.value.trim()
    } else {
      body.channel_id = Number(channelSel.value)
    }
    const res = await api.createRec(body) as {
      id?: number
      recommendation?: { id: number }
      fetch?: { message: string; done: number }
    }
    const recId = res.recommendation?.id ?? res.id
    if (!recId) {
      throw new Error('保存成功但返回数据异常，请到「我的追踪」查看')
    }
    toast(res.fetch?.message || '已保存')
    router.push(`/recommendations/${recId}`)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadMeta)
</script>

<template>
  <div class="page">
    <div class="topbar">
      <div>
        <h2>录入推荐</h2>
        <p class="desc">添加新的股票推荐并开始自动追踪</p>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-head"><h3>基本信息</h3></div>
        <div class="card-body">
          <div class="form-group">
            <label>股票代码</label>
            <input v-model="stockCode" class="form-control mono" inputmode="numeric" maxlength="6">
          </div>
          <div class="form-group">
            <label>股票名称</label>
            <input v-model="stockName" class="form-control" readonly style="opacity:.6">
          </div>
          <div class="form-group">
            <label>推荐渠道</label>
            <select v-model="channelSel" class="form-control">
              <option v-for="ch in channels" :key="ch.id" :value="String(ch.id)">{{ ch.name }}</option>
              <option :value="NEW">＋ 新建渠道</option>
            </select>
            <div v-if="showNewChannel" class="channel-new-field">
              <input v-model="newChannelName" class="form-control" placeholder="输入新渠道名称">
              <p class="form-hint">保存后自动创建</p>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>推荐日期</label>
              <input v-model="recommendDate" class="form-control mono" type="date">
            </div>
            <div class="form-group">
              <label>推荐价格（元）</label>
              <input v-model="recommendPrice" class="form-control mono" inputmode="decimal" placeholder="留空则自动取推荐日收盘价">
              <p v-if="priceHint" class="form-hint">{{ priceHint }}</p>
            </div>
          </div>
          <div class="form-group">
            <label>推荐理由</label>
            <textarea v-model="reason" class="form-control" />
          </div>
        </div>
      </div>

      <div>
        <div class="card">
          <div class="card-head"><h3>追踪周期</h3></div>
          <div class="card-body">
            <p style="color:var(--t2);font-size:13.5px;margin-bottom:14px;line-height:1.7">
              保存后系统将在各节点到期日自动抓取收盘价。若推荐日期较早，已到期节点会<strong>立即抓取历史行情</strong>。
            </p>
            <div class="node-tags">
              <span v-for="p in periods" :key="p.id" class="node-tag">{{ p.label }}（{{ p.days }}天）</span>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-head"><h3>追踪时间表预览</h3></div>
          <div style="padding:0 4px">
            <table>
              <thead><tr><th>节点</th><th>预计日期</th><th>状态</th></tr></thead>
              <tbody>
                <tr v-for="t in timeline" :key="t.label">
                  <td>{{ t.label }}</td>
                  <td class="mono">{{ t.due }}</td>
                  <td :class="t.ready ? 'ready' : 'dim'">{{ t.ready ? '保存后立即抓取' : '待到期' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <div style="display:flex;gap:12px">
          <button type="button" class="btn btn-primary" style="flex:1;justify-content:center" :disabled="loading" @click="submit">
            {{ loading ? (hasPastNodes ? '保存并抓取历史行情…' : '保存中…') : '保存并开始追踪' }}
          </button>
          <button type="button" class="btn btn-ghost" @click="router.push('/dashboard')">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>
