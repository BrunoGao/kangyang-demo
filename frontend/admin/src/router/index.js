import { createRouter, createWebHistory } from 'vue-router'
import ModernLayout from '@/components/ModernLayout.vue'

const routes = [
  {
    path: '/',
    component: ModernLayout,
    redirect: '/dashboard',
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/ModernDashboard.vue'),
        meta: { title: '智能监控中心', icon: 'Odometer' }
      },
      {
        path: '/events',
        name: 'Events',
        component: () => import('@/views/Events.vue'),
        meta: { title: '告警事件', icon: 'Warning' }
      },
      {
        path: '/cameras',
        name: 'Cameras',
        component: () => import('@/views/Cameras.vue'),
        meta: { title: '摄像头管理', icon: 'VideoCamera' }
      },
      {
        path: '/monitor',
        name: 'Monitor',
        component: () => import('@/views/Monitor.vue'),
        meta: { title: '实时监控', icon: 'Monitor' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router