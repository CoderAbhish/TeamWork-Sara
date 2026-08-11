<script setup>
defineProps({
  title: { type: String, default: '' },
  widthClass: { type: String, default: 'max-w-lg' },
})
const emit = defineEmits(['close'])
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-ink-900/50" @click="emit('close')"></div>
    <div
      :class="['relative bg-white rounded-lg shadow-xl w-full max-h-[90vh] overflow-y-auto', widthClass]"
    >
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
        <h2 class="text-base font-semibold text-slate-800">{{ title }}</h2>
        <button @click="emit('close')" class="text-slate-400 hover:text-slate-600" type="button">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div class="p-6">
        <slot />
      </div>
      <div v-if="$slots.footer" class="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50 rounded-b-lg">
        <slot name="footer" />
      </div>
    </div>
  </div>
</template>
