<script setup lang="ts">
import { ref, watch } from 'vue'
import { api } from '@/api/client'
import { toast } from '@/utils/toast'
import {
  inferUnitFromLabel,
  periodUnitText,
  periodValueHint,
  suggestLabel,
  type PeriodUnit,
} from '@/utils/periodCalc'
import type { PeriodOut } from '@/types/api'

const props = defineProps<{
  open: boolean
  periods: PeriodOut[]
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: [periods: PeriodOut[]]
}>()

interface DraftPeriod {
  label: string
  days: number
  unit: PeriodUnit
}

const draft = ref<DraftPeriod[]>([])
const newLabel = ref('')
const newDays = ref('')
const newUnit = ref<PeriodUnit>('trading_day')
const saving = ref(false)

const unitOptions: { value: PeriodUnit; text: string }[] = [
  { value: 'trading_day', text: '交易日（跳过周末）' },
  { value: 'natural_week', text: '自然周（7天）' },
  { value: 'natural_month', text: '自然月（日历月）' },
]

watch(
  () => props.open,
  (visible) => {
    if (!visible) return
    draft.value = props.periods.map((p) => ({
      label: p.label,
      days: p.days,
      unit: p.unit || inferUnitFromLabel(p.label),
    }))
    newLabel.value = ''
    newDays.value = ''
    newUnit.value = 'trading_day'
  },
)

function close() {
  emit('update:open', false)
}

function addPeriod() {
  const days = Number(newDays.value)
  if (!days || days < 1) {
    toast(`请填写${periodValueHint(newUnit.value)}`)
    return
  }
  const label = newLabel.value.trim() || suggestLabel(newUnit.value, days)
  draft.value = [...draft.value, { label, days, unit: newUnit.value }].sort((a, b) => a.days - b.days)
  newLabel.value = ''
  newDays.value = ''
  toast(`已添加「${label}」`)
}

function removePeriod(index: number) {
  if (draft.value.length <= 1) {
    toast('至少保留一个周期')
    return
  }
  draft.value = draft.value.filter((_, i) => i !== index)
}

async function save() {
  if (!draft.value.length) {
    toast('至少保留一个周期')
    return
  }
  saving.value = true
  try {
    const saved = await api.savePeriods(
      draft.value.map((p) => ({
        label: p.label.trim() || suggestLabel(p.unit, p.days),
        days: p.days,
        unit: p.unit,
      })),
    ) as PeriodOut[]
    emit('saved', saved)
    toast('周期设置已保存')
    close()
  } catch (e) {
    toast(e instanceof Error ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="modal-bg" :class="{ open }" @click.self="close">
    <div class="modal period-modal">
      <h3>自定义追踪周期</h3>
      <p class="modal-desc">
        <strong>交易日</strong>：按 A 股交易日计数（跳过周六日）。<strong>自然周 / 自然月</strong>：按日历周、日历月计算到期日。
        新录入的自选将按此配置生成时间表。
      </p>
      <div class="period-list">
        <div v-for="(p, i) in draft" :key="i" class="period-item">
          <input v-model="p.label" placeholder="显示名称">
          <select v-model="p.unit" class="unit-select">
            <option v-for="opt in unitOptions" :key="opt.value" :value="opt.value">{{ opt.text }}</option>
          </select>
          <input v-model.number="p.days" class="days-input" type="number" min="1" max="365" :placeholder="periodValueHint(p.unit)">
          <span class="unit-hint">{{ periodUnitText(p.unit, p.days) }}</span>
          <button type="button" class="del-period" @click="removePeriod(i)">×</button>
        </div>
      </div>
      <div class="add-period-row">
        <select v-model="newUnit" class="unit-select">
          <option v-for="opt in unitOptions" :key="opt.value" :value="opt.value">{{ opt.text }}</option>
        </select>
        <input v-model="newLabel" placeholder="名称（可留空自动）">
        <input v-model="newDays" type="number" min="1" max="365" :placeholder="periodValueHint(newUnit)" style="width:88px">
        <button type="button" class="btn btn-sm btn-ghost" @click="addPeriod">添加</button>
      </div>
      <div class="modal-foot">
        <button type="button" class="btn btn-ghost" @click="close">取消</button>
        <button type="button" class="btn btn-primary" :disabled="saving" @click="save">
          {{ saving ? '保存中…' : '完成' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-desc {
  color: var(--t2);
  font-size: 13px;
  margin: -12px 0 18px;
  line-height: 1.7;
}
.period-modal { max-width: 560px; }
.period-item { display: grid; grid-template-columns: 1fr 130px 72px auto 28px; gap: 8px; align-items: center; margin-bottom: 8px; }
.add-period-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 12px; }
.unit-select { padding: 8px; font-size: 12px; border-radius: var(--r-sm); border: 1px solid var(--border-strong); background: var(--surface); }
.unit-hint { font-size: 11px; color: var(--t3); white-space: nowrap; }
</style>
