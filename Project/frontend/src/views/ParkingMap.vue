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
                :disabled="orderStore.getCarStatus(car.plate_number) !== null"
              >
                <div class="car-option">
                  <div class="car-main-info">
                    <span class="car-plate">{{ car.plate_number }}</span>
                    <span v-if="car.nickname" class="car-nick">{{ car.nickname }}</span>
                  </div>
                  <el-tag 
                    v-if="orderStore.getCarStatus(car.plate_number) !== null" 
                    size="small" 
                    :type="getOrderStatusType(orderStore.getCarStatus(car.plate_number))"
                  >
                    {{ getOrderStatusText(orderStore.getCarStatus(car.plate_number)) }}
                  </el-tag>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-alert
            title="温馨提示"
            :description="`预约后请在 ${reservationMinutes} 分钟内到达，否则将自动取消并扣除信用分`"
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

    <!-- Payment Dialog -->
    <el-dialog 
      v-model="showPaymentDialog" 
      title="选择支付方式" 
      width="520px"
      :close-on-click-modal="false"
    >
      <div class="payment-dialog-content">
        <!-- Order Summary -->
        <div class="order-summary-card">
          <div class="summary-header">
            <el-icon :size="24"><Van /></el-icon>
            <span>订单信息</span>
          </div>
          <div class="summary-details">
            <div class="detail-row">
              <span class="label">车牌号码</span>
              <span class="value">{{ currentPaymentOrder?.plate_number }}</span>
            </div>
            <div class="detail-row">
              <span class="label">停车时长</span>
              <span class="value">{{ formatDuration(orderDurations[currentPaymentOrder?.order_id] || 0) }}</span>
            </div>
            <div class="detail-row total">
              <span class="label">应付金额</span>
              <span class="value amount">{{ formatCurrency(currentPaymentOrder?.total_fee) }}</span>
            </div>
          </div>
        </div>

        <!-- Payment Methods -->
        <div class="payment-methods">
          <div class="method-title">支付方式</div>
          
          <!-- Balance Payment -->
          <div 
            class="payment-method-card" 
            :class="{ 
              'selected': selectedPaymentMethod === 0,
              'disabled': userStore.balance < (currentPaymentOrder?.total_fee || 0)
            }"
            @click="selectPaymentMethod(0)"
          >
            <div class="method-icon balance-icon">
              <el-icon :size="28"><Wallet /></el-icon>
            </div>
            <div class="method-info">
              <div class="method-name">余额支付</div>
              <div class="method-desc">
                当前余额：{{ formatCurrency(userStore.balance) }}
                <span v-if="userStore.balance < (currentPaymentOrder?.total_fee || 0)" class="insufficient">（余额不足）</span>
              </div>
            </div>
            <div class="method-check">
              <el-icon v-if="selectedPaymentMethod === 0" :size="20" color="#10b981"><Check /></el-icon>
            </div>
          </div>

          <!-- Alipay Payment -->
          <div 
            class="payment-method-card" 
            :class="{ 
              'selected': selectedPaymentMethod === 2
            }"
            @click="selectPaymentMethod(2)"
          >
            <div class="method-icon alipay-icon">
              <svg viewBox="0 0 1024 1024" width="28" height="28">
                <path d="M1024 701.9v162.5c0 88.7-71.8 160.5-160.5 160.5H160.5C71.8 1024.9 0 953.1 0 864.4V159.5C0 70.8 71.8-1 160.5-1h703c88.7 0 160.5 71.8 160.5 160.5v542.4zM643.5 548.5c-48.5-14.3-117.3-35.8-199.5-60.3-54.5 75-120.8 134.5-198.3 178.3 0 0-4.5 2.3-12 0-216-97.5-265.5-344.3-210.8-402 32.3-34.5 75.8-29.3 119.3 11.3 43.5 40.5 81.8 114 113.3 215.3 47.3-29.3 89.3-64.5 125.3-105 10.5-12 20.3-24.8 29.3-38.3-24-56.3-38.3-117.8-38.3-172.5 0-83.3 34.5-119.3 79.5-119.3s79.5 36 79.5 119.3c0 47.3-9.8 95.3-27 141.8 39.8 51 95.3 93.8 164.3 123.8l-24.8 108.5z m-192-332.3c-20.3 0-36.8 28.5-36.8 83.3 0 39.8 9 81 24 117.8 24-39.8 36.8-81.8 36.8-117.8 0-54.8-9-83.3-24-83.3z" fill="#00A0E9"/>
              </svg>
            </div>
            <div class="method-info">
              <div class="method-name">支付宝</div>
              <div class="method-desc">扫码支付，安全便捷</div>
            </div>
            <div class="method-check">
              <el-icon v-if="selectedPaymentMethod === 2" :size="20" color="#10b981"><Check /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showPaymentDialog = false" size="large">取消</el-button>
          <el-button 
            type="primary" 
            @click="confirmPayment" 
            :loading="paying"
            :disabled="selectedPaymentMethod === null || (selectedPaymentMethod === 0 && userStore.balance < (currentPaymentOrder?.total_fee || 0))"
            size="large"
          >
            <el-icon class="mr-1"><Check /></el-icon>
            确认支付
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Alipay QR Code Dialog -->
    <el-dialog 
      v-model="showQRCodeDialog" 
      title="支付宝扫码支付" 
      width="420px"
      :close-on-click-modal="false"
      @close="stopPolling"
    >
      <div class="qrcode-dialog-content">
        <div class="qrcode-header">
          <el-icon :size="32" color="#00A0E9"><svg viewBox="0 0 1024 1024" width="32" height="32">
            <path d="M1024 701.9v162.5c0 88.7-71.8 160.5-160.5 160.5H160.5C71.8 1024.9 0 953.1 0 864.4V159.5C0 70.8 71.8-1 160.5-1h703c88.7 0 160.5 71.8 160.5 160.5v542.4zM643.5 548.5c-48.5-14.3-117.3-35.8-199.5-60.3-54.5 75-120.8 134.5-198.3 178.3 0 0-4.5 2.3-12 0-216-97.5-265.5-344.3-210.8-402 32.3-34.5 75.8-29.3 119.3 11.3 43.5 40.5 81.8 114 113.3 215.3 47.3-29.3 89.3-64.5 125.3-105 10.5-12 20.3-24.8 29.3-38.3-24-56.3-38.3-117.8-38.3-172.5 0-83.3 34.5-119.3 79.5-119.3s79.5 36 79.5 119.3c0 47.3-9.8 95.3-27 141.8 39.8 51 95.3 93.8 164.3 123.8l-24.8 108.5z m-192-332.3c-20.3 0-36.8 28.5-36.8 83.3 0 39.8 9 81 24 117.8 24-39.8 36.8-81.8 36.8-117.8 0-54.8-9-83.3-24-83.3z" fill="#00A0E9"/>
          </svg></el-icon>
          <div class="qrcode-title">
            <div class="title-main">请使用支付宝扫码支付</div>
            <div class="title-sub">支付金额：{{ formatCurrency(currentPaymentOrder?.total_fee) }}</div>
          </div>
        </div>

        <div class="qrcode-container">
          <div v-if="qrCodeLoading" class="qrcode-loading">
            <el-icon class="is-loading" :size="40"><Loading /></el-icon>
            <div>正在安全请求支付网关...</div>
          </div>
          
          <!-- 新增：支付成功后的展示层，防止显示红叉 -->
          <div v-else-if="pollingStatus === 'success'" class="qrcode-success-display">
            <el-icon :size="80" color="#10b981" class="success-icon-animate"><SuccessFilled /></el-icon>
            <div class="success-title">支付成功</div>
            <div class="success-sub">感谢您的使用</div>
          </div>

          <div v-else-if="qrCodeUrl" class="qrcode-wrapper">
            <!-- 使用国内访问更稳定的二维码引擎 -->
            <img :src="`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(qrCodeUrl)}`" 
                 alt="支付二维码" 
                 class="qrcode-image"
                 @load="qrCodeLoading = false" 
            >
            <div class="qrcode-tip">
              <el-icon><InfoFilled /></el-icon>
              <span>二维码5分钟内有效</span>
            </div>
          </div>
          <div v-else class="qrcode-error">
            <el-icon :size="40" color="#ef4444"><CircleClose /></el-icon>
            <div>二维码生成失败</div>
          </div>
        </div>

        <!-- 底部状态栏，成功时隐藏，因为中间已经显示了大图标 -->
        <div class="payment-status" v-if="pollingStatus !== 'success'">
          <div v-if="pollingStatus === 'waiting'" class="status-waiting">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>正在等待您的扫码支付...</span>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showQRCodeDialog = false" size="large">取消支付</el-button>
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
import { Wallet, Location, Lock, Clock, Van, WarningFilled, Tools, Check, Loading, InfoFilled, CircleClose, SuccessFilled } from '@element-plus/icons-vue'
import { initWebSocket, closeWebSocket } from '@/utils/websocket'
import { formatCurrency, formatDuration } from '@/utils/format'

import { getAdminConfig } from '@/api/admin'
import { createAlipayQRCode, queryAlipayStatus } from '@/api/payment'

const router = useRouter()
const userStore = useUserStore()
const parkingStore = useParkingStore()
const orderStore = useOrderStore()

// 状态映射常量
const STATUS_MAP = {
  SPOT_STATUS: {
    0: { text: '空闲', class: 'spot-available' },
    1: { text: '占用', class: 'spot-occupied' },
    2: { text: '维修', class: 'spot-maintenance' },
    3: { text: '已预约', class: 'spot-reserved' }
  },
  ORDER_STATUS: {
    0: { text: '预约中', type: '', badge: 'RESERVED' },  // el-tag 不支持 primary，用空字符串（默认样式）
    1: { text: '停车中', type: 'success', badge: 'PARKING' },
    2: { text: '待支付', type: 'warning', badge: 'UNPAID' },
    3: { text: '已完成', type: 'success', badge: 'COMPLETED' },
    4: { text: '已取消', type: 'info', badge: 'CANCELLED' },
    5: { text: '已退款', type: 'info', badge: 'REFUNDED' },
    6: { text: '违约', type: 'danger', badge: 'VIOLATION' }
  }
}

const CREDIT_COLORS = { EXCELLENT: '#34a853', GOOD: '#fbbc04', POOR: '#ea4335' }
const POLLING_CONFIG = { INTERVAL: 3000, MAX_DURATION: 300000 } // 轮询间隔3秒，最长5分钟

// 响应式状态
const activeZone = ref(null)
const showReservationDialog = ref(false)
const showPaymentDialog = ref(false)
const selectedSpot = ref(null)
const reservationForm = reactive({ plate_number: '' })
const reservationFormRef = ref(null)
const reserving = ref(false)
const paying = ref(false)
const simulating = ref(false)
const orderDurations = reactive({})
let durationInterval = null

// 支付相关
const currentPaymentOrder = ref(null)
const selectedPaymentMethod = ref(null)
const showQRCodeDialog = ref(false)
const qrCodeUrl = ref('')
const qrCodeLoading = ref(false)
const pollingStatus = ref('')
let pollingTimer = null

// 系统配置
const sysConfig = ref({ reservation_timeout: 30, fee_multiplier: 10.0 })
const reservationMinutes = computed(() => sysConfig.value.reservation_timeout)

// 键盘快捷键支持
const handleKeyPress = (e) => {
  if (e.key === 'Enter' && showReservationDialog.value) handleReservation()
}

watch(showReservationDialog, (isOpen) => {
  isOpen ? document.addEventListener('keypress', handleKeyPress) : document.removeEventListener('keypress', handleKeyPress)
})

// 计算属性
const creditColor = computed(() => {
  const score = userStore.creditScore
  const { perfect = 100, good = 85, min = 70 } = sysConfig.value.credit_thresholds || {}
  if (score >= good) return CREDIT_COLORS.EXCELLENT
  if (score >= min) return CREDIT_COLORS.GOOD
  return CREDIT_COLORS.POOR
})

// 辅助函数
const getSpotClass = (status) => ({
  'spot-available': status === 0,
  'spot-occupied': status === 1,
  'spot-maintenance': status === 2,
  'spot-reserved': status === 3
})

const getStatusText = (status) => STATUS_MAP.SPOT_STATUS[status]?.text || '未知'
const getOrderStatusText = (status) => STATUS_MAP.ORDER_STATUS[status]?.text || '占用中'
const getOrderStatusType = (status) => STATUS_MAP.ORDER_STATUS[status]?.type || 'info'

const getEstimatedFee = (order) => {
  const durationInSeconds = orderDurations[order.order_id] || 0
  const minutes = durationInSeconds / 60
  const freeTime = order.free_time || 0
  
  // 如果停车时长在免费时长内，费用为 0
  if (minutes <= freeTime) {
    return 0
  }
  
  // 模拟后端计费逻辑：超过免费时长后，不足1小时按1小时计 (向上取整)
  const hours = Math.ceil(minutes / 60)
  
  const feeRate = order.fee_rate || 5.0
  const multiplier = sysConfig.value.fee_multiplier || 1.0 // 修正默认倍率为 1.0
  
  // 从动态配置中获取折扣，如果不存在则默认为 1.0 (无折扣)
  const discount = sysConfig.value.roles?.[order.user_role.toString()] ?? 1.0
  
  return (hours * feeRate * discount * multiplier).toFixed(2)
}

const handleZoneChange = async (zoneId) => {
  await parkingStore.fetchSpots(zoneId)
}

const handleSpotClick = (spot) => {
  // 维修中的车位直接提示
  if (spot.status === 2) return ElMessage.warning('该车位正在维护中，暂停使用')
  
  // 违约和信用分检查
  if (orderStore.hasViolation) return ElMessage.error('您有违约记录未处理，请先处理违约账单')
  const passScore = sysConfig.value.credit_thresholds?.min || 70
  if (userStore.creditScore < passScore) return ElMessage.error(`信用分不足 ${passScore}，无法预约车位`)
  
  // 重复预约拦截
  if (orderStore.activeOrder) return ElMessage.info('您已有预约或正在进行的订单，请先处理后再预约')
  
  // 点击自己的预约车位时提示
  const isMyReserved = spot.status === 3 && userStore.cars.some(c => c.plate_number === spot.current_plate)
  if (isMyReserved) {
    selectedSpot.value = spot
    return ElMessage.info({ message: '这是您的预约车位，可在下方进行操作', duration: 2000 })
  }
  
  // 车位可用性检查
  if (spot.status !== 0) return ElMessage.warning('该车位目前不可用')
  if (userStore.cars.length === 0) {
    ElMessage.warning('请先绑定车辆')
    return router.push('/profile')
  }
  
  selectedSpot.value = spot
  
  // 智能选择空闲车辆
  const availableCar = userStore.cars.find(car => orderStore.getCarStatus(car.plate_number) === null)
  if (availableCar) {
    reservationForm.plate_number = availableCar.plate_number
  } else {
    reservationForm.plate_number = userStore.cars[0]?.plate_number || ''
    ElMessage.warning('您的所有车辆都有进行中的订单，请先处理后再预约')
  }
  
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
  const targetOrder = order || orderStore.unpaidOrders[0]
  if (!targetOrder) return

  // 设置当前支付订单并打开支付对话框
  currentPaymentOrder.value = targetOrder
  selectedPaymentMethod.value = null // 重置选择
  
  // 如果余额足够，默认选中余额支付
  if (userStore.balance >= targetOrder.total_fee) {
    selectedPaymentMethod.value = 0
  }
  
  showPaymentDialog.value = true
}

// 选择支付方式
const selectPaymentMethod = (method) => {
  // 如果是余额支付且余额不足，不允许选择
  if (method === 0 && userStore.balance < (currentPaymentOrder.value?.total_fee || 0)) {
    return
  }
  selectedPaymentMethod.value = method
}

// 确认支付
const confirmPayment = async () => {
  if (selectedPaymentMethod.value === null) {
    ElMessage.warning('请选择支付方式')
    return
  }

  paying.value = true
  try {
    if (selectedPaymentMethod.value === 0) {
      // 余额支付
      await orderStore.payOrder(currentPaymentOrder.value.order_id, 0)
      ElMessage.success('支付成功')
      showPaymentDialog.value = false
      await userStore.fetchProfile() // 刷新用户余额
    } else if (selectedPaymentMethod.value === 2) {
      // 支付宝支付
      await handleAlipayPayment()
    }
  } catch (error) {
    console.error('Payment failed:', error)
  } finally {
    paying.value = false
  }
}

// 处理支付宝支付
const handleAlipayPayment = async () => {
  try {
    qrCodeLoading.value = true
    showPaymentDialog.value = false
    showQRCodeDialog.value = true
    pollingStatus.value = 'waiting'
    
    // 调用后端生成二维码
    const res = await createAlipayQRCode({ order_id: currentPaymentOrder.value.order_id })
    
    if (res.success) {
      qrCodeUrl.value = res.data.qr_code
      qrCodeLoading.value = false
      
      // 开始轮询支付状态
      startPolling(res.data.out_trade_no)
    } else {
      throw new Error(res.message || '生成二维码失败')
    }
  } catch (error) {
    qrCodeLoading.value = false
    ElMessage.error(error.message || '生成支付二维码失败')
    showQRCodeDialog.value = false
  }
}

// 开始轮询支付状态
const startPolling = (outTradeNo) => {
  const startTime = Date.now()
  
  // 定义轮询函数
  const poll = async () => {
    // 如果已经停止轮询，直接返回
    if (!pollingStatus.value) return
    
    // 检查是否超时（5分钟）
    if (Date.now() - startTime > POLLING_CONFIG.MAX_DURATION) {
      stopPolling()
      ElMessage.warning('支付超时，请重新发起支付')
      return
    }
    
    try {
      const res = await queryAlipayStatus({ out_trade_no: outTradeNo })
      
      if (res.success && res.data.trade_status === 'TRADE_SUCCESS') {
        // 支付成功
        stopPolling()
        pollingStatus.value = 'success'
        ElMessage.success('支付成功！')
        
        // 延迟关闭对话框，让用户看到成功提示
        setTimeout(async () => {
          showQRCodeDialog.value = false
          await orderStore.fetchOrders()
          await userStore.fetchProfile()
        }, 1500)
        return // 结束递归
      }
    } catch (error) {
      // 忽略超时错误，继续轮询
      console.log('查询支付状态失败（可能网络波动），继续轮询...', error)
    }
    
    // 继续下一次轮询
    pollingTimer = setTimeout(poll, POLLING_CONFIG.INTERVAL)
  }
  
  // 开始第一次轮询
  poll()
}

// 停止轮询
const stopPolling = () => {
  if (pollingTimer) {
    clearTimeout(pollingTimer) // 注意这里改为clearTimeout
    pollingTimer = null
  }
  // 如果是支付成功状态，不要立即清空，让用户看到成功提示
  if (pollingStatus.value !== 'success') {
    qrCodeUrl.value = ''
    qrCodeLoading.value = false
    pollingStatus.value = ''
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
      // 使用 Math.max(0, ...) 防止服务器时间微领先于本地时间时显示负数
      orderDurations[order.order_id] = Math.max(0, Math.floor((now - inTime) / 1000))
    }
  })
}

onMounted(async () => {
  // Initialize WebSocket
  initWebSocket()
  
  // Fetch user profile and cars
  await userStore.fetchProfile()
  
  // Fetch system config (for dynamic timeouts)
  try {
    const configRes = await getAdminConfig()
    if (configRes.success) {
      sysConfig.value = configRes.data
    }
  } catch (err) {
    console.error('Failed to load system config')
  }
  
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

/* 列表动画 - 解决位移抖动和重排感 */
.list-enter-active,
.list-leave-active {
  transition: all 0.5s cubic-bezier(0.55, 0, 0.1, 1);
}

.list-enter-from {
  opacity: 0;
  transform: translateY(30px) scale(0.9);
}

.list-leave-to {
  opacity: 0;
  transform: scale(0.5);
}

/* 关键：处理重排时的平滑移动 */
.list-move {
  transition: transform 0.6s cubic-bezier(0.55, 0, 0.1, 1);
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
  justify-content: space-between;
  width: 100%;
}

.car-main-info {
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

/* 支付对话框样式 */
.payment-dialog-content {
  padding: 8px 0;
}

.order-summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  color: white;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 20px;
  opacity: 0.95;
}

.summary-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.detail-row.total {
  border-bottom: none;
  padding-top: 16px;
  margin-top: 8px;
  border-top: 2px solid rgba(255, 255, 255, 0.3);
}

.detail-row .label {
  font-size: 14px;
  opacity: 0.9;
}

.detail-row .value {
  font-size: 15px;
  font-weight: 600;
}

.detail-row.total .label {
  font-size: 16px;
  font-weight: 700;
}

.detail-row.total .value.amount {
  font-size: 28px;
  font-weight: 900;
  color: #fbbf24;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.payment-methods {
  margin-top: 8px;
}

.method-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 16px;
}

.payment-method-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.payment-method-card:hover:not(.disabled) {
  border-color: #10b981;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
  transform: translateY(-2px);
}

.payment-method-card.selected {
  border-color: #10b981;
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.2);
}

.payment-method-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f9fafb;
}

.method-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.balance-icon {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: white;
}

.alipay-icon {
  background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
}

.method-info {
  flex: 1;
}

.method-name {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}

.method-desc {
  font-size: 13px;
  color: #64748b;
}

.method-desc .insufficient {
  color: #ef4444;
  font-weight: 600;
}

.method-check {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 支付宝二维码对话框样式 */
.qrcode-dialog-content {
  padding: 20px 0;
}

.qrcode-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 2px solid #f1f5f9;
}

.qrcode-title {
  flex: 1;
}

.title-main {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}

.title-sub {
  font-size: 14px;
  color: #64748b;
}

.qrcode-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 260px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 16px;
  padding: 30px;
  margin-bottom: 20px;
}

.qrcode-loading,
.qrcode-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #64748b;
}

.qrcode-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.qrcode-image {
  width: 200px;
  height: 200px;
  border: 4px solid white;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.qrcode-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748b;
}

.payment-status {
  min-height: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.status-waiting,
.status-success {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
}

.status-waiting {
  color: #3b82f6;
}

.status-success {
  color: #10b981;
}

/* 支付成功展示样式 */
.qrcode-success-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 240px;
  animation: fadeIn 0.3s ease-out;
}

.success-icon-animate {
  margin-bottom: 20px;
  animation: scaleIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.success-title {
  font-size: 24px;
  font-weight: 600;
  color: #10b981;
  margin-bottom: 8px;
}

.success-sub {
  font-size: 14px;
  color: #6b7280;
}

@keyframes scaleIn {
  from {
    transform: scale(0);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
