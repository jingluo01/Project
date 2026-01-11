<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const API_BASE = 'http://127.0.0.1:5001/api'

// 数据状态
const spots = ref([])
const orderList = ref([]) 
const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
const loading = ref(false)
const myPlates = ref([]) // 我的车牌列表

// 弹窗控制
const dialogVisible = ref(false)
const dialogTitle = ref('')
const currentAction = ref('') 
const activeSpot = ref(null)  
const form = ref({ plate: '', fee: 0, duration: '' }) 
const paymentMethod = ref('balance')
const activeArea = ref('A')

const filteredSpots = computed(() => spots.value.filter(spot => spot.area === activeArea.value))

// === 1. API请求 ===
const fetchSpots = async () => {
    try {
        const res = await axios.get(`${API_BASE}/parking/spots`)
        spots.value = res.data.data
    } catch (err) { console.error(err) }
}

const fetchOrders = async () => {
    if(!user.value) return
    try {
        const res = await axios.get(`${API_BASE}/parking/orders?user_id=${user.value.id}`)
        orderList.value = res.data.data
    } catch (err) { console.error(err) }
}

// 【关键修改】获取用户信息并同步车牌
const fetchUserProfile = async () => {
    if(!user.value) return
    try {
        const res = await axios.get(`${API_BASE}/auth/profile?user_id=${user.value.id}`)
        user.value.credit = res.data.data.credit
        user.value.balance = res.data.data.balance
        
        // 核心：如果有返回车牌，就更新到 myPlates
        if (res.data.data.plates) {
            myPlates.value = res.data.data.plates
        }
        
        localStorage.setItem('user', JSON.stringify(user.value))
    } catch (err) { console.error(err) }
}

// === 2. 交互逻辑 ===
const handleSpotClick = (spot) => {
    activeSpot.value = spot
    form.value = { plate: '', fee: 0, duration: '' }

    if (spot.status === 0) {
        if (user.value.credit < 80) return ElMessage.error(`信用分不足 (${user.value.credit})，无法预约`)
        
        dialogTitle.value = `预约车位 ${spot.no}`
        currentAction.value = 'reserve'
        // 自动填入第一辆车
        if (myPlates.value.length > 0) form.value.plate = myPlates.value[0]
        dialogVisible.value = true
    }
    else if (spot.status === 2) {
        dialogTitle.value = `入场识别 (${spot.no})`
        currentAction.value = 'enter'
        form.value.plate = spot.current_plate 
        dialogVisible.value = true
    }
    else if (spot.status === 1) {
        dialogTitle.value = `出场结算 (${spot.no})`
        currentAction.value = 'exit'
        form.value.plate = spot.current_plate
        dialogVisible.value = true
    }
    else if (spot.status === 3) handleExitCalc(spot)
}

const confirmAction = async () => {
    loading.value = true
    try {
        if (currentAction.value === 'reserve') {
            if (!form.value.plate) return ElMessage.warning('请输入车牌')
            await axios.post(`${API_BASE}/parking/reserve`, {
                user_id: user.value.id, spot_id: activeSpot.value.id, plate_number: form.value.plate
            })
            ElMessage.success('预约成功')
        }
        else if (currentAction.value === 'enter') {
            await axios.post(`${API_BASE}/parking/enter`, { order_no: activeSpot.value.current_order })
            ElMessage.success('入场成功')
        }
        else if (currentAction.value === 'exit') {
            const res = await axios.post(`${API_BASE}/parking/exit`, { order_no: activeSpot.value.current_order })
            currentAction.value = 'pay'
            paymentMethod.value = 'balance'
            form.value.fee = res.data.data.fee
            form.value.duration = res.data.data.duration
            loading.value = false; fetchSpots(); fetchOrders(); return 
        }
        else if (currentAction.value === 'pay') {
            await axios.post(`${API_BASE}/parking/pay`, { order_no: activeSpot.value.current_order, payment_method: paymentMethod.value })
            await fetchUserProfile() // 支付完刷新余额
            ElMessage.success('支付成功')
        }
        dialogVisible.value = false
        fetchSpots(); fetchOrders()
    } catch (err) {
        if (err.response && (err.response.status === 403 || err.response.status === 402)) {
            ElMessage.error(err.response.data.msg)
            await fetchUserProfile()
        } else ElMessage.error(err.response?.data?.msg || '失败')
    } finally { loading.value = false }
}

const handleCancel = async (order) => {
    try {
        await ElMessageBox.confirm('确定取消预约?', '提示', {type:'warning'})
        await axios.post(`${API_BASE}/parking/cancel`, { order_no: order.order_no })
        ElMessage.success('已取消')
        fetchSpots(); fetchOrders()
    } catch(e){}
}

const handleExitCalc = async (spot) => {
    dialogTitle.value = '待支付'
    currentAction.value = 'pay'
    paymentMethod.value = 'balance'
    form.value.fee = '计算中' 
    form.value.plate = spot.current_plate
    dialogVisible.value = true
}

const logout = () => { localStorage.clear(); router.push('/login') }
const getStatusText = (s) => ({0:'空闲',1:'占用',2:'已预约',3:'待支付'}[s])
const getOrderStatus = (s) => ({0:'已预约',1:'停车中',2:'已完成',3:'待支付',4:'已取消'}[s])

onMounted(() => {
    if(!user.value) router.push('/login')
    else {
        fetchSpots(); fetchOrders(); fetchUserProfile()
        setInterval(() => { fetchSpots(); fetchOrders() }, 3000)
    }
})
</script>

<template>
  <div class="dashboard">
    <div class="header">
      <div class="logo">🎓 智能停车系统</div>
      <div class="user-info">
        <el-button v-if="user?.role==='admin'" type="warning" @click="router.push('/admin')">管理后台</el-button>
        <el-button type="primary" plain @click="router.push('/profile')">个人中心</el-button>
        <span style="margin:0 10px">{{ user?.username }}</span>
        <el-tag :type="user?.credit<80?'danger':'success'">信用 {{ user?.credit }}</el-tag>
        <el-button link type="danger" @click="logout" style="margin-left:10px">退出</el-button>
      </div>
    </div>
    <div class="main-content">
        <el-tabs v-model="activeArea" class="area-tabs">
            <el-tab-pane label="A区 (教学楼)" name="A"></el-tab-pane>
            <el-tab-pane label="B区 (宿舍楼)" name="B"></el-tab-pane>
            <el-tab-pane label="C区 (访客区)" name="C"></el-tab-pane>
        </el-tabs>
        <div class="grid">
          <div v-for="spot in filteredSpots" :key="spot.id" class="card" :class="'status-'+spot.status" @click="handleSpotClick(spot)">
             <div class="icon">{{ ['🅿️','🚘','🔒','💰'][spot.status] }}</div>
             <div class="no">{{ spot.no }}</div>
             <div class="plate" v-if="spot.current_plate">{{ spot.current_plate }}</div>
             <div class="status-tag">{{ getStatusText(spot.status) }}</div>
          </div>
        </div>
        
        <div class="panel-header" style="margin-top:30px">📋 停车记录</div>
        <el-table :data="orderList" stripe height="300">
            <el-table-column prop="order_no" label="订单号" width="180" />
            <el-table-column prop="plate" label="车牌" width="120" />
            <el-table-column label="状态" width="100"><template #default="s"><el-tag>{{ getOrderStatus(s.row.status) }}</el-tag></template></el-table-column>
            <el-table-column prop="in_time" label="入场时间" />
            <el-table-column label="费用"><template #default="s"><b v-if="s.row.fee>0" style="color:#f56c6c">¥{{s.row.fee}}</b></template></el-table-column>
            <el-table-column label="操作" width="120">
                <template #default="s">
                    <el-button v-if="s.row.status===3" type="danger" size="small" @click="handleExitCalc({current_plate:s.row.plate});activeSpot={current_order:s.row.order_no}">支付</el-button>
                    <el-button v-else-if="s.row.status===0" type="warning" plain size="small" @click="handleCancel(s.row)">取消</el-button>
                </template>
            </el-table-column>
        </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="350px">
        <div v-if="currentAction==='reserve'">
            <p>请选择/输入车牌：</p>
            <el-select v-model="form.plate" placeholder="选择车辆" filterable allow-create default-first-option style="width:100%">
                <el-option v-for="p in myPlates" :key="p" :label="p" :value="p" />
            </el-select>
            <div v-if="myPlates.length===0" style="font-size:12px;color:#999;margin-top:5px">提示: 请去个人中心绑定车辆</div>
        </div>
        <div v-if="['enter','exit'].includes(currentAction)" style="text-align:center">
            <h2 style="color:#409EFF">{{ form.plate }}</h2>
            <p>{{ currentAction==='enter'?'识别成功，允许入场？':'到达出口，进行结算？' }}</p>
        </div>
        <div v-if="currentAction==='pay'" style="text-align:center">
            <h1>¥ {{ form.fee }}</h1>
            <el-radio-group v-model="paymentMethod">
                <el-radio label="balance" border>余额支付 (余:{{ user?.balance }})</el-radio>
                <el-radio label="scan" border>扫码</el-radio>
            </el-radio-group>
        </div>
        <template #footer>
            <el-button @click="dialogVisible=false">取消</el-button>
            <el-button type="primary" :loading="loading" @click="confirmAction">确认</el-button>
        </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.dashboard { min-height: 100vh; background: #f5f7fa; }
.header { height: 60px; background: #fff; display: flex; justify-content: space-between; align-items: center; padding: 0 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.main-content { max-width: 1000px; margin: 30px auto; padding: 0 20px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 15px; }
.card { height: 160px; border-radius: 12px; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; transition: 0.3s; border: 2px solid transparent; }
.card:hover { transform: translateY(-5px); box-shadow: 0 8px 20px rgba(0,0,0,0.1); }
.status-0 { border-color: #95d475; background: #f0f9eb; color: #529b2e; } /* 空闲 */
.status-2 { border-color: #409eff; background: #ecf5ff; color: #409eff; } /* 预约 */
.status-1 { border-color: #f56c6c; background: #fef0f0; color: #f56c6c; } /* 占用 */
.status-3 { border-color: #e6a23c; background: #fdf6ec; color: #b88230; } /* 待支付 */
.icon { font-size: 32px; margin-bottom: 5px; }
.no { font-weight: bold; font-size: 18px; }
.plate { background: rgba(0,0,0,0.05); padding: 2px 6px; border-radius: 4px; font-size: 13px; margin: 5px 0; }
</style>