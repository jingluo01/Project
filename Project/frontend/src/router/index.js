import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/Login.vue'),
        meta: { requiresAuth: false }
    },
    {
        path: '/register',
        name: 'Register',
        component: () => import('@/views/Register.vue'),
        meta: { requiresAuth: false }
    },
    {
        path: '/',
        redirect: '/parking'
    },
    {
        path: '/parking',
        name: 'ParkingMap',
        component: () => import('@/views/ParkingMap.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/profile',
        name: 'UserProfile',
        component: () => import('@/views/UserProfile.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/orders',
        name: 'OrderHistory',
        component: () => import('@/views/OrderHistory.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/admin',
        component: () => import('@/views/admin/AdminLayout.vue'),
        redirect: '/admin/dashboard',
        meta: { requiresAuth: true, requiresAdmin: true },
        children: [
            {
                path: 'dashboard',
                name: 'AdminDashboard',
                component: () => import('@/views/admin/Dashboard.vue')
            },
            {
                path: 'users',
                name: 'UserManagement',
                component: () => import('@/views/admin/UserManagement.vue')
            },
            {
                path: 'parking',
                name: 'ParkingManagement',
                component: () => import('@/views/admin/ParkingManagement.vue')
            },
            {
                path: 'orders',
                name: 'OrderManagement',
                component: () => import('@/views/admin/OrderManagement.vue')
            },
            {
                path: 'settings',
                name: 'SystemSettings',
                component: () => import('@/views/admin/SystemSettings.vue')
            }
        ]
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
    const userStore = useUserStore()

    if (to.meta.requiresAuth && !userStore.isLoggedIn) {
        next('/login')
    } else if (to.meta.requiresAdmin && !userStore.isAdmin) {
        next('/parking')
    } else if ((to.path === '/login' || to.path === '/register') && userStore.isLoggedIn) {
        // Redirect to appropriate dashboard based on role
        if (userStore.isAdmin) {
            next('/admin/dashboard')
        } else {
            next('/parking')
        }
    } else {
        next()
    }
})

export default router
