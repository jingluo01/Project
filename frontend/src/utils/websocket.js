import { io } from 'socket.io-client'
import { useParkingStore } from '@/stores/parking'
import { useUserStore } from '@/stores/user'
import { ElMessageBox, ElMessage } from 'element-plus'
import router from '@/router'

let socket = null

export const initWebSocket = () => {
    if (socket) return socket

    const token = localStorage.getItem('token')

    socket = io({
        path: '/socket.io',
        autoConnect: true,
        auth: {
            token: token
        }
    })

    socket.on('connect', () => {
        console.log('WebSocket connected')
    })

    socket.on('disconnect', () => {
        console.log('WebSocket disconnected')
    })

    socket.on('spot_status_update', (data) => {
        console.log('Spot status update:', data)
        const parkingStore = useParkingStore()
        parkingStore.updateSpotStatus(data.spot_id, data.status, data.current_plate)
    })

    // 监听实时踢出事件
    socket.on('kickout', (data) => {
        console.log('Received kickout command:', data)
        const userStore = useUserStore()

        // 1. 立即停止任何后台轮询/连接，防止继续发起 API 请求
        closeWebSocket()

        // 2. 清除状态
        userStore.logout()

        // 3. 弹出非阻塞通知，告知用户原因
        ElMessage({
            message: data.message || '您的账号已在别处登录，正在退出...',
            type: 'warning',
            duration: 3000,
            showClose: true
        })

        // 4. 强制直接跳转，绕过路由拦截器，确保立即生效
        // 使用 window.location.href 可以执行硬跳转，彻底销毁内存中的任何残留状态
        window.location.href = '/login?reason=kickout'
    })

    return socket
}

export const closeWebSocket = () => {
    if (socket) {
        socket.close()
        socket = null
    }
}

export const getSocket = () => socket
