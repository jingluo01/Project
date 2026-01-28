<template>
  <div class="order-management card">
    <div class="card-header">
      <div class="header-info">
        <h3>全量订单监控</h3>
        <p class="subtitle">共处理 {{ total }} 笔停车业务</p>
      </div>
      <div class="header-filters">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 250px"
          @change="fetchOrders"
        />
        <el-select 
          v-model="statusFilter" 
          placeholder="订单状态" 
          clearable 
          style="width: 150px"
          @change="fetchOrders"
        >
          <el-option label="预约中" :value="0" />
          <el-option label="停车中" :value="1" />
          <el-option label="待支付" :value="2" />
          <el-option label="已结算" :value="3" />
          <el-option label="已取消" :value="4" />
          <el-option label="已退款" :value="5" />
          <el-option label="超时违约" :value="6" />
        </el-select>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索订单/车牌/姓名/学号..."
          prefix-icon="Search"
          style="width: 260px"
          clearable
          @clear="fetchOrders"
          @keyup.enter="fetchOrders"
        />
        <el-button type="primary" icon="Search" @click="fetchOrders">执行查询</el-button>
      </div>
    </div>

    <el-table :data="orders" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="order_no" label="订单记录编号" min-width="170" />
      <el-table-column prop="plate_number" label="车牌号" width="130">
        <template #default="{ row }">
          <span class="plate-highlight">{{ row.plate_number }}</span>
        </template>
      </el-table-column>
      <el-table-column label="关联用户" min-width="150">
        <template #default="{ row }">
          <div class="user-cell">
            <span class="username">{{ row.username }}</span>
            <span class="user-no">{{ row.user_no }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="停留时段" min-width="210">
        <template #default="{ row }">
          <div class="time-range">
            <div class="time-line"><span class="dot in"></span> {{ formatDate(row.in_time || row.reserve_time) }}</div>
            <div v-if="row.out_time" class="time-line mt-1">
              <span class="dot out"></span> {{ formatDate(row.out_time) }}
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="交易状态" width="120">
        <template #default="{ row }">
          <el-tag 
            :type="getOrderStatusType(row.status)" 
            :class="getCustomStatusClass(row.status)"
            effect="light"
          >
            {{ getOrderStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="费用总计" width="110">
        <template #default="{ row }">
          <span class="money-text">{{ formatCurrency(row.total_fee) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="管理操作" width="180" fixed="right">
        <template #default="{ row }">
          <div class="op-buttons">
            <el-button size="small" type="primary" link icon="Document" @click="viewDetail(row)">详情</el-button>
            <el-button 
              v-if="row.status === 0" 
              size="small" 
              type="info" 
              link 
              icon="Close"
              @click="handleForceCancel(row)"
            >取消</el-button>
            <el-button 
              v-if="row.status === 1" 
              size="small" 
              type="warning" 
              link 
              icon="VideoPause"
              @click="handleForceClose(row)"
            >结束</el-button>
            <el-button 
              v-if="row.status === 3" 
              size="small" 
              type="danger" 
              link 
              icon="RefreshLeft"
              @click="handleRefund(row)"
            >退款</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-area">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next, jumper"
        @current-change="fetchOrders"
      />
    </div>

    <!-- Details Drawer -->
    <el-drawer
      v-model="showDetail"
      title="订单流水全视图"
      direction="rtl"
      size="420px"
      custom-class="order-drawer"
    >
      <div v-if="currentOrder" class="detail-container">
        <div class="detail-section">
          <h4 class="section-title">核心信息</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="label">流水单号</span>
              <span class="value copyable">{{ currentOrder.order_no }}</span>
            </div>
            <div class="detail-item">
              <span class="label">绑定车牌</span>
              <span class="value plate-val">{{ currentOrder.plate_number }}</span>
            </div>
            <div class="detail-item">
              <span class="label">绑定用户</span>
              <span class="value">{{ currentOrder.username || currentOrder.user_id }} <small v-if="currentOrder.user_no">({{ currentOrder.user_no }})</small></span>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="detail-section">
          <h4 class="section-title">停放详情</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="label">所属区域</span>
              <span class="value">{{ currentOrder.zone_name || currentOrder.zone_id }}</span>
            </div>
            <div class="detail-item">
              <span class="label">车位编号</span>
              <span class="value">{{ currentOrder.spot_no || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">预约时间</span>
              <span class="value">{{ formatDate(currentOrder.reserve_time) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">入场时间</span>
              <span class="value">{{ currentOrder.in_time ? formatDate(currentOrder.in_time) : '尚未入场' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">出场时间</span>
              <span class="value">{{ currentOrder.out_time ? formatDate(currentOrder.out_time) : '车辆尚未离场' }}</span>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="detail-section total-section">
          <div class="price-row">
            <span class="label">结算状态</span>
            <el-tag :type="getOrderStatusType(currentOrder.status)">{{ getOrderStatusText(currentOrder.status) }}</el-tag>
          </div>
          <div class="price-row mt-4">
            <span class="label">实付总计</span>
            <span class="value price-big">{{ formatCurrency(currentOrder.total_fee) }}</span>
          </div>
          <div class="price-row mt-1" v-if="currentOrder.pay_time">
            <span class="label">支付时间</span>
            <span class="value date-small">{{ formatDate(currentOrder.pay_time) }}</span>
          </div>
        </div>

        <div class="drawer-footer">
          <el-button 
            v-if="currentOrder.status === 0" 
            type="info" 
            style="flex: 1"
            @click="handleForceCancel(currentOrder)"
          >强制取消预约</el-button>
          <el-button 
            v-if="currentOrder.status === 1" 
            type="warning" 
            style="flex: 1"
            @click="handleForceClose(currentOrder)"
          >强制释放车位</el-button>
          <el-button 
            v-if="currentOrder.status === 3" 
            type="danger" 
            style="flex: 1"
            @click="handleRefund(currentOrder)"
          >立即退款</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAllOrders, forceExitOrder } from '@/api/admin'
import { refundOrder, cancelOrder } from '@/api/order'
import { formatCurrency, formatDate, getOrderStatusText, getOrderStatusType } from '@/utils/format'
import { ElMessageBox, ElMessage } from 'element-plus'

const loading = ref(false)
const orders = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const statusFilter = ref(null)
const searchKeyword = ref('')
const dateRange = ref([])

const getCustomStatusClass = (status) => {
  if (status === 1) return 'status-parking'  // 进行中 - 紫色
  if (status === 5) return 'status-refunded' // 已退款 - 青色
  return ''
}

const showDetail = ref(false)
const currentOrder = ref(null)

const fetchOrders = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      perPage: pageSize.value,
      status: statusFilter.value,
      query: searchKeyword.value
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.startDate = dateRange.value[0] + ' 00:00:00'
      params.endDate = dateRange.value[1] + ' 23:59:59'
    }

    const res = await getAllOrders(params)
    orders.value = res.data.orders
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

const viewDetail = (order) => {
  currentOrder.value = order
  showDetail.value = true
}

const handleForceClose = (order) => {
  ElMessageBox.confirm('确定要强制结束该订单吗？该操作将立即标记车位为空闲并结算当前费用。', '严重警告', {
    confirmButtonText: '确定释放',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await forceExitOrder(order.plate_number)
      ElMessage.success('订单已强制关闭，车位已释放，请提醒用户及时支付账单')
      showDetail.value = false
      fetchOrders()
    } catch (err) {}
  })
}

const handleForceCancel = (order) => {
  ElMessageBox.confirm('确定要强制取消该预约吗？此操作将立即释放预留车位。', '操作确认', {
    confirmButtonText: '确定取消',
    type: 'info'
  }).then(async () => {
    try {
      await cancelOrder({ order_id: order.order_id })
      ElMessage.success('预约已成功取消并释放')
      showDetail.value = false
      fetchOrders()
    } catch (err) {}
  })
}

const handleRefund = (order) => {
  ElMessageBox.confirm('确定要为该笔金额执行全额退款吗？资金将充值回用户余额。', '退款确认').then(async () => {
    try {
      await refundOrder({ order_id: order.order_id })
      ElMessage.success('退款成功，资金已原路返还至用户余额')
      showDetail.value = false
      fetchOrders()
    } catch (err) {}
  })
}

onMounted(fetchOrders)
</script>

<style scoped>
.order-management { padding: 24px; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-info h3 { font-size: 19px; font-weight: 800; color: #0f172a; margin: 0; }
.subtitle { font-size: 13px; color: #64748b; margin-top: 4px; }

.header-filters { display: flex; gap: 12px; }

.plate-highlight {
  background: #f8fafc;
  padding: 6px 12px;
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #1e293b;
  border: 1px solid #e2e8f0;
}

.time-range { font-size: 13px; color: #475569; }
.time-line { display: flex; align-items: center; gap: 8px; }
.dot { width: 6px; height: 6px; border-radius: 50%; }
.dot.in { background: #3b82f6; }
.dot.out { background: #10b981; }
.mt-1 { margin-top: 6px; }

.money-text { font-weight: 800; color: #f59e0b; font-size: 15px; }

.op-buttons { display: flex; gap: 4px; }

.pagination-area {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

/* Drawer Styles */
.detail-container { padding: 0 4px; position: relative; height: 100%; display: flex; flex-direction: column; }
.section-title { font-size: 15px; font-weight: 700; color: #334155; margin-bottom: 16px; display: flex; align-items: center; }
.section-title::before { content: ""; width: 4px; height: 14px; background: #3b82f6; margin-right: 8px; border-radius: 2px; }

.detail-grid { display: flex; flex-direction: column; gap: 14px; }
.detail-item { display: flex; justify-content: space-between; align-items: center; }
.detail-item .label { color: #94a3b8; font-size: 13px; }
.detail-item .value { color: #1e293b; font-weight: 600; font-size: 14px; }
.plate-val { background: #1e293b; color: white !important; padding: 2px 8px; border-radius: 4px; font-family: monospace; }

.total-section { background: #f8fafc; padding: 20px; border-radius: 16px; margin-top: auto; }
.price-row { display: flex; justify-content: space-between; align-items: center; }
.price-big { font-size: 24px; color: #f59e0b; font-weight: 900; }
.date-small { font-size: 12px; color: #94a3b8; }
.mt-4 { margin-top: 16px; }

.drawer-footer { margin-top: 24px; display: flex; gap: 12px; }

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

/* User Cell Styling */
.user-cell {
  display: flex;
  flex-direction: column;
  line-height: 1.4;
}

.username {
  font-weight: 600;
  color: #1e293b;
}

.user-no {
  font-size: 11px;
  color: #94a3b8;
  font-family: 'JetBrains Mono', monospace;
}
</style>
