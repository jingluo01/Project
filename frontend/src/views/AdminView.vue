<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const API_BASE = 'http://127.0.0.1:5001/api'
const activeMenu = ref('dashboard')

// 数据
const summary = ref({})
const userList = ref([])
const orderList = ref([])
const sysConfig = ref({ rate: 1.0 })

// 搜索与分页
const searchKeyword = ref('')
const filteredOrders = computed(() => {
    if (!searchKeyword.value) return orderList.value
    const kw = searchKeyword.value.toLowerCase()
    return orderList.value.filter(o => 
        o.plate.toLowerCase().includes(kw) || 
        o.order_no.toLowerCase().includes(kw) ||
        o.username.includes(kw)
    )
})

// 图表
const lineChartRef = ref(null); const pieChartRef = ref(null)
let lineChart = null; let pieChart = null

// === API ===
const fetchData = async () => {
    try {
        const [res1, res2, res3, res4] = await Promise.all([
            axios.get(`${API_BASE}/parking/stats`),
            axios.get(`${API_BASE}/auth/users`),
            axios.get(`${API_BASE}/parking/admin/orders`),
            axios.get(`${API_BASE}/parking/admin/config`)
        ])
        summary.value = res1.data.data.summary
        userList.value = res2.data.data
        orderList.value = res3.data.data
        sysConfig.value = res4.data.data
        
        await nextTick()
        renderCharts(res1.data.data)
    } catch(e) { console.error(e) }
}

const renderCharts = (data) => {
    if (!lineChartRef.value) return
    if (lineChart) lineChart.dispose(); if (pieChart) pieChart.dispose()
    
    lineChart = echarts.init(lineChartRef.value)
    lineChart.setOption({
        title: { text: '营收趋势' }, tooltip: { trigger: 'axis' }, xAxis: { type: 'category', data: data.line_data.categories }, yAxis: {},
        series: [{ type: 'line', smooth: true, data: data.line_data.values, itemStyle: { color: '#409EFF' }, areaStyle: {} }]
    })
    pieChart = echarts.init(pieChartRef.value)
    pieChart.setOption({ title: { text: '车位分布', left: 'center' }, tooltip: {}, series: [{ type: 'pie', radius: ['40%', '70%'], data: data.pie_data }] })
}

// === 功能逻辑 ===
const saveConfig = async () => {
    await axios.post(`${API_BASE}/parking/admin/config`, { rate: sysConfig.value.rate })
    ElMessage.success('费率设置已保存，下一次计费生效')
}

// 导出 Excel (CSV格式)
const exportExcel = () => {
    const headers = ['订单号,用户名,车牌,状态,入场时间,费用\n']
    const rows = filteredOrders.value.map(o => 
        `${o.order_no},${o.username},${o.plate},${getOrderStatus(o.status)},${o.in_time},${o.fee}`
    )
    const blob = new Blob([headers + rows.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `停车订单报表_${new Date().toLocaleDateString()}.csv`
    link.click()
    ElMessage.success('报表下载成功')
}

const logout = () => { localStorage.clear(); router.push('/login') }
const getOrderStatus = (s) => ({0:'已预约',1:'停车中',2:'已完成',3:'待支付',4:'已取消'}[s] || '未知')
onMounted(fetchData)
</script>

<template>
  <div class="admin-layout">
    <div class="sidebar">
        <div class="logo">🎓 管理后台</div>
        <div class="menu">
            <div class="item" :class="{active: activeMenu==='dashboard'}" @click="activeMenu='dashboard'">📊 仪表盘</div>
            <div class="item" :class="{active: activeMenu==='users'}" @click="activeMenu='users'">👥 用户管理</div>
            <div class="item" :class="{active: activeMenu==='orders'}" @click="activeMenu='orders'">📝 订单报表</div>
            <div class="item" :class="{active: activeMenu==='settings'}" @click="activeMenu='settings'">⚙️ 系统设置</div>
        </div>
        <div class="item logout" @click="logout">🚪 退出</div>
    </div>

    <div class="content">
        <div v-show="activeMenu==='dashboard'" class="fade-in">
            <div class="cards">
                <el-card><h4>总营收</h4><h2>¥ {{ summary.total_income }}</h2></el-card>
                <el-card><h4>利用率</h4><h2 style="color:green">{{ summary.utilization }}%</h2></el-card>
            </div>
            <div class="charts"><div ref="lineChartRef" class="chart"></div><div ref="pieChartRef" class="chart"></div></div>
        </div>

        <div v-if="activeMenu==='orders'" class="fade-in">
            <div class="toolbar">
                <h2>📝 全局订单</h2>
                <div class="tools">
                    <el-input v-model="searchKeyword" placeholder="搜索车牌/订单号/用户" prefix-icon="Search" style="width: 250px; margin-right: 10px" />
                    <el-button type="success" icon="Download" @click="exportExcel">导出 Excel</el-button>
                </div>
            </div>
            <el-table :data="filteredOrders" border stripe height="500">
                <el-table-column prop="order_no" label="订单号" width="180" />
                <el-table-column prop="username" label="用户" width="100" />
                <el-table-column prop="plate" label="车牌" width="120" />
                <el-table-column label="状态"><template #default="s"><el-tag>{{ getOrderStatus(s.row.status) }}</el-tag></template></el-table-column>
                <el-table-column prop="in_time" label="入场时间" width="180" />
                <el-table-column prop="fee" label="费用" />
            </el-table>
        </div>

        <div v-if="activeMenu==='settings'" class="fade-in">
            <h2>⚙️ 系统参数设置</h2>
            <el-card style="max-width: 500px; margin-top: 20px;">
                <el-form label-width="120px">
                    <el-form-item label="停车单价">
                        <el-input-number v-model="sysConfig.rate" :precision="1" :step="0.5" :min="0" />
                        <span style="margin-left: 10px">元 / 分钟</span>
                    </el-form-item>
                    <el-form-item>
                        <el-button type="primary" @click="saveConfig">保存设置</el-button>
                    </el-form-item>
                </el-form>
                <el-alert title="修改后，后续出场的车辆将按新费率计费" type="info" :closable="false" style="margin-top: 20px" />
            </el-card>
        </div>
        
        <div v-if="activeMenu==='users'" class="fade-in">
            <h2>👥 用户列表</h2>
            <el-table :data="userList" border stripe><el-table-column prop="username" label="账号"/><el-table-column prop="real_name" label="姓名"/><el-table-column prop="credit" label="信用分"/><el-table-column prop="balance" label="余额"/></el-table>
        </div>
    </div>
  </div>
</template>

<style scoped>
.admin-layout { display: flex; height: 100vh; background: #f0f2f5; }
.sidebar { width: 220px; background: #001529; color: white; display: flex; flex-direction: column; }
.logo { height: 60px; line-height: 60px; text-align: center; font-size: 18px; font-weight: bold; background: #002140; }
.menu { flex: 1; }
.item { padding: 15px 20px; cursor: pointer; transition: 0.3s; }
.item:hover, .item.active { background: #1890ff; }
.logout { background: #d9363e; text-align: center; }
.content { flex: 1; padding: 20px; overflow: auto; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.charts { display: flex; gap: 20px; height: 350px; }
.chart { flex: 1; background: white; padding: 10px; border-radius: 4px; }
.cards { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.fade-in { animation: fadeIn 0.3s; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>