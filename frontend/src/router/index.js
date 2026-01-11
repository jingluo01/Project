import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import AdminView from '../views/AdminView.vue'
// 👇 1. 引入新页面组件
import ProfileView from '../views/ProfileView.vue' 

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminView
    },
    // 👇 2. 注册路由：/profile
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView
    }
  ]
})

// === 全局路由守卫 ===
router.beforeEach((to, from, next) => {
  const userStr = localStorage.getItem('user')
  const user = userStr ? JSON.parse(userStr) : null
  
  // 去登录页直接放行
  if (to.name === 'login') {
    next()
    return
  }

  // 没登录强制踢回登录页
  if (!user) {
    next({ name: 'login' })
    return
  }

  // 权限校验：非管理员不能进 admin
  if (to.path.startsWith('/admin') && user.role !== 'admin') {
     next({ name: 'dashboard' })
     return
  }

  next()
})

export default router