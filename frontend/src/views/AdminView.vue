<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { RefreshLeft, Check, Delete } from '@element-plus/icons-vue'
import websocketService from '@/services/websocket.js'

const router = useRouter()
const API_BASE = 'http://127.0.0.1:5001/api'
const activeMenu = ref('dashboard')

// 数据
const summary = ref({})
const userList = ref([])
const orderList = ref([])
const spotList = ref([])
const sysConfig = ref({ rate: 1.0 })
const realTimeStats = ref({})

// WebSocket 订阅管理
let unsubscribeSpots = null
let unsubscribeOrders = null
let unsubscribeStats = null

// 搜索与分页
const searchKeyword = ref('')
const userSearchKeyword = ref('')
const statusFilter = ref('')
const dateRange = ref([])

// 计算属性
const filteredOrders = computed(() => {
    let filtered = orderList.value
    
    // 关键词搜索
    if (searchKeyword.value) {
        const kw = searchKeyword.value.toLowerCase()
        filtered = filtered.filter(o => 
            o.plate.toLowerCase().includes(kw) || 
            o.order_no.toLowerCase().includes(kw) ||
            o.username.includes(kw)
        )
    }
    
    // 状态筛选
    if (statusFilter.value !== '') {
        filtered = filtered.filter(o => o.status == statusFilter.value)
    }
    
    return filtered
})

const filteredUsers = computed(() => {
    if (!userSearchKeyword.value) return userList.value
    const kw = userSearchKeyword.value.toLowerCase()
    return userList.value.filter(u => 
        u.username.toLowerCase().includes(kw) || 
        u.real_name.includes(kw)
    )
})

// 统计数据 - 使用后端统计接口的数据
const orderStats = computed(() => {
    // 如果有统计数据，使用统计接口的数据
    if (summary.value && summary.value.total_orders !== undefined) {
        return {
            total: summary.value.total_orders,
            reserved: summary.value.reserved_orders || 0,
            parking: summary.value.parking_orders || 0,
            completed: summary.value.completed_orders || 0,
            pending: summary.value.pending_orders || 0,
            cancelled: summary.value.cancelled_orders || 0,
            totalRevenue: summary.value.total_income || 0
        }
    }
    
    // 备用：从订单列表计算（保持兼容性）
    const stats = {
        total: orderList.value.length,
        reserved: orderList.value.filter(o => o.status === 0).length,
        parking: orderList.value.filter(o => o.status === 1).length,
        completed: orderList.value.filter(o => o.status === 2).length,
        pending: orderList.value.filter(o => o.status === 3).length,
        cancelled: orderList.value.filter(o => o.status === 4).length,
        totalRevenue: orderList.value.filter(o => o.status === 2).reduce((sum, o) => sum + parseFloat(o.fee || 0), 0)  // 只计算已完成订单的收入
    }
    return stats
})

// 图表
const lineChartRef = ref(null)
const pieChartRef = ref(null)
const revenueChartRef = ref(null)
let lineChart = null
let pieChart = null
let revenueChart = null

// 弹窗控制
const userEditDialog = ref(false)
const editingUser = ref({})
const orderDetailDrawer = ref(false)
const selectedOrder = ref({})

// === WebSocket 事件处理 ===
const setupWebSocket = () => {
  websocketService.connect()
  
  // 订阅车位更新
  unsubscribeSpots = websocketService.subscribe('spots_update', (data) => {
    spotList.value = data
  })
  
  // 订阅订单更新
  unsubscribeOrders = websocketService.subscribe('orders_update', (data) => {
    orderList.value = data
  })
  
  // 订阅统计数据更新
  unsubscribeStats = websocketService.subscribe('stats_update', (data) => {
    // 更新summary数据
    if (data && data.summary) {
      summary.value = data.summary
    }
    
    // 重新渲染图表
    nextTick(() => {
      renderCharts(data)
    })
  })
}

// === API ===
const fetchData = async () => {
    try {
        const [res1, res2, res3, res4, res5] = await Promise.all([
            axios.get(`${API_BASE}/parking/stats`),
            axios.get(`${API_BASE}/auth/users`),
            axios.get(`${API_BASE}/parking/admin/orders`),
            axios.get(`${API_BASE}/parking/admin/config`),
            axios.get(`${API_BASE}/parking/spots`)
        ])
        summary.value = res1.data.data.summary
        userList.value = res2.data.data
        orderList.value = res3.data.data
        sysConfig.value = res4.data.data
        spotList.value = res5.data.data
        
        await nextTick()
        renderCharts(res1.data.data)
    } catch(e) { 
        console.error(e)
        ElMessage.error('数据加载失败')
    }
}

// 页面刷新功能
const refreshPage = () => {
    window.location.reload()
}

const fetchUserData = async () => {
    try {
        const res = await axios.get(`${API_BASE}/auth/users`)
        userList.value = res.data.data
    } catch(e) {
        console.error(e)
    }
}

const fetchConfig = async () => {
    try {
        const res = await axios.get(`${API_BASE}/parking/admin/config`)
        sysConfig.value = res.data.data
    } catch(e) {
        console.error(e)
    }
}

const renderCharts = (data) => {
    // 检查必要的DOM元素
    if (!lineChartRef.value || !pieChartRef.value || !revenueChartRef.value) {
        console.error('图表DOM元素不存在')
        return
    }
    
    // 检查数据结构
    if (!data || !data.line_data || !data.pie_data) {
        console.error('图表数据结构不完整:', data)
        return
    }
    
    // 销毁现有图表实例
    if (lineChart) {
        lineChart.dispose()
        lineChart = null
    }
    if (pieChart) {
        pieChart.dispose()
        pieChart = null
    }
    if (revenueChart) {
        revenueChart.dispose()
        revenueChart = null
    }
    
    try {
        // 营收趋势图
        lineChart = echarts.init(lineChartRef.value)
        lineChart.setOption({
            title: { text: '营收趋势', textStyle: { fontSize: 16 } },
            tooltip: { trigger: 'axis', formatter: '{b}: ¥{c}' },
            xAxis: { 
                type: 'category', 
                data: data.line_data.categories || []
            },
            yAxis: { type: 'value', name: '营收(元)' },
            series: [{
                type: 'line',
                smooth: true,
                data: data.line_data.values || [],
                itemStyle: { color: '#409EFF' },
                areaStyle: { color: 'rgba(64, 158, 255, 0.1)' }
            }],
            grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true }
        })
        
        // 车位分布饼图
        pieChart = echarts.init(pieChartRef.value)
        pieChart.setOption({
            title: { text: '车位状态分布', left: 'center', textStyle: { fontSize: 16 } },
            tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c} ({d}%)' },
            series: [{
                name: '车位状态',
                type: 'pie',
                radius: ['40%', '70%'],
                data: data.pie_data || [],
                emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
            }]
        })
        
        // 订单状态统计图
        revenueChart = echarts.init(revenueChartRef.value)
        const statusData = [
            { name: '已完成', value: orderStats.value.completed },
            { name: '停车中', value: orderStats.value.parking },
            { name: '已预约', value: orderStats.value.reserved },
            { name: '待支付', value: orderStats.value.pending },
            { name: '已取消', value: orderStats.value.cancelled }
        ]
        revenueChart.setOption({
            title: { text: '订单状态统计', left: 'center', textStyle: { fontSize: 16 } },
            tooltip: { trigger: 'item' },
            series: [{
                type: 'pie',
                radius: '60%',
                data: statusData,
                emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
            }]
        })
    } catch (error) {
        console.error('图表渲染失败:', error)
    }
}

// === 功能逻辑 ===
const saveConfig = async () => {
    try {
        await axios.post(`${API_BASE}/parking/admin/config`, { rate: sysConfig.value.rate })
        ElMessage.success('费率设置已保存，下一次计费生效')
    } catch (e) {
        ElMessage.error('保存失败')
    }
}

// 用户管理
const editUser = (user) => {
    editingUser.value = { ...user }
    userEditDialog.value = true
}

const saveUser = async () => {
    try {
        await axios.post(`${API_BASE}/auth/admin/update_user`, {
            user_id: editingUser.value.id,
            credit: editingUser.value.credit,
            balance: editingUser.value.balance
        })
        ElMessage.success('用户信息更新成功')
        userEditDialog.value = false
        fetchUserData() // 刷新用户数据
    } catch (e) {
        ElMessage.error('更新失败')
    }
}

// 订单管理
const viewOrderDetail = (order) => {
    selectedOrder.value = order
    orderDetailDrawer.value = true
}

const refundOrder = async (order) => {
    try {
        await ElMessageBox.confirm('确定要退款此订单吗？退款金额将返回到用户余额。', '确认退款', {
            type: 'warning'
        })
        await axios.post(`${API_BASE}/parking/admin/refund`, { order_no: order.order_no })
        ElMessage.success('退款成功')
        // 数据会通过WebSocket自动更新
    } catch (e) {
        if (e !== 'cancel') {
            ElMessage.error('退款失败: ' + (e.response?.data?.msg || '未知错误'))
        }
    }
}

const deleteOrder = async (order) => {
    try {
        await ElMessageBox.confirm(
            `确定要删除订单 ${order.order_no} 吗？此操作不可恢复！${order.status === 2 && order.fee > 0 ? '\n注意：已完成订单删除时会自动退款到用户余额。' : ''}`, 
            '确认删除', 
            {
                type: 'error',
                confirmButtonText: '确定删除',
                cancelButtonText: '取消'
            }
        )
        await axios.post(`${API_BASE}/parking/admin/delete-order`, { order_no: order.order_no })
        ElMessage.success('订单删除成功')
        // 数据会通过WebSocket自动更新
    } catch (e) {
        if (e !== 'cancel') {
            ElMessage.error('删除失败: ' + (e.response?.data?.msg || '未知错误'))
        }
    }
}

// 导出功能增强
const exportExcel = () => {
    const headers = ['订单号,用户名,车牌,状态,预约时间,入场时间,出场时间,费用\n']
    const rows = filteredOrders.value.map(o => {
        const status = getOrderStatus(o.status)
        return `${o.order_no},${o.username},${o.plate},${status},${o.reserve_time || '-'},${o.in_time},${o.out_time || '-'},${o.fee}`
    })
    const blob = new Blob([headers + rows.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `停车订单报表_${new Date().toLocaleDateString()}.csv`
    link.click()
    ElMessage.success('报表下载成功')
}

const logout = () => { localStorage.clear(); router.push('/login') }
const getOrderStatus = (s) => ({0:'已预约',1:'停车中',2:'已完成',3:'待支付',4:'已取消'}[s] || '未知')
const getStatusType = (s) => ({0:'warning',1:'primary',2:'success',3:'danger',4:'info'}[s] || 'info')

onMounted(() => {
    // 初始化WebSocket连接
    setupWebSocket()
    
    // 只获取初始数据一次，后续通过WebSocket更新
    fetchData()
})

onUnmounted(() => {
    // 清理WebSocket订阅
    if (unsubscribeSpots) unsubscribeSpots()
    if (unsubscribeOrders) unsubscribeOrders()
    if (unsubscribeStats) unsubscribeStats()
})
</script>

<template>
  <div class="admin-layout">
    <div class="sidebar">
        <div class="logo">🎓 智能停车管理系统</div>
        <div class="menu">
            <div class="item" :class="{active: activeMenu==='dashboard'}" @click="activeMenu='dashboard'">
                <i class="icon">📊</i> 数据仪表盘
            </div>
            <div class="item" :class="{active: activeMenu==='spots'}" @click="activeMenu='spots'">
                <i class="icon">🅿️</i> 车位管理
            </div>
            <div class="item" :class="{active: activeMenu==='orders'}" @click="activeMenu='orders'">
                <i class="icon">📝</i> 订单管理
            </div>
            <div class="item" :class="{active: activeMenu==='users'}" @click="activeMenu='users'">
                <i class="icon">👥</i> 用户管理
            </div>
            <div class="item" :class="{active: activeMenu==='settings'}" @click="activeMenu='settings'">
                <i class="icon">⚙️</i> 系统设置
            </div>
        </div>
        <div class="item logout" @click="logout">🚪 退出登录</div>
    </div>

    <div class="content">
        <!-- 数据仪表盘 -->
        <div v-show="activeMenu==='dashboard'" class="fade-in">
            <div class="page-header">
                <h1>📊 数据仪表盘</h1>
                <div class="header-actions">
                    <el-button type="primary" @click="refreshPage">刷新</el-button>
                </div>
            </div>
            
            <!-- 统计卡片 -->
            <div class="stats-cards">
                <el-card class="stat-card">
                    <div class="stat-content">
                        <div class="stat-icon revenue">💰</div>
                        <div class="stat-info">
                            <h3>¥ {{ summary.total_income }}</h3>
                            <p>总营收</p>
                        </div>
                    </div>
                </el-card>
                <el-card class="stat-card">
                    <div class="stat-content">
                        <div class="stat-icon utilization">📈</div>
                        <div class="stat-info">
                            <h3>{{ summary.utilization }}%</h3>
                            <p>车位利用率</p>
                        </div>
                    </div>
                </el-card>
                <el-card class="stat-card">
                    <div class="stat-content">
                        <div class="stat-icon orders">📋</div>
                        <div class="stat-info">
                            <h3>{{ orderStats.total }}</h3>
                            <p>总订单数</p>
                        </div>
                    </div>
                </el-card>
                <el-card class="stat-card">
                    <div class="stat-content">
                        <div class="stat-icon users">👥</div>
                        <div class="stat-info">
                            <h3>{{ userList.length }}</h3>
                            <p>注册用户</p>
                        </div>
                    </div>
                </el-card>
            </div>

            <!-- 图表区域 -->
            <div class="charts-container">
                <el-card class="chart-card">
                    <div ref="lineChartRef" class="chart"></div>
                </el-card>
                <el-card class="chart-card">
                    <div ref="pieChartRef" class="chart"></div>
                </el-card>
                <el-card class="chart-card">
                    <div ref="revenueChartRef" class="chart"></div>
                </el-card>
            </div>
        </div>

        <!-- 车位管理 -->
        <div v-if="activeMenu==='spots'" class="fade-in">
            <div class="page-header">
                <h1>🅿️ 车位管理</h1>
                <div class="header-actions">
                    <el-button type="primary" @click="refreshPage">刷新</el-button>
                </div>
            </div>
            
            <div class="spots-grid">
                <el-card v-for="spot in spotList" :key="spot.id" class="spot-card" :class="'spot-status-' + spot.status">
                    <div class="spot-header">
                        <h3>{{ spot.no }}</h3>
                        <el-tag :type="spot.status === 0 ? 'success' : spot.status === 1 ? 'danger' : 'warning'">
                            {{ spot.status === 0 ? '空闲' : spot.status === 1 ? '占用' : '预约' }}
                        </el-tag>
                    </div>
                    <div class="spot-info">
                        <p><strong>区域:</strong> {{ spot.area }}</p>
                        <p v-if="spot.current_plate"><strong>车牌:</strong> {{ spot.current_plate }}</p>
                        <p v-if="spot.current_order"><strong>订单:</strong> {{ spot.current_order }}</p>
                    </div>
                </el-card>
            </div>
        </div>

        <!-- 订单管理 -->
        <div v-if="activeMenu==='orders'" class="fade-in">
            <div class="page-header">
                <h1>📝 订单管理</h1>
                <div class="header-actions">
                    <el-button type="success" icon="Download" @click="exportExcel">导出报表</el-button>
                    <el-button type="primary" @click="refreshPage">刷新</el-button>
                </div>
            </div>
            
            <!-- 筛选工具栏 -->
            <el-card class="filter-card">
                <div class="filters">
                    <el-input 
                        v-model="searchKeyword" 
                        placeholder="搜索车牌/订单号/用户" 
                        prefix-icon="Search" 
                        style="width: 250px; margin-right: 15px"
                        clearable
                    />
                    <el-select v-model="statusFilter" placeholder="订单状态" style="width: 150px; margin-right: 15px" clearable>
                        <el-option label="已预约" :value="0" />
                        <el-option label="停车中" :value="1" />
                        <el-option label="已完成" :value="2" />
                        <el-option label="待支付" :value="3" />
                        <el-option label="已取消" :value="4" />
                    </el-select>
                    <el-date-picker
                        v-model="dateRange"
                        type="daterange"
                        range-separator="至"
                        start-placeholder="开始日期"
                        end-placeholder="结束日期"
                        style="margin-right: 15px"
                    />
                </div>
                
                <!-- 统计信息 -->
                <div class="order-stats">
                    <el-tag class="stat-tag">总计: {{ orderStats.total }}</el-tag>
                    <el-tag class="stat-tag" type="warning">已预约: {{ orderStats.reserved }}</el-tag>
                    <el-tag class="stat-tag" type="primary">停车中: {{ orderStats.parking }}</el-tag>
                    <el-tag class="stat-tag" type="success">已完成: {{ orderStats.completed }}</el-tag>
                    <el-tag class="stat-tag" type="danger">待支付: {{ orderStats.pending }}</el-tag>
                    <el-tag class="stat-tag" type="info">已取消: {{ orderStats.cancelled }}</el-tag>
                    <el-tag class="stat-tag revenue-tag">总收入: ¥{{ orderStats.totalRevenue.toFixed(2) }}</el-tag>
                </div>
            </el-card>

            <!-- 订单表格 -->
            <el-card>
                <el-table :data="filteredOrders" border stripe height="500" v-loading="false">
                    <el-table-column prop="order_no" label="订单号" width="180" />
                    <el-table-column prop="username" label="用户" width="100" />
                    <el-table-column prop="plate" label="车牌" width="120" />
                    <el-table-column label="状态" width="100">
                        <template #default="{ row }">
                            <el-tag :type="getStatusType(row.status)">{{ getOrderStatus(row.status) }}</el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column prop="in_time" label="入场时间" width="180" />
                    <el-table-column label="费用" width="100">
                        <template #default="{ row }">
                            <span v-if="row.fee > 0" style="color: #f56c6c; font-weight: bold">¥{{ row.fee }}</span>
                            <span v-else>-</span>
                        </template>
                    </el-table-column>
                    <el-table-column label="操作" width="200">
                        <template #default="{ row }">
                            <el-button size="small" @click="viewOrderDetail(row)">详情</el-button>
                            <el-button v-if="row.status === 2" size="small" type="warning" @click="refundOrder(row)">退款</el-button>
                            <el-button v-if="row.status === 2 || row.status === 4" size="small" type="danger" @click="deleteOrder(row)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-card>
        </div>

        <!-- 用户管理 -->
        <div v-if="activeMenu==='users'" class="fade-in">
            <div class="page-header">
                <h1>👥 用户管理</h1>
                <div class="header-actions">
                    <el-input 
                        v-model="userSearchKeyword" 
                        placeholder="搜索用户名/姓名" 
                        prefix-icon="Search" 
                        style="width: 200px; margin-right: 10px"
                        clearable
                    />
                    <el-button type="primary" @click="refreshPage">刷新</el-button>
                </div>
            </div>
            
            <el-card>
                <el-table :data="filteredUsers" border stripe>
                    <el-table-column prop="username" label="账号" width="120" />
                    <el-table-column prop="real_name" label="姓名" width="120" />
                    <el-table-column label="信用分" width="100">
                        <template #default="{ row }">
                            <el-tag :type="row.credit >= 80 ? 'success' : 'danger'">{{ row.credit }}</el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column label="余额" width="120">
                        <template #default="{ row }">
                            <span style="color: #409eff; font-weight: bold">¥{{ row.balance }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column label="操作" width="120">
                        <template #default="{ row }">
                            <el-button size="small" type="primary" @click="editUser(row)">编辑</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-card>
        </div>

        <!-- 系统设置 -->
        <div v-if="activeMenu==='settings'" class="fade-in">
            <div class="page-header">
                <h1>⚙️ 系统设置</h1>
            </div>
            
            <div class="settings-container">
                <el-card class="setting-card">
                    <template #header>
                        <h3>💰 费率设置</h3>
                    </template>
                    <el-form label-width="120px">
                        <el-form-item label="停车单价">
                            <el-input-number 
                                v-model="sysConfig.rate" 
                                :precision="1" 
                                :step="0.5" 
                                :min="0" 
                                :max="10"
                            />
                            <span style="margin-left: 10px">元 / 分钟</span>
                        </el-form-item>
                        <el-form-item>
                            <el-button type="primary" @click="saveConfig">保存设置</el-button>
                        </el-form-item>
                    </el-form>
                    <el-alert 
                        title="修改后，后续出场的车辆将按新费率计费" 
                        type="info" 
                        :closable="false" 
                        style="margin-top: 20px" 
                    />
                </el-card>
                
                <el-card class="setting-card">
                    <template #header>
                        <h3>🔧 系统维护</h3>
                    </template>
                    <div class="maintenance-actions">
                        <el-button type="info" @click="refreshPage">刷新页面</el-button>
                    </div>
                </el-card>
            </div>
        </div>
    </div>

    <!-- 用户编辑弹窗 -->
    <el-dialog v-model="userEditDialog" title="编辑用户信息" width="400px">
        <el-form :model="editingUser" label-width="80px">
            <el-form-item label="用户名">
                <el-input v-model="editingUser.username" disabled />
            </el-form-item>
            <el-form-item label="姓名">
                <el-input v-model="editingUser.real_name" disabled />
            </el-form-item>
            <el-form-item label="信用分">
                <el-input-number v-model="editingUser.credit" :min="0" :max="100" />
            </el-form-item>
            <el-form-item label="余额">
                <el-input-number v-model="editingUser.balance" :precision="2" :min="0" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="userEditDialog = false">取消</el-button>
            <el-button type="primary" @click="saveUser">保存</el-button>
        </template>
    </el-dialog>

    <!-- 订单详情侧边抽屉 -->
    <el-drawer v-model="orderDetailDrawer" title="订单详情" size="400px" direction="rtl">
        <div class="order-detail-drawer">
            <el-descriptions :column="1" border>
                <el-descriptions-item label="订单号">
                    <el-tag type="info">{{ selectedOrder.order_no }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="用户姓名">
                    <span class="user-name">{{ selectedOrder.username }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="车牌号码">
                    <el-tag class="plate-tag">{{ selectedOrder.plate }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="订单状态">
                    <el-tag :type="getStatusType(selectedOrder.status)" size="large">
                        {{ getOrderStatus(selectedOrder.status) }}
                    </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="预约时间">
                    <span class="time-info">{{ selectedOrder.reserve_time || '未预约' }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="入场时间">
                    <span class="time-info">{{ selectedOrder.in_time || '未入场' }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="出场时间">
                    <span class="time-info">{{ selectedOrder.out_time || '未出场' }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="停车费用">
                    <div class="fee-info">
                        <span v-if="selectedOrder.fee > 0" class="fee-amount">¥{{ selectedOrder.fee }}</span>
                        <span v-else class="no-fee">免费</span>
                    </div>
                </el-descriptions-item>
            </el-descriptions>
            
            <!-- 操作按钮区域 -->
            <div class="drawer-actions">
                <el-button v-if="selectedOrder.status === 2" type="warning" size="large" @click="refundOrder(selectedOrder)">
                    <el-icon><RefreshLeft /></el-icon>
                    申请退款
                </el-button>
                <el-button v-if="selectedOrder.status === 2 || selectedOrder.status === 4" type="danger" size="large" @click="deleteOrder(selectedOrder)">
                    <el-icon><Delete /></el-icon>
                    删除订单
                </el-button>
                <el-button type="primary" size="large" @click="orderDetailDrawer = false">
                    <el-icon><Check /></el-icon>
                    确定
                </el-button>
            </div>
        </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.admin-layout { 
    display: flex; 
    height: 100vh; 
    background: #f0f2f5; 
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.sidebar { 
    width: 260px; 
    background: linear-gradient(180deg, #001529 0%, #002140 100%);
    color: white; 
    display: flex; 
    flex-direction: column;
    box-shadow: 2px 0 8px rgba(0,0,0,0.1);
}

.logo { 
    height: 70px; 
    line-height: 70px; 
    text-align: center; 
    font-size: 16px; 
    font-weight: bold; 
    background: rgba(0,0,0,0.2);
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.menu { flex: 1; padding: 20px 0; }

.item { 
    padding: 15px 25px; 
    cursor: pointer; 
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    margin: 0 15px;
    border-radius: 8px;
}

.item .icon {
    margin-right: 10px;
    font-size: 16px;
}

.item:hover { 
    background: rgba(24, 144, 255, 0.8);
    transform: translateX(5px);
}

.item.active { 
    background: #1890ff;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.logout { 
    background: #d9363e; 
    text-align: center; 
    margin: 15px;
    border-radius: 8px;
    font-weight: bold;
}

.logout:hover {
    background: #c73030;
    transform: none;
}

.content { 
    flex: 1; 
    padding: 30px; 
    overflow: auto;
    background: #f0f2f5;
}

.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    padding: 0 5px;
}

.page-header h1 {
    margin: 0;
    font-size: 24px;
    color: #262626;
    font-weight: 600;
}

.header-actions {
    display: flex;
    gap: 10px;
}

/* 统计卡片样式 */
.stats-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.stat-card {
    border: none;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.stat-content {
    display: flex;
    align-items: center;
    padding: 10px;
}

.stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    margin-right: 20px;
}

.stat-icon.revenue { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.stat-icon.utilization { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.stat-icon.orders { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.stat-icon.users { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }

.stat-info h3 {
    margin: 0 0 5px 0;
    font-size: 28px;
    font-weight: bold;
    color: #262626;
}

.stat-info p {
    margin: 0;
    color: #8c8c8c;
    font-size: 14px;
}

/* 图表容器 */
.charts-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 30px;
}

.chart-card {
    border: none;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.chart-card:nth-child(3) {
    grid-column: 1 / -1;
}

.chart {
    height: 350px;
    padding: 20px;
}

/* 车位网格 */
.spots-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
}

.spot-card {
    border: none;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
}

.spot-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.12);
}

.spot-card.spot-status-0 { border-left: 4px solid #52c41a; }
.spot-card.spot-status-1 { border-left: 4px solid #ff4d4f; }
.spot-card.spot-status-2 { border-left: 4px solid #1890ff; }

.spot-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.spot-header h3 {
    margin: 0;
    font-size: 18px;
    font-weight: bold;
}

.spot-info p {
    margin: 8px 0;
    color: #595959;
}

/* 筛选卡片 */
.filter-card {
    margin-bottom: 20px;
    border: none;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.filters {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 15px;
    margin-bottom: 20px;
}

.order-stats {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.stat-tag {
    padding: 8px 12px;
    border-radius: 6px;
    font-weight: 500;
}

.revenue-tag {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
}

/* 设置页面 */
.settings-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
}

.setting-card {
    border: none;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.maintenance-actions {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

/* 订单详情抽屉 */
.order-detail-drawer {
    padding: 20px;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.order-detail-drawer .el-descriptions {
    flex: 1;
    margin-bottom: 30px;
}

.order-detail-drawer .el-descriptions-item__label {
    font-weight: 600;
    color: #303133;
    background-color: #f8f9fa;
}

.order-detail-drawer .el-descriptions-item__content {
    padding: 12px 16px;
}

.user-name {
    font-size: 16px;
    font-weight: 500;
    color: #409eff;
}

.plate-tag {
    font-family: 'Courier New', monospace;
    font-weight: bold;
    font-size: 14px;
    letter-spacing: 1px;
}

.time-info {
    font-size: 14px;
    color: #606266;
}

.fee-info {
    display: flex;
    align-items: center;
}

.fee-amount {
    font-size: 18px;
    font-weight: bold;
    color: #f56c6c;
}

.no-fee {
    font-size: 14px;
    color: #909399;
}

.drawer-actions {
    display: flex;
    gap: 12px;
    padding-top: 20px;
    border-top: 1px solid #ebeef5;
}

.drawer-actions .el-button {
    flex: 1;
    height: 44px;
    font-size: 16px;
    border-radius: 8px;
}

/* 动画效果 */
.fade-in { 
    animation: fadeIn 0.4s ease-out; 
}

@keyframes fadeIn { 
    from { 
        opacity: 0; 
        transform: translateY(20px); 
    } 
    to { 
        opacity: 1; 
        transform: translateY(0); 
    } 
}

/* 响应式设计 */
@media (max-width: 1200px) {
    .stats-cards {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .charts-container {
        grid-template-columns: 1fr;
    }
    
    .settings-container {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .admin-layout {
        flex-direction: column;
    }
    
    .sidebar {
        width: 100%;
        height: auto;
    }
    
    .menu {
        display: flex;
        overflow-x: auto;
        padding: 10px;
    }
    
    .item {
        white-space: nowrap;
        margin: 0 5px;
    }
    
    .stats-cards {
        grid-template-columns: 1fr;
    }
    
    .content {
        padding: 20px;
    }
}

/* Element Plus 组件样式覆盖 */
.el-card {
    border: none;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.el-table {
    border-radius: 8px;
    overflow: hidden;
}

.el-button {
    border-radius: 6px;
    font-weight: 500;
}

.el-input {
    border-radius: 6px;
}

.el-select {
    border-radius: 6px;
}
</style>