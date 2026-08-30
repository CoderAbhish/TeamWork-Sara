<script setup>
import { onMounted, ref } from 'vue'

defineProps({
  title: { type: String, default: '' },
  // A full Tailwind class incl. the sm: prefix (e.g. "sm:max-w-lg") —
  // applies only at sm: and up, since below that the modal is a
  // full-screen sheet with no width cap (item 20). The prefix has to be
  // written out literally by the caller (not built with string
  // concatenation here) so Tailwind's build-time scanner can see it.
  // Ideally capped at sm:max-w-lg (~600px, item 13).
  widthClass: { type: String, default: 'sm:max-w-lg' },
})
const emit = defineEmits(['close'])

const bodyRef = ref(null)

// Focus the first field on open (item 19) — scrollIntoView is a defensive
// belt-and-braces since most mobile browsers already do this when a virtual
// keyboard opens, but not every WebView does it reliably.
onMounted(() => {
  const first = bodyRef.value?.querySelector('input, select, textarea, button')
  first?.focus({ preventScroll: true })
  first?.scrollIntoView({ block: 'center' })
})

function onBodyFocusIn(event) {
  event.target.scrollIntoView?.({ block: 'center', behavior: 'smooth' })
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center sm:p-4">
    <div class="absolute inset-0 bg-ink-900/50" @click="emit('close')"></div>
    <div
      :class="['relative bg-white shadow-xl w-full flex flex-col h-dvh sm:h-auto sm:max-h-[90vh] sm:rounded-lg', widthClass]"
    >
      <div class="flex items-center justify-between px-4 sm:px-6 py-4 border-b border-slate-200 shrink-0">
        <h2 class="text-base font-semibold text-slate-800">{{ title }}</h2>
        <button @click="emit('close')" class="tap-target flex items-center justify-center text-slate-400 hover:text-slate-600" type="button">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div ref="bodyRef" class="p-4 sm:p-6 flex-1 overflow-y-auto" @focusin="onBodyFocusIn">
        <slot />
      </div>
      <div
        v-if="$slots.footer"
        class="flex justify-end gap-3 px-4 sm:px-6 py-4 border-t border-slate-200 bg-slate-50 shrink-0 sm:rounded-b-lg"
        style="padding-bottom: max(1rem, env(safe-area-inset-bottom))"
      >
        <slot name="footer" />
      </div>
    </div>
  </div>
</template>
