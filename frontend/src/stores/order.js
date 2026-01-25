import { defineStore } from 'pinia'
import { getOrders, createOrder as createOrderApi, payOrder as payOrderApi, cancelOrder as cancelOrderApi } from '@/api/order'
import { vehicleEnter, vehicleExit } from '@/api/parking'

export const useOrderStore = defineStore('order', {
    state: () => ({
        orders: [],
        currentOrder: null,
        loading: false
    }),

    getters: {
        // 正在进行的订单（预约中或停车中）
        activeOrder: (state) => {
            return state.orders.find(o => o.status === 0 || o.status === 1)
        },

        // 所有活跃订单列表 (支持多车展示)
        activeOrders: (state) => {
            return state.orders.filter(o => o.status === 0 || o.status === 1)
        },

        // 待支付的订单（正常出场待支付或超时违约）
        unpaidOrder: (state) => {
            return state.orders.find(o => o.status === 2 || o.status === 6)
        },

        // 所有待支付订单列表 (支持多个账单)
        unpaidOrders: (state) => {
            return state.orders.filter(o => o.status === 2 || o.status === 6)
        },

        // 底部展示的所有订单 (活跃+待支付)，保持稳定排序
        visibleOrders: (state) => {
            return state.orders.filter(o => [0, 1, 2, 6].includes(o.status))
        },

        // 所有订单列表
        orderList: (state) => state.orders
    },

    actions: {
        async fetchOrders(status = null, page = 1, perPage = 100) {
            this.loading = true
            try {
                const res = await getOrders(status, page, perPage)
                // 后端现在返回分页结构: { success: true, data: { orders: [], total: ... } }
                this.orders = res.data.orders || []
                return res
            } finally {
                this.loading = false
            }
        },

        async createOrder(orderData) {
            const res = await createOrderApi(orderData)
            await this.fetchOrders()
            return res
        },

        async payOrder(orderId, payWay = 0) {
            const res = await payOrderApi({ order_id: orderId, pay_way: payWay })
            await this.fetchOrders()
            // 支付成功后可能需要更新用户信息（余额）
            return res
        },

        async cancelOrder(orderId) {
            const res = await cancelOrderApi({ order_id: orderId })
            await this.fetchOrders()
            return res
        },

        async simulateEnter(plateNumber) {
            const res = await vehicleEnter({ plate_number: plateNumber })
            await this.fetchOrders()
            return res
        },

        async simulateExit(plateNumber) {
            // 用户手动操作，禁止自动支付，强制进入待支付状态
            const res = await vehicleExit({
                plate_number: plateNumber,
                auto_pay: false
            })
            await this.fetchOrders()
            return res
        },

        setCurrentOrder(order) {
            this.currentOrder = order
        }
    }
})
