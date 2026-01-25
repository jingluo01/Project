<template>
  <div class="orders-container">
    <div class="orders-header">
      <h1>订单历史</h1>
      <el-radio-group v-model="selectedStatus" @change="handleStatusChange">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button :label="0">已预约</el-radio-button>
        <el-radio-button :label="1">进行中</el-radio-button>
        <el-radio-button :label="2">待支付</el-radio-button>
        <el-radio-button :label="6">违约</el-radio-button>
        <el-radio-button :label="3">已完成</el-radio-button>
      </el-radio-group>
      <el-button @click="router.push('/parking')">返回停车地图</el-button>
    </div>
    
    <div class="orders-content card">
      <el-table :data="orderStore.orders" v-loading="orderStore.loading">
        <el-table-column prop="order_no" label="订单号" width="180" />
        <el-table-column prop="plate_number" label="车牌号" width="120" />
        <el-table-column label="预约时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.reserve_time) }}
          </template>
        </el-table-column>
        <el-table-column label="入场时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.in_time) }}
          </template>
        </el-table-column>
        <el-table-column label="出场时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.out_time) }}
          </template>
        </el-table-column>
        <el-table-column label="费用" width="100">
          <template #default="{ row }">
            {{ formatCurrency(row.total_fee) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getOrderStatusType(row.status)">
              {{ getOrderStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button v-if="[2, 6].includes(row.status)" type="primary" size="small" @click="handlePay(row)">
              支付
            </el-button>
            <el-button v-if="row.status === 0" type="danger" size="small" @click="handleCancel(row)">
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useOrderStore } from '@/stores/order'
import { payOrder, cancelOrder } from '@/api/order'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDate, formatCurrency, getOrderStatusText, getOrderStatusType } from '@/utils/format'

const router = useRouter()
const orderStore = useOrderStore()

const handlePay = async (order) => {
  try {
    await ElMessageBox.confirm(`确认支付 ${formatCurrency(order.total_fee)} 吗？`, '支付确认', {
      confirmButtonText: '确认支付',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await payOrder({ order_id: order.order_id, pay_way: 0 })
    ElMessage.success('支付成功')
    await orderStore.fetchOrders()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Pay failed:', error)
    }
  }
}

const handleCancel = async (order) => {
  try {
    await ElMessageBox.confirm('确定要取消该订单吗？', '取消确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await cancelOrder({ order_id: order.order_id })
    ElMessage.success('取消成功')
    await orderStore.fetchOrders()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Cancel failed:', error)
    }
  }
}

onMounted(() => {
  orderStore.fetchOrders()
})
</script>

<style scoped>
.orders-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 30px;
}

.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.orders-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
}
</style>
