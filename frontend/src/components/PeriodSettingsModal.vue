<script setup lang="ts">
import { ref, watch } from 'vue'
import { api } from '@/api/client'
import { toast } from '@/utils/toast'
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
}

const draft = ref<DraftPeriod[]>([])
const newLabel = ref('')
const newDays = ref('')
const saving = ref(false)

watch(
  () => props.open,
  (visible) => {
    if (!visible) return
    draft.value = props.periods.map((p) => ({ label: p.label, days: p.days }))
    newLabel.value = ''
    newDays.value = ''
  },
)

function close() {
  emit('update:open', false)
}

function addPeriod() {
  const label = newLabel.value.trim()
  const days = Number(newDays.value)
  if (!label || !days || days < 1) {
    toast('请填写名称和天数')
    return
  }
  draft.value = [...draft.value, { label, days }].sort((a, b) => a.days - b.days)
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
      draft.value.map((p) => ({ label: p.label.trim(), days: p.days })),
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
    <div class="modal">
      <h3>自定义追踪周期</h3>
      <p class="modal-desc">
        设置追踪节点，新录入的推荐将按此配置生成时间表。已有记录的周期不会被修改。
      </p>
      <div class="period-list">
        <div v-for="(p, i) in draft" :key="i" class="period-item">
          <input v-model="p.label" placeholder="名称">
          <input v-model.number="p.days" class="days-input" type="number" min="1" max="365" placeholder="天数">
          <button type="button" class="del-period" @click="removePeriod(i)">×</button>
        </div>
      </div>
      <div class="add-period-row">
        <input v-model="newLabel" placeholder="名称（如：6月）">
        <input v-model="newDays" type="number" min="1" max="365" placeholder="天数" style="width:80px">
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
</style>
