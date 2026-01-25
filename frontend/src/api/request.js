import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
    baseURL: '/api',
    timeout: 10000
})

// Request interceptor
request.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    error => {
        return Promise.reject(error)
    }
)

// Response interceptor
request.interceptors.response.use(
    response => {
        const res = response.data

        if (res.success === false) {
            ElMessage.error(res.message || '请求失败')
            return Promise.reject(new Error(res.message || '请求失败'))
        }

        return res
    },
    error => {
        if (error.response) {
            const { status, data } = error.response

            if (status === 401) {
                ElMessage.error('登录已过期，请重新登录')
                localStorage.removeItem('token')
                localStorage.removeItem('user')
                router.push('/login')
            } else if (status === 403) {
                ElMessage.error(data.message || '没有权限')
            } else if (status === 404) {
                ElMessage.error(data.message || '资源不存在')
            } else {
                ElMessage.error(data.message || '服务器错误')
            }
        } else {
            ElMessage.error('网络连接失败')
        }

        return Promise.reject(error)
    }
)

export default request
