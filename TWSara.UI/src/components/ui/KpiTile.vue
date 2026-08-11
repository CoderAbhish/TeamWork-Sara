<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
})
</script>

<template>
  <div class="bg-white rounded-lg border border-slate-200 p-5">
    <p class="text-xs font-medium text-slate-500 uppercase tracking-wide">{{ label }}</p>
    <p class="text-3xl font-semibold text-ink-900 mt-2">{{ value }}</p>
  </div>
</template>
