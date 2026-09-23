import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('../Layout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'datasources', name: 'Datasource', component: () => import('../views/Datasource.vue') },
      { path: 'tasks', name: 'Task', component: () => import('../views/Task.vue') },
      { path: 'logs', name: 'Log', component: () => import('../views/Log.vue') },
      { path: 'settings', name: 'Settings', component: () => import('../views/Settings.vue'), meta: { adminOnly: true } }
    ]
  }
]

const router = createRouter({
  history: createWebHistory('/'),
  routes
})

// 路由守卫：未登录拦截
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) {
    return '/login'
  }
  if (to.path === '/login' && token) {
    return '/dashboard'
  }
  if (to.meta.adminOnly && JSON.parse(localStorage.getItem('user') || '{}').role !== 'admin') {
    return '/dashboard'
  }
  return true
})

export default router
