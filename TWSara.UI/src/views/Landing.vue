<script setup>
import { onMounted, ref } from 'vue'
import KpiTile from '@/components/ui/KpiTile.vue'
import { getPublicStats } from '@/api/analytics'
import landingImage from '@/imgs/landing.jpg'

const stats = ref(null)

onMounted(async () => {
  stats.value = await getPublicStats()
})
</script>

<template>
  <div class="min-h-dvh bg-slate-50">
    <nav class="w-full bg-white border-b border-slate-200">
      <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <span class="text-xl font-semibold tracking-tight text-ink-900">
          Sara<span class="text-brand-500">Hive</span>
        </span>
        <div class="flex items-center gap-3">
          <router-link to="/login" class="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
            Sign In
          </router-link>
          <router-link
            to="/register"
            class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 text-white text-sm font-semibold transition-colors"
          >
            Join as Team Member
          </router-link>
        </div>
      </div>
    </nav>

    <section class="relative w-full h-[480px] overflow-hidden">
      <img :src="landingImage" alt="Real estate skyline" class="absolute inset-0 w-full h-full object-cover" />
      <div class="absolute inset-0 bg-gradient-to-r from-ink-900/85 via-ink-900/60 to-ink-900/20"></div>
      <div class="relative max-w-6xl mx-auto px-6 h-full flex items-center">
        <div class="max-w-xl text-white">
          <p class="text-sm font-medium tracking-wide uppercase text-brand-300 mb-3">Internal Workspace</p>
          <h1 class="text-4xl font-semibold tracking-tight mb-4 leading-tight">
            The hive where Team Sara turns leads into homes closed.
          </h1>
          <p class="text-slate-200 leading-relaxed mb-8">
            SaraHive is where the Sara Honeycomb team tracks builders, projects and
            every lead from first contact to closed deal — one shared, organized
            workspace for the whole team.
          </p>
          <div class="flex gap-3">
            <router-link
              to="/login"
              class="px-6 py-3 rounded-md bg-brand-500 hover:bg-brand-600 text-white text-sm font-semibold transition-colors shadow-lg"
            >
              Sign In
            </router-link>
            <router-link
              to="/register"
              class="px-6 py-3 rounded-md bg-white/10 hover:bg-white/20 border border-white/30 text-white text-sm font-semibold transition-colors"
            >
              Register as Team Member
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <section class="max-w-6xl mx-auto px-6 py-12">
      <p class="text-sm font-medium text-slate-500 uppercase tracking-wide mb-4 text-center">Where we stand today</p>
      <div v-if="stats" class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiTile label="Leads managed" :value="stats.totalLeads" />
        <KpiTile label="Builder partners" :value="stats.totalBuilders" />
        <KpiTile label="Team members" :value="stats.totalTeamMembers" />
        <KpiTile label="Conversion rate" :value="`${stats.conversionRate}%`" />
      </div>
    </section>

    <footer class="border-t border-slate-200 py-6 text-center text-xs text-slate-400">
      SaraHive — internal workspace for the Sara Honeycomb team.
    </footer>
  </div>
</template>
