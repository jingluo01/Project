<template>
  <div class="parking-map-container">
    <!-- Header -->
    <div class="header">
      <div class="header-left">
        <h1 class="title">你好，{{ userStore.username }}</h1>
      </div>
      
      <div class="header-right">
        <div class="credit-score">
          <el-progress
            type="circle"
            :percentage="userStore.creditScore"
            :width="60"
            :stroke-width="6"
            :color="creditColor"
          >
            <template #default="{ percentage }">
              <span class="percentage-value">{{ percentage }}</span>
              <span class="percentage-label">分</span>
            </template>
          </el-progress>
          <span class="credit-label">信用积分</span>
        </div>
        
        <div class="balance">
          <el-icon><Wallet /></el-icon>
          <span>余额: {{ formatCurrency(userStore.balance) }}</span>
        </div>
        
        <el-button @click="router.push('/profile')">个人中心</el-button>
        <el-button @click="handleLogout">退出</el-button>
      </div>
    </div>
    
    <!-- Zone Tabs -->
    <el-tabs v-model="activeZone" @tab-change="handleZoneChange" class="zone-tabs">
      <el-tab-pane
        v-for="zone in parkingStore.zones"
        :key="zone.zone_id"
        :label="`${zone.zone_name.substring(0, 2)}`"
        :name="zone.zone_id"
      />
    </el-tabs>
    
    <!-- Parking Grid -->
    <div class="parking-grid-container">
      <div class="parking-grid" v-loading="parkingStore.loading">
        <div
          v-for="spot in parkingStore.spots"
          :key="spot.spot_id"
          class="parking-spot"
          :class="getSpotClass(spot.status)"
          @click="handleSpotClick(spot)"
        >
          <div class="spot-icon">
            <el-icon v-if="spot.status === 0"><Location /></el-icon>
            <el-icon v-else-if="spot.status === 1"><Lock /></el-icon>
            <el-icon v-else-if="spot.status === 2"><Tools /></el-icon>
            <el-icon v-else><Clock /></el-icon>
          </div>
          <div class="spot-no">{{ spot.spot_no }}</div>
          <div class="spot-status">{{ getStatusText(spot.status) }}</div>
          <div v-if="spot.current_plate" class="spot-plate">{{ spot.current_plate }}</div>
        </div>
      </div>
    </div>
    
    <!-- Orders Container -->
    <div class="orders-container">
      <transition-group name="list">
        <!-- Unified Orders List (Maintains Stable Order) -->
        <div 
          v-for="order in orderStore.visibleOrders" 
          :key="order.order_id" 
          class="current-order glass-effect shine-effect" 
          :class="{ 
            'order-pending': order.status === 0,
            'order-parking': order.status === 1,
            'order-warning': order.status === 2 || order.status === 6 
          }"
        >
          <!-- Status Badge Layer -->
          <div class="status-badge">
            {{ 
              order.status === 0 ? 'RESERVED' : 
              order.status === 1 ? 'PARKING' : 
              order.status === 2 ? 'PAYMENT' : 'VIOLATION' 
            }}
          </div>

          <div class="order-icon-wrapper">
            <div class="status-glow"></div>
            <div class="order-icon">
              <el-icon v-if="order.status === 2 || order.status === 6"><WarningFilled /></el-icon>
              <el-icon v-else-if="order.status === 0"><Clock /></el-icon>
              <el-icon v-else><Van /></el-icon>
            </div>
          </div>

          <div class="order-info">
            <div class="order-title">
              {{ 
                order.status === 0 ? '预约中' : 
                order.status === 1 ? '停车中' : 
                order.status === 2 ? '待结算' : '已违约' 
              }}
              <span class="plate-text">{{ order.plate_number }}</span>
            </div>
            
            <div class="time-box">
              <div v-if="order.status === 1" class="order-time-vibrant">
                <span class="digit">{{ formatDuration(orderDurations[order.order_id] || 0) }}</span>
              </div>
              <div v-else class="order-time-static">
                {{ order.status === 0 ? '请按时入场' : '请及时支付' }}
              </div>
            </div>

            <div class="order-fee-vibrant">
              <span class="fee-label">费用</span>
              <span class="fee-value">{{ formatCurrency(order.status === 1 ? getEstimatedFee(order) : order.total_fee) }}</span>
            </div>
          </div>

          <div class="order-actions-vertical">
            <el-button v-if="order.status === 2 || order.status === 6" type="warning" class="action-btn-premium" @click="handlePayment(order)" :loading="paying">立即结账</el-button>
            <template v-else>
              <el-button v-if="order.status === 0" type="primary" class="action-btn-premium" @click="handleStartParking(order)" :loading="simulating">快速入场</el-button>
              <el-button v-if="order.status === 1" type="danger" class="action-btn-premium" @click="handleEndParking(order)" :loading="simulating">结束停车</el-button>
              <el-button v-if="order.status === 0" link class="cancel-link" @click="handleCancelReservation(order)">取消预约</el-button>
            </template>
          </div>
        </div>
      </transition-group>
    </div>
    
    <!-- Reservation Dialog -->
    <el-dialog 
      v-model="showReservationDialog" 
      title="预约车位" 
      width="480px"
      :close-on-click-modal="false"
    >
      <div class="dialog-content-reservation">
        <div class="spot-info-card">
          <div class="spot-icon">
            <el-icon :size="32"><Location /></el-icon>
          </div>
          <div class="spot-details">
            <div class="spot-label">车位编号</div>
            <div class="spot-number">{{ selectedSpot?.spot_no }}</div>
          </div>
        </div>
        
        <el-form :model="reservationForm" ref="reservationFormRef">
          <el-form-item label="选择车辆" prop="plate_number">
            <el-select 
              v-model="reservationForm.plate_number" 
              placeholder="请选择要停放的车辆" 
              size="large"
              style="width: 100%"
            >
              <el-option
                v-for="car in userStore.cars"
                :key="car.car_id"
                :label="`${car.plate_number} ${car.nickname ? '(' + car.nickname + ')' : ''}`"
                :value="car.plate_number"
              >
                <div class="car-option">
                  <span class="car-plate">{{ car.plate_number }}</span>
                  <span v-if="car.nickname" class="car-nick">{{ car.nickname }}</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-alert
            title="温馨提示"
            description="预约后请在15分钟内到达，否则将自动取消并扣除信用分"
            type="info"
            :closable="false"
            show-icon
          />
        </el-form>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showReservationDialog = false" size="large">取消</el-button>
          <el-button type="primary" @click="handleReservation" :loading="reserving" size="large">
            <el-icon class="mr-1"><Check /></el-icon>
            确认预约
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useParkingStore } from '@/stores/parking'
import { useOrderStore } from '@/stores/order'
import { ElMessage } from 'element-plus'
import { Wallet, Location, Lock, Clock, Van, WarningFilled, Tools, Check } from '@element-plus/icons-vue'
import { initWebSocket, closeWebSocket } from '@/utils/websocket'
import { formatCurrency, formatDuration } from '@/utils/format'

const router = useRouter()
const userStore = useUserStore()
const parkingStore = useParkingStore()
const orderStore = useOrderStore()

const activeZone = ref(null)
const showReservationDialog = ref(false)
const selectedSpot = ref(null)
const reservationForm = reactive({ plate_number: '' })
const reservationFormRef = ref(null)
const reserving = ref(false)
const paying = ref(false)
const simulating = ref(false)
const orderDurations = reactive({})
let durationInterval = null

// 键盘事件处理
const handleKeyPress = (e) => {
  if (e.key === 'Enter' && showReservationDialog.value) {
    handleReservation()
  }
}

// 监听对话框状态
watch(showReservationDialog, (isOpen) => {
  if (isOpen) {
    document.addEventListener('keypress', handleKeyPress)
  } else {
    document.removeEventListener('keypress', handleKeyPress)
  }
})

const creditColor = computed(() => {
  const score = userStore.creditScore
  if (score >= 90) return '#34a853'
  if (score >= 80) return '#fbbc04'
  return '#ea4335'
})

const getSpotClass = (status) => {
  return {
    'spot-available': status === 0,
    'spot-occupied': status === 1,
    'spot-maintenance': status === 2, // 新增：维修
    'spot-reserved': status === 3     // 变更：3为预约
  }
}

const getStatusText = (status) => {
  const map = { 0: '空闲', 1: '占用', 2: '维修', 3: '已预约' }
  return map[status] || '未知'
}

const getEstimatedFee = (order) => {
  const durationInSeconds = orderDurations[order.order_id] || 0
  const minutes = durationInSeconds / 60
  
  // 模拟后端计费逻辑：不足1小时按1小时计 (向上取整)
  const hours = Math.ceil(minutes / 60) || 1
  
  const feeRate = order.fee_rate || 5.0
  const multiplier = 10.0 // 对应 config.py 中的 FEE_MULTIPLIER
  
  const discounts = { 0: 1.0, 1: 0.9, 2: 0.8 }
  const discount = discounts[order.user_role] || 1.0
  
  return hours * feeRate * discount * multiplier
}

const handleZoneChange = async (zoneId) => {
  await parkingStore.fetchSpots(zoneId)
}

const handleSpotClick = (spot) => {
  // 如果点击的是正在维修的车位
  if (spot.status === 2) {
    ElMessage.warning('该车位正在维护中，暂停使用')
    return
  }

  // 如果用户有待支付订单，禁止新预约并提示
  if (orderStore.unpaidOrder) {
    ElMessage.error('您有未支付订单，请先完成支付')
    return
  }

  // 如果点击的是自己的预约车位 (status 3)
  const isMyReserved = spot.status === 3 && userStore.cars.some(c => c.plate_number === spot.current_plate)
  if (isMyReserved) {
    selectedSpot.value = spot
    ElMessage.info({
      message: '这是您的预约车位，可在下方进行操作',
      duration: 2000
    })
    return
  }

  if (spot.status !== 0) {
    ElMessage.warning('该车位目前不可用')
    return
  }
  
  if (userStore.cars.length === 0) {
    ElMessage.warning('请先绑定车辆')
    router.push('/profile')
    return
  }
  
  selectedSpot.value = spot
  reservationForm.plate_number = userStore.cars[0]?.plate_number || ''
  showReservationDialog.value = true
}

const handleCancelReservation = async (order) => {
  const targetOrder = order || orderStore.activeOrder
  if (!targetOrder || targetOrder.status !== 0) return

  try {
    await orderStore.cancelOrder(targetOrder.order_id)
    ElMessage.success('已取消预约')
    await parkingStore.fetchSpots(activeZone.value)
  } catch (error) {
    console.error('Cancel failed:', error)
  }
}

const handlePayment = async (order) => {
  const targetOrder = order || orderStore.unpaidOrder
  if (!targetOrder) return

  paying.value = true
  try {
    await orderStore.payOrder(targetOrder.order_id)
    ElMessage.success('支付成功')
    await userStore.fetchProfile() // 更新余额
  } catch (error) {
    console.error('Payment failed:', error)
  } finally {
    paying.value = false
  }
}

const handleStartParking = async (order) => {
  const targetOrder = order || orderStore.activeOrder
  if (!targetOrder) return

  simulating.value = true
  try {
    await orderStore.simulateEnter(targetOrder.plate_number)
    ElMessage.success('识别成功，欢迎入场')
    await parkingStore.fetchSpots(activeZone.value)
  } catch (error) {
    console.error('Start parking failed:', error)
  } finally {
    simulating.value = false
  }
}

const handleEndParking = async (order) => {
  const targetOrder = order || orderStore.activeOrder
  if (!targetOrder) return

  simulating.value = true
  try {
    await orderStore.simulateExit(targetOrder.plate_number)
    ElMessage.success('已识别离场，请及时支付账单')
    await parkingStore.fetchSpots(activeZone.value)
  } catch (error) {
    console.error('End parking failed:', error)
  } finally {
    simulating.value = false
  }
}

const handleReservation = async () => {
  if (!reservationForm.plate_number) {
    ElMessage.warning('请选择车辆')
    return
  }
  
  reserving.value = true
  try {
    await orderStore.createOrder({
      spot_id: selectedSpot.value.spot_id,
      plate_number: reservationForm.plate_number
    })
    
    ElMessage.success('预约成功')
    showReservationDialog.value = false
    await parkingStore.fetchSpots(activeZone.value)
  } catch (error) {
    console.error('Reservation failed:', error)
  } finally {
    reserving.value = false
  }
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

const updateOrderDuration = () => {
  const now = new Date()
  orderStore.activeOrders.forEach(order => {
    if (order.in_time) {
      const inTimeStr = order.in_time.endsWith('Z') ? order.in_time : order.in_time + 'Z'
      const inTime = new Date(inTimeStr)
      orderDurations[order.order_id] = Math.floor((now - inTime) / 1000)
    }
  })
}

onMounted(async () => {
  // Initialize WebSocket
  initWebSocket()
  
  // Fetch user profile and cars
  await userStore.fetchProfile()
  
  // Fetch zones and spots
  await parkingStore.fetchZones()
  if (parkingStore.zones.length > 0) {
    activeZone.value = parkingStore.zones[0].zone_id
    await parkingStore.fetchSpots(activeZone.value)
  }
  
  // Fetch orders
  await orderStore.fetchOrders()
  
  // Start duration counter
  durationInterval = setInterval(updateOrderDuration, 1000)
})

onUnmounted(() => {
  closeWebSocket()
  if (durationInterval) {
    clearInterval(durationInterval)
  }
})
</script>

<style scoped>
.parking-map-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  color: white;
}

.title {
  font-size: 28px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.credit-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.percentage-value {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
}

.percentage-label {
  font-size: 12px;
  color: #ffffff;
}

.credit-label {
  font-size: 12px;
  opacity: 0.9;
}

.balance {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
}

.zone-tabs {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.parking-grid-container {
  background: white;
  border-radius: 12px;
  padding: 30px;
  min-height: 500px;
}

.parking-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 20px;
}

.parking-spot {
  aspect-ratio: 1;
  border-radius: 12px;
  padding: 16px 16px 40px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  position: relative;
  overflow: hidden;
  min-height: 0;
}

.spot-available {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  border: 2px solid #34d399;
}

.spot-available:hover {
  transform: translateY(-4px) scale(1.05);
  box-shadow: 0 8px 16px rgba(52, 211, 153, 0.3);
}

.spot-occupied {
  background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%);
  border: 2px solid #ef4444;
  cursor: not-allowed;
}

.spot-maintenance {
  background: linear-gradient(135deg, #f3f4f6 0%, #d1d5db 100%);
  border: 2px solid #9ca3af;
  color: #6b7280;
  cursor: not-allowed;
  opacity: 0.8;
}

.spot-reserved {
  background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%);
  border: 2px solid #f97316;
  cursor: pointer;
}

.spot-icon {
  font-size: 32px;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.spot-no {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 4px;
  flex-shrink: 0;
  white-space: nowrap;
}

.spot-status {
  font-size: 13px;
  opacity: 0.8;
  flex-shrink: 0;
  white-space: nowrap;
  margin-bottom: 10px;
}

.spot-plate {
  font-size: 11px;
  padding: 3px 10px;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  font-weight: 600;
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  max-width: calc(100% - 24px);
  overflow: hidden;
  text-overflow: ellipsis;
}

.orders-container {
  position: fixed;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: row; /* 横向排列 */
  gap: 16px;
  max-width: 90vw; /* 限制宽度，防止溢出屏幕 */
  overflow-x: auto; /* 水平滚动 */
  padding: 15px;
  z-index: 1000;
  justify-content: center; /* 居中显示 */
  align-items: flex-end;
}

/* 隐藏滚动条但保留功能 (可选优化) */
.orders-container::-webkit-scrollbar {
  height: 6px;
}
.orders-container::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.1);
  border-radius: 3px;
}

.current-order {
  position: relative;
  flex-shrink: 0;
  border-radius: 20px;
  padding: 24px 28px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.12);
  display: flex;
  align-items: center;
  gap: 20px;
  width: 440px;
  height: 140px; /* 统一高度 */
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
}

.current-order:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.18);
}

/* 状态标识浮线 */
.status-badge {
  position: absolute;
  top: 0;
  right: 0;
  padding: 4px 12px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1px;
  color: white;
  border-bottom-left-radius: 12px;
  background: #64748b;
  text-transform: uppercase;
  opacity: 0.9;
}

.order-pending .status-badge { background: linear-gradient(135deg, #3b82f6, #60a5fa); }
.order-parking .status-badge { background: linear-gradient(135deg, #10b981, #34d399); }
.order-warning .status-badge { background: linear-gradient(135deg, #ef4444, #f87171); }

/* 图标光圈 */
.order-icon-wrapper {
  position: relative;
  width: 70px;
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.status-glow {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  opacity: 0.2;
}

.order-pending .status-glow { background: #3b82f6; box-shadow: 0 0 20px #3b82f6; }
.order-parking .status-glow { 
  background: #10b981; 
  box-shadow: 0 0 20px #10b981;
  animation: pulse-glow 2s infinite; 
}
.order-warning .status-glow { background: #ef4444; box-shadow: 0 0 20px #ef4444; }

@keyframes pulse-glow {
  0% { transform: scale(1); opacity: 0.2; }
  50% { transform: scale(1.2); opacity: 0.4; }
  100% { transform: scale(1); opacity: 0.2; }
}

.order-icon {
  font-size: 32px;
  color: #1e293b;
  z-index: 2;
}

/* 文字排版 */
.order-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.order-title {
  font-size: 15px;
  font-weight: 700;
  color: #334155;
  display: flex;
  align-items: center;
  gap: 8px;
}

.plate-text {
  font-family: 'Monaco', monospace;
  color: #64748b;
  font-size: 13px;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 6px;
}

.order-time-vibrant .digit {
  font-size: 24px;
  font-weight: 900;
  color: #1e293b;
  letter-spacing: -1px;
}

.order-time-static {
  font-size: 13px;
  color: #94a3b8;
  height: 32px; /* 与计时器数字高度大致对齐，保持占位一致 */
  display: flex;
  align-items: center;
}

.time-box {
  height: 32px;
  display: flex;
  align-items: center;
}

.order-fee-vibrant {
  margin-top: 4px;
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.fee-label {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
}

.fee-value {
  font-size: 18px;
  font-weight: 800;
  color: #f97316;
}

/* 按钮组 */
.order-actions-vertical {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 100px;
}

.action-btn-premium {
  border-radius: 10px !important;
  font-weight: 700 !important;
  letter-spacing: 0.5px !important;
  height: 40px !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
  transition: all 0.3s !important;
}

.action-btn-premium:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 15px rgba(0,0,0,0.15) !important;
}

.cancel-link {
  font-size: 12px !important;
  color: #94a3b8 !important;
  text-decoration: underline !important;
}

.cancel-link:hover {
  color: #ef4444 !important;
}

.order-pending { border-left: 5px solid #3b82f6; }
.order-parking { border-left: 5px solid #10b981; }
.order-warning { border-left: 5px solid #ef4444; }

/* 对话框美化 */
.dialog-content-reservation {
  padding: 8px 0;
}

.spot-info-card {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.spot-icon {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.spot-details {
  flex: 1;
}

.spot-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 4px;
}

.spot-number {
  font-size: 24px;
  font-weight: 700;
  color: white;
  letter-spacing: 2px;
}

.car-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.car-plate {
  font-weight: 600;
  color: #1e293b;
}

.car-nick {
  font-size: 12px;
  color: #64748b;
}

.dialog-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.mr-1 {
  margin-right: 4px;
}
</style>
