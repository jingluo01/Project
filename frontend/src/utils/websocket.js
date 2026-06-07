import { io } from 'socket.io-client'
import { useParkingStore } from '@/stores/parking'
import { useUserStore } from '@/stores/user'
import { useOrderStore } from '@/stores/order'
import { ElMessageBox, ElMessage } from 'element-plus'
import router from '@/router'

let socket = null

export const initWebSocket = () => {
    if (socket) return socket

    const token = localStorage.getItem('token')

    const targetUrl = import.meta.env.DEV ? 'http://127.0.0.1:5000' : undefined
    socket = io(targetUrl, {
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

    socket.on('order_status_update', (data) => {
        console.log('Order status update:', data)
        const userStore = useUserStore()
        const orderStore = useOrderStore()
        
        // 如果是普通用户，且更新的订单是自己的，刷新用户个人的订单列表与资产
        if (data.user_id === userStore.user?.user_id) {
            orderStore.fetchOrders()
            userStore.fetchProfile() // 更新可能变动的钱包和信用分
        }
        
        // 派发全局事件供后台管理大盘或订单列表刷新
        window.dispatchEvent(new CustomEvent('admin_order_refresh', { detail: data }))
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
