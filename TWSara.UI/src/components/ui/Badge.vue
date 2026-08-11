<script setup>
defineProps({
  label: { type: String, required: true },
  color: { type: String, default: 'slate' },
})
</script>

<template>
  <span
    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap"
    :class="`bg-${color}-100 text-${color}-700`"
  >
    {{ label }}
  </span>
</template>
