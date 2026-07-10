<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api, chipClass, fmtPct } from '@/api/client'
import { tagColor } from '@/utils/colors'
import { fmtDateShort, fmtPrice, isDueDateReached, sortNodesByDueDate } from '@/utils/format'
import { toast } from '@/utils/toast'
import type { RecommendationOut } from '@/types/api'

const route = useRoute()
const router = useRouter()
const rec = ref<RecommendationOut | null>(null)
const loading = ref(true)
const editing = ref(false)
const saving = ref(false)
const deleting = ref(false)
const refetching = ref(false)
const fetchMsg = ref('')
const formDate = ref('')
const formPrice = ref('')
const formReason = ref('')
const errorMsg = ref('')

const backPath = computed(() => {
  const from = route.query.from as string
  if (from === 'admin') return '/admin/records'
  if (from === 'search') return '/search'
  return '/tracking'
})

const isAdminView = computed(() => route.query.from === 'admin')

const nodesByDueDate = computed(() => {
  if (!rec.value) return []
  return sortNodesByDueDate(rec.value.nodes)
})

const railTimeline = computed(() => {
  if (!rec.value) return []
  const open = {
    key: 'open',
    label: '开仓',
    date: rec.value.recommend_date,
    price: rec.value.recommend_price,
    pct: null as number | null,
    status: 'done' as const,
    isOpen: true,
  }
  const nodes = nodesByDueDate.value.map((node) => ({
    key: String(node.id),
    label: node.label,
    date: node.due_date,
    price: isDueDateReached(node.due_date) ? node.close_price : null,
    pct: isDueDateReached(node.due_date) && node.status === 'done' ? node.pct_change : null,
    status: !isDueDateReached(node.due_date) ? 'pending' as const : node.status,
    isOpen: false,
  }))
  return [open, ...nodes]
})

function nodeStatusLabel(node: { due_date: string; status: string }) {
  if (!isDueDateReached(node.due_date)) return '待到期'
  if (node.status === 'done') return '已完成'
  if (node.status === 'failed') return '获取失败'
  return '待抓取'
}

async function load() {
  loading.value = true
  try {
    rec.value = await api.getRec(Number(route.params.id)) as RecommendationOut
    resetForm()
  } finally {
    loading.value = false
  }
}

function resetForm() {
  if (!rec.value) return
  formDate.value = rec.value.recommend_date
  formPrice.value = String(rec.value.recommend_price)
  formReason.value = rec.value.reason || ''
}

function startEdit() {
  resetForm()
  editing.value = true
  errorMsg.value = ''
}

function cancelEdit() {
  editing.value = false
  errorMsg.value = ''
  resetForm()
}

async function saveEdit() {
  if (!rec.value) return
  if (!formDate.value) {
    errorMsg.value = '请填写自选日期'
    return
  }
  saving.value = true
  errorMsg.value = ''
  try {
    const body: Record<string, unknown> = {
      recommend_date: formDate.value,
      reason: formReason.value,
    }
    const price = Number(formPrice.value)
    if (price > 0) body.recommend_price = price
    rec.value = await api.updateRec(rec.value.id, body) as RecommendationOut
    editing.value = false
    await refetchNodes(false)
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

async function deleteRec() {
  if (!rec.value) return
  if (!confirm(`确定删除「${rec.value.stock_name}」的自选记录？删除后无法恢复。`)) return
  deleting.value = true
  errorMsg.value = ''
  try {
    const res = isAdminView.value
      ? await api.adminDeleteRec(rec.value.id)
      : await api.deleteRec(rec.value.id)
    toast(res.message || '自选记录已删除')
    router.push(backPath.value)
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '删除失败'
    toast(errorMsg.value)
  } finally {
    deleting.value = false
  }
}

async function refetchNodes(showConfirm = true) {
  if (!rec.value || isAdminView.value) return
  if (showConfirm && !confirm('重新抓取所有已到期节点的行情？')) return
  refetching.value = true
  fetchMsg.value = ''
  errorMsg.value = ''
  try {
    const res = await api.refetchRec(rec.value.id) as { message: string }
    fetchMsg.value = res.message
    await load()
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '抓取失败'
  } finally {
    refetching.value = false
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
            <span class="user-badge mine">我的自选</span>
            <span class="tag" :style="{ '--tag-c': tagColor(rec.channel_color) }">{{ rec.channel_name }}</span>
          </div>
        </div>
        <div class="title-actions">
          <span v-if="!editing" class="meta">开仓 {{ rec.recommend_date }} · ¥{{ fmtPrice(rec.recommend_price) }}</span>
          <div v-if="!editing" class="title-btns">
            <button type="button" class="btn btn-sm btn-ghost" @click="startEdit">编辑</button>
            <button
              v-if="!isAdminView"
              type="button"
              class="btn btn-sm btn-ghost"
              :disabled="refetching"
              @click="refetchNodes()"
            >{{ refetching ? '抓取中…' : '重新抓价' }}</button>
            <button type="button" class="btn btn-sm btn-danger" :disabled="deleting" @click="deleteRec">删除</button>
          </div>
        </div>
      </div>

      <div v-if="editing" class="card edit-card">
        <div class="card-head"><h3>编辑自选信息</h3></div>
        <div class="card-body edit-form">
          <div class="form-group">
            <label>开仓日期</label>
            <input v-model="formDate" type="date" class="form-control">
          </div>
          <div class="form-group">
            <label>开仓价格（元）</label>
            <input v-model="formPrice" type="number" step="0.01" min="0.01" class="form-control" placeholder="留空则保持原价">
          </div>
          <div class="form-group">
            <label>自选理由</label>
            <textarea v-model="formReason" class="form-control" rows="3" />
          </div>
          <p class="edit-hint">修改日期或价格后，追踪节点将自动重建并重新抓取。</p>
          <p v-if="errorMsg" class="form-error">{{ errorMsg }}</p>
          <div class="edit-actions">
            <button type="button" class="btn btn-ghost" :disabled="saving" @click="cancelEdit">取消</button>
            <button type="button" class="btn btn-primary" :disabled="saving" @click="saveEdit">保存</button>
          </div>
        </div>
      </div>

      <div class="card rail-card">
        <div class="card-head"><h3>开仓与追踪时间线</h3></div>
        <div class="rail">
          <div
            v-for="item in railTimeline"
            :key="item.key"
            class="rail-node"
            :class="{ done: item.status === 'done', open: item.isOpen }"
          >
            <div class="rail-dot" />
            <div class="rl">{{ item.label }}</div>
            <div class="rd">{{ fmtDateShort(item.date) }}</div>
            <div v-if="item.isOpen" class="rv open-price">¥{{ fmtPrice(item.price ?? 0) }}</div>
            <div
              v-else-if="item.status === 'done' && item.pct != null"
              class="rv"
              :class="chipClass(item.pct)"
            >{{ fmtPct(item.pct) }}</div>
            <div v-else-if="item.price != null" class="rv open-price">¥{{ fmtPrice(item.price) }}</div>
            <div v-else class="rv pend">{{ item.status === 'pending' ? '待到期' : '—' }}</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-head"><h3>时间线明细</h3></div>
        <div class="v-timeline">
          <div v-for="item in railTimeline" :key="`v-${item.key}`" class="v-tl-item" :class="{ open: item.isOpen }">
            <div class="v-tl-dot" />
            <div class="v-tl-body">
              <div class="v-tl-title">
                <strong>{{ item.label }}</strong>
                <span class="mono">{{ fmtDateShort(item.date) }}</span>
              </div>
              <div class="v-tl-meta">
                <span v-if="item.isOpen">开仓价 ¥{{ fmtPrice(item.price ?? 0) }}</span>
                <template v-else>
                  <span v-if="item.price != null">收盘 ¥{{ fmtPrice(item.price) }}</span>
                  <span
                    v-if="item.pct != null"
                    class="chip"
                    :class="chipClass(item.pct)"
                  >{{ fmtPct(item.pct) }}</span>
                  <span v-else-if="item.status === 'pending'" class="dim">待到期</span>
                </template>
              </div>
            </div>
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
                <th>周期</th>
                <th>到期日</th>
                <th>状态</th>
                <th class="num">收盘价</th>
                <th class="num">涨跌幅</th>
              </tr>
            </thead>
            <tbody>
              <tr class="open-row">
                <td>开仓</td>
                <td class="mono">开仓</td>
                <td class="td-date">{{ rec.recommend_date }}</td>
                <td>已开仓</td>
                <td class="price-cell">{{ fmtPrice(rec.recommend_price) }}</td>
                <td class="num-cell"><span class="chip flat">基准</span></td>
              </tr>
              <tr v-for="node in nodesByDueDate" :key="node.id">
                <td>{{ node.label }}</td>
                <td>{{ node.label }}</td>
                <td class="td-date">{{ node.due_date }}</td>
                <td>{{ nodeStatusLabel(node) }}</td>
                <td class="price-cell">{{ isDueDateReached(node.due_date) && node.close_price != null ? fmtPrice(node.close_price) : '—' }}</td>
                <td class="num-cell">
                  <span
                    v-if="isDueDateReached(node.due_date) && node.pct_change != null"
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

      <div v-if="rec.reason && !editing" class="card">
        <div class="card-head"><h3>自选理由</h3></div>
        <div class="card-body"><p>{{ rec.reason }}</p></div>
      </div>

      <p v-if="fetchMsg && !editing" class="fetch-msg">{{ fetchMsg }}</p>
      <div v-if="errorMsg && !editing" class="form-error page-error">{{ errorMsg }}</div>

      <div class="detail-foot">
        <RouterLink :to="backPath" class="btn btn-ghost">← 返回列表</RouterLink>
        <button v-if="!editing" type="button" class="btn btn-danger" :disabled="deleting" @click="deleteRec">
          删除此自选
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.title-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}
.title-btns {
  display: flex;
  gap: 8px;
}
.page-error {
  margin-bottom: 16px;
}
.fetch-msg {
  color: var(--t2);
  font-size: 13px;
  margin: 0 0 16px;
}
.detail-foot {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}
.edit-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 420px;
}
.edit-hint {
  font-size: 12px;
  color: var(--t3);
  margin: 0;
}
.edit-actions {
  display: flex;
  gap: 8px;
}
.form-error {
  color: var(--danger, #e53e3e);
  font-size: 13px;
  margin: 0;
}
.rail-node.open .rail-dot {
  background: var(--warn);
  border-color: var(--warn);
}
.rv.open-price {
  color: var(--ink);
  font-size: 13px;
  font-weight: 600;
}
.v-timeline {
  padding: 8px 22px 20px;
  display: flex;
  flex-direction: column;
  gap: 0;
}
.v-tl-item {
  display: flex;
  gap: 14px;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
  position: relative;
}
.v-tl-item:last-child { border-bottom: 0; }
.v-tl-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--accent);
  margin-top: 4px;
  flex-shrink: 0;
}
.v-tl-item.open .v-tl-dot { background: var(--warn); }
.v-tl-body { flex: 1; min-width: 0; }
.v-tl-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 14px;
}
.v-tl-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 6px;
  font-size: 13px;
  color: var(--t2);
}
.open-row { background: rgba(var(--up-rgb), 0.04); }
</style>
