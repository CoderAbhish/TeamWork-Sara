<script setup>
import Modal from './Modal.vue'

defineProps({
  title: { type: String, default: 'Confirm' },
  message: { type: String, required: true },
  confirmLabel: { type: String, default: 'Confirm' },
  cancelLabel: { type: String, default: 'Cancel' },
})
const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <Modal :title="title" width-class="max-w-md" @close="emit('cancel')">
    <p class="text-sm text-slate-700 whitespace-pre-line">{{ message }}</p>

    <template #footer>
      <button @click="emit('cancel')" class="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
        {{ cancelLabel }}
      </button>
      <button @click="emit('confirm')" class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 text-white text-sm font-semibold">
        {{ confirmLabel }}
      </button>
    </template>
  </Modal>
</template>
