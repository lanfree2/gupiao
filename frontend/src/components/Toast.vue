<script setup lang="ts">
import { useToastState } from '@/utils/toast'

const { message, visible } = useToastState()
</script>

<template>
  <div class="toast" :class="{ show: visible }">{{ message }}</div>
</template>
