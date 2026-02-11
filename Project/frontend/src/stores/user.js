import { defineStore } from 'pinia'
import { login as loginApi, register as registerApi } from '@/api/auth'
import { getProfile } from '@/api/user'

export const useUserStore = defineStore('user', {
    state: () => ({
        token: localStorage.getItem('token') || '',
        user: JSON.parse(localStorage.getItem('user') || 'null'),
        cars: []
    }),

    getters: {
        isLoggedIn: (state) => !!state.token,
        isAdmin: (state) => state.user?.role === 3,
        username: (state) => state.user?.username || '',
        balance: (state) => state.user?.balance || 0,
        creditScore: (state) => state.user?.credit_score || 0
    },

    actions: {
        async login(credentials) {
            const res = await loginApi(credentials)
            this.token = res.data.token
            this.user = res.data.user

            localStorage.setItem('token', this.token)
            localStorage.setItem('user', JSON.stringify(this.user))

            return res
        },

        async register(userData) {
            const res = await registerApi(userData)
            this.token = res.data.token
            this.user = res.data.user

            localStorage.setItem('token', this.token)
            localStorage.setItem('user', JSON.stringify(this.user))

            return res
        },

        async fetchProfile() {
            const res = await getProfile()
            this.user = {
                user_id: res.data.user_id,
                user_no: res.data.user_no,
                username: res.data.username,
                role: res.data.role,
                balance: res.data.balance,
                credit_score: res.data.credit_score,
                is_active: res.data.is_active
            }
            this.cars = res.data.cars || []

            localStorage.setItem('user', JSON.stringify(this.user))

            return res
        },

        logout() {
            this.token = ''
            this.user = null
            this.cars = []

            localStorage.removeItem('token')
            localStorage.removeItem('user')
        },

        updateBalance(newBalance) {
            if (this.user) {
                this.user.balance = newBalance
                localStorage.setItem('user', JSON.stringify(this.user))
            }
        }
    }
})
