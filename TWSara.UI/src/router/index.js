import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/stores/auth'

export function dashboardRouteForRole() {
  return '/dashboard'
}

const routes = [
  {
    path: '/',
    name: 'landing',
    component: () => import('@/views/Landing.vue'),
    meta: { public: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/Register.vue'),
    meta: { public: true },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/Dashboard.vue'),
  },
  {
    path: '/leads',
    name: 'leads',
    component: () => import('@/views/LeadsList.vue'),
  },
  {
    path: '/leads/:id',
    name: 'lead-detail',
    component: () => import('@/views/LeadDetail.vue'),
    props: true,
  },
  {
    path: '/builders',
    name: 'builders',
    component: () => import('@/views/Builders.vue'),
  },
  {
    path: '/builders/:id',
    name: 'builder-detail',
    component: () => import('@/views/BuilderDetail.vue'),
    props: true,
  },
  {
    path: '/suggestions',
    name: 'suggestions',
    component: () => import('@/views/Suggestions.vue'),
  },
  {
    path: '/team-members',
    name: 'team-members',
    component: () => import('@/views/TeamMembers.vue'),
    meta: { adminOnly: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const { isAuthenticated, role } = useAuth()

  if (to.meta.public) {
    if (isAuthenticated.value) {
      return dashboardRouteForRole()
    }
    return true
  }

  if (!isAuthenticated.value) {
    return { name: 'login' }
  }

  if (to.meta.adminOnly && role.value !== 'admin') {
    return dashboardRouteForRole()
  }

  return true
})

export default router
