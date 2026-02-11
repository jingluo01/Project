<template>
  <div class="profile-container">
    <div class="profile-header">
      <h1>个人中心</h1>
      <el-button @click="router.push('/parking')">返回停车地图</el-button>
    </div>
    
    <div class="profile-layout">
      <!-- Left Content (70%) -->
      <div class="left-content">
        <!-- User Info Card -->
        <div class="card info-card">
          <div class="card-header">
            <h3>个人信息</h3>
            <el-button type="primary" size="small" @click="showRechargeDialog = true">充值余额</el-button>
          </div>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="学号/工号">{{ userStore.user?.user_no }}</el-descriptions-item>
            <el-descriptions-item label="姓名">{{ userStore.user?.username }}</el-descriptions-item>
            <el-descriptions-item label="身份身份">{{ getRoleText(userStore.user?.role) }}</el-descriptions-item>
            <el-descriptions-item label="信用分分数">
              <el-tag :type="userStore.creditScore >= 90 ? 'success' : userStore.creditScore >= 80 ? 'warning' : 'danger'">
                {{ userStore.creditScore }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="账户余额">
              <span class="balance-text">{{ formatCurrency(userStore.balance) }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- History Orders Card -->
        <div class="card history-card">
          <div class="card-header">
            <h3>历史订单查询</h3>
            <el-button @click="orderStore.fetchOrders()" :loading="orderStore.loading" icon="Refresh" circle size="small" />
          </div>
          
          <div class="table-container">
            <el-scrollbar max-height="400px">
              <el-table :data="orderStore.orders" v-loading="orderStore.loading" stripe style="width: 100%">
                <el-table-column prop="order_no" label="订单号" min-width="180" show-overflow-tooltip />
                <el-table-column prop="plate_number" label="车牌" width="100" />
                <el-table-column label="入场时间" min-width="150">
                  <template #default="{ row }">
                    {{ row.in_time ? formatDate(row.in_time) : (row.status === 0 ? '预约中' : '-') }}
                  </template>
                </el-table-column>
                <el-table-column label="费用" width="100">
                  <template #default="{ row }">
                    {{ formatCurrency(row.total_fee) }}
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag 
                      :type="getOrderStatusType(row.status)" 
                      :class="getCustomStatusClass(row.status)"
                      size="small"
                    >
                      {{ getOrderStatusText(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-scrollbar>
          </div>
        </div>
      </div>

      <!-- Right Sidebar (30%) -->
      <div class="right-sidebar">
        <!-- Cars Card -->
        <div class="card car-card">
          <div class="card-header">
            <div class="header-info">
              <h3>我的车辆</h3>
              <span class="sub-title">{{ userStore.cars.length }}/3</span>
            </div>
            <el-button type="primary" size="small" :disabled="userStore.cars.length >= 3" @click="showAddCarDialog = true">绑定</el-button>
          </div>
          
          <div v-if="userStore.cars.length > 0" class="car-list">
            <div v-for="car in userStore.cars" :key="car.car_id" class="car-item">
              <div class="car-icon">
                <el-icon><Van /></el-icon>
              </div>
              <div class="car-info">
                <div class="car-plate">{{ car.plate_number }}</div>
                <div class="car-nickname">{{ car.nickname || '未设置备注' }}</div>
              </div>
              <div class="car-actions">
                <el-button type="danger" link @click="handleRemoveCar(car.car_id)">解绑</el-button>
              </div>
            </div>
          </div>
          <el-empty v-else :image-size="60" description="暂无车辆" />
        </div>
      </div>
    </div>
    
    <!-- Recharge Dialog -->
    <el-dialog 
      v-model="showRechargeDialog" 
      title="账户充值" 
      width="450px"
      :close-on-click-modal="false"
    >
      <div class="dialog-content">
        <div class="balance-display">
          <div class="balance-label">当前余额</div>
          <div class="balance-amount">{{ formatCurrency(userStore.user.balance) }}</div>
        </div>
        
        <el-form :model="rechargeForm">
          <el-form-item label="充值金额">
            <el-input 
              v-model="rechargeForm.amount" 
              type="number" 
              placeholder="请输入充值金额"
              size="large"
              @keyup.enter="handleRecharge"
            >
              <template #prefix>¥</template>
            </el-input>
          </el-form-item>
          
          <div class="quick-amount">
            <span class="quick-label">快捷金额：</span>
            <el-button size="small" @click="rechargeForm.amount = 50">50元</el-button>
            <el-button size="small" @click="rechargeForm.amount = 100">100元</el-button>
            <el-button size="small" @click="rechargeForm.amount = 200">200元</el-button>
            <el-button size="small" @click="rechargeForm.amount = 500">500元</el-button>
          </div>
        </el-form>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showRechargeDialog = false" size="large">取消</el-button>
          <el-button type="primary" @click="handleRecharge" size="large">
            <el-icon class="mr-1"><Money /></el-icon>
            确认充值
          </el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- Add Car Dialog -->
    <el-dialog 
      v-model="showAddCarDialog" 
      title="绑定车辆" 
      width="500px" 
      destroy-on-close
      :close-on-click-modal="false"
    >
      <div class="dialog-content">
        <el-form 
          :model="addCarForm" 
          :rules="addCarRules" 
          ref="addCarFormRef" 
          label-width="90px"
        >
          <el-form-item label="车牌号码" prop="plate_number">
            <el-input 
              v-model="addCarForm.plate_number" 
              placeholder="请输入车牌号，如：京A88888"
              size="large"
              @keyup.enter="handleAddCar"
            >
              <template #prefix>
                <el-icon><Van /></el-icon>
              </template>
            </el-input>
            <div class="form-tip">✓ 支持蓝牌、绿牌及学/警车牌</div>
          </el-form-item>
          
          <el-form-item label="车辆备注" prop="nickname">
            <el-input 
              v-model="addCarForm.nickname" 
              placeholder="例如：我的宝马、家里的车" 
              maxlength="20" 
              show-word-limit
              size="large"
              @keyup.enter="handleAddCar"
            />
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddCarDialog = false" size="large">取消</el-button>
          <el-button type="primary" @click="handleAddCar" :loading="binding" size="large">
            <el-icon class="mr-1"><Van /></el-icon>
            确认绑定
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useOrderStore } from '@/stores/order'
import { bindCar, removeCar, recharge } from '@/api/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Van, Refresh, Money } from '@element-plus/icons-vue'
import { formatCurrency, formatDate, getRoleText, getOrderStatusText, getOrderStatusType } from '@/utils/format'

const router = useRouter()
const userStore = useUserStore()
const orderStore = useOrderStore()

const showRechargeDialog = ref(false)
const showAddCarDialog = ref(false)
const binding = ref(false)

// 键盘事件处理
const handleKeyPress = (e) => {
  if (e.key === 'Enter') {
    if (showRechargeDialog.value) {
      handleRecharge()
    } else if (showAddCarDialog.value) {
      handleAddCar()
    }
  }
}

// 监听对话框状态，添加/移除键盘监听
watch([showRechargeDialog, showAddCarDialog], ([recharge, addCar]) => {
  if (recharge || addCar) {
    document.addEventListener('keypress', handleKeyPress)
  } else {
    document.removeEventListener('keypress', handleKeyPress)
  }
})

onUnmounted(() => {
  document.removeEventListener('keypress', handleKeyPress)
})

const getCustomStatusClass = (status) => {
  if (status === 1) return 'status-parking'  // 进行中 - 紫色
  if (status === 5) return 'status-refunded' // 已退款 - 青色
  return ''
}

const rechargeForm = reactive({ amount: '' })
const addCarForm = reactive({ 
  plate_number: '',
  nickname: ''
})
const addCarFormRef = ref(null)

const addCarRules = {
  plate_number: [
    { required: true, message: '请输入车牌号', trigger: 'blur' },
    { 
      pattern: /^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{4,5}[A-Z0-9挂学警港澳]?$/,
      message: '车牌号格式不正确，如：京A88888',
      trigger: 'blur'
    }
  ],
  nickname: [
    { max: 20, message: '备注不能超过20个字符', trigger: 'blur' }
  ]
}

const handleRecharge = async () => {
  if (!rechargeForm.amount || rechargeForm.amount <= 0) {
    ElMessage.warning('请输入有效的充值金额')
    return
  }
  
  try {
    const res = await recharge({ amount: rechargeForm.amount })
    userStore.updateBalance(res.data.balance)
    ElMessage.success('充值成功')
    showRechargeDialog.value = false
    rechargeForm.amount = ''
  } catch (error) {
    console.error('Recharge failed:', error)
  }
}

const handleAddCar = async () => {
  if (!addCarFormRef.value) return
  
  await addCarFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    binding.value = true
    try {
      await bindCar(addCarForm)
      await userStore.fetchProfile()
      ElMessage.success('绑定成功')
      showAddCarDialog.value = false
      addCarForm.plate_number = ''
      addCarForm.nickname = ''
    } catch (error) {
      console.error('Bind car failed:', error)
    } finally {
      binding.value = false
    }
  })
}

const handleRemoveCar = async (carId) => {
  try {
    await ElMessageBox.confirm('确定要解绑该车辆吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await removeCar(carId)
    await userStore.fetchProfile()
    ElMessage.success('解绑成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Remove car failed:', error)
    }
  }
}

onMounted(async () => {
  await userStore.fetchProfile()
  await orderStore.fetchOrders()
})
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 30px;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.profile-layout {
  display: flex;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
  animation: slideUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.left-content > .card {
  animation: slideUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) both;
}

.left-content > .card:nth-child(2) {
  animation-delay: 0.2s;
}

.right-sidebar > .card {
  animation: slideUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) both;
  animation-delay: 0.4s;
}

.left-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0; /* 防止表格撑开 Flex 容器 */
}

.table-container {
  margin-top: 16px;
}

.right-sidebar {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.card h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.balance-text {
  font-size: 18px; 
  font-weight: 600; 
  color: #f97316;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header h3 {
  margin: 0;
}

.header-info h3 {
  margin-bottom: 4px;
}

.sub-title {
  font-size: 13px;
  color: #909399;
}

.car-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.car-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
}

.car-item:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.car-icon {
  font-size: 24px;
  color: #3b82f6;
  margin-right: 16px;
  display: flex;
  align-items: center;
}

.car-info {
  flex: 1;
}

.car-plate {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 2px;
}

.car-nickname {
  font-size: 13px;
  color: #64748b;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin: 4px 0 0;
  line-height: 1.4;
}

/* 自定义状态颜色 */
.status-parking {
  --el-tag-bg-color: #e0e7ff;
  --el-tag-border-color: #a5b4fc;
  --el-tag-text-color: #6366f1;
}

.status-refunded {
  --el-tag-bg-color: #dbeafe;
  --el-tag-border-color: #93c5fd;
  --el-tag-text-color: #1e40af;
}

/* 对话框美化 */
.dialog-content {
  padding: 8px 0;
}

.balance-display {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.balance-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 8px;
}

.balance-amount {
  font-size: 32px;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.quick-amount {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.quick-label {
  font-size: 13px;
  color: #64748b;
  white-space: nowrap;
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
