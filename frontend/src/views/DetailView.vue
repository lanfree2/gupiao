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
const editing = ref(false)
const saving = ref(false)
const deleting = ref(false)
const errorMsg = ref('')
const formDate = ref('')
const formPrice = ref('')
const formReason = ref('')

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
  const price = Number(formPrice.value)
  if (!formDate.value || !price || price <= 0) {
    errorMsg.value = '请填写有效的推荐日期和价格'
    return
  }
  saving.value = true
  errorMsg.value = ''
  try {
    rec.value = await api.updateRec(rec.value.id, {
      recommend_date: formDate.value,
      recommend_price: price,
      reason: formReason.value,
    }) as RecommendationOut
    editing.value = false
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

async function deleteRec() {
  if (!rec.value) return
  if (!confirm(`确定删除「${rec.value.stock_name}」的推荐记录？删除后无法恢复。`)) return
  deleting.value = true
  errorMsg.value = ''
  try {
    await api.deleteRec(rec.value.id)
    router.push(backPath.value)
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '删除失败'
  } finally {
    deleting.value = false
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
        <div class="title-actions">
          <span v-if="!editing" class="meta">{{ rec.recommend_date }} · ¥{{ fmtPrice(rec.recommend_price) }}</span>
          <div v-if="!editing" class="title-btns">
            <button type="button" class="btn btn-sm btn-ghost" @click="startEdit">编辑</button>
            <button type="button" class="btn btn-sm btn-danger" :disabled="deleting" @click="deleteRec">删除</button>
          </div>
        </div>
      </div>

      <div v-if="editing" class="card edit-card">
        <div class="card-head"><h3>编辑推荐信息</h3></div>
        <div class="card-body edit-form">
          <div class="form-group">
            <label>推荐日期</label>
            <input v-model="formDate" type="date" class="form-control">
          </div>
          <div class="form-group">
            <label>推荐价格（元）</label>
            <input v-model="formPrice" type="number" step="0.01" min="0.01" class="form-control">
          </div>
          <div class="form-group">
            <label>推荐理由</label>
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

      <div v-if="rec.reason && !editing" class="card">
        <div class="card-head"><h3>推荐理由</h3></div>
        <div class="card-body"><p>{{ rec.reason }}</p></div>
      </div>

      <div v-if="errorMsg && !editing" class="form-error page-error">{{ errorMsg }}</div>

      <RouterLink :to="backPath" class="btn btn-ghost">← 返回列表</RouterLink>
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
</style>
