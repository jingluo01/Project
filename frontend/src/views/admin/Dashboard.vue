<template>
  <div class="dashboard-content" v-loading="loading">
    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card shine-effect">
        <div class="stat-icon" style="background: #eff6ff">
          <el-icon color="#3b82f6"><TrendCharts /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">今日营收</div>
          <div class="stat-value">{{ formatCurrency(stats.today_revenue) }}</div>
          <div class="stat-trend success">
            <el-icon><CaretTop /></el-icon> <span>12.5%</span>
          </div>
        </div>
      </div>
      
      <div class="stat-card shine-effect">
        <div class="stat-icon" style="background: #f0fdf4">
          <el-icon color="#22c55e"><UserFilled /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">当前活跃用户</div>
          <div class="stat-value">{{ stats.active_users }}</div>
          <div class="stat-trend">保持稳定</div>
        </div>
      </div>
      
      <div class="stat-card shine-effect">
        <div class="stat-icon" style="background: #faf5ff">
          <el-icon color="#a855f7"><Document /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">实时订单数</div>
          <div class="stat-value">{{ stats.current_orders }}</div>
          <div class="stat-trend success">处理中</div>
        </div>
      </div>
      
      <div class="stat-card shine-effect">
        <div class="stat-icon" style="background: #fff7ed">
          <el-icon color="#f97316"><Location /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-label">空闲车位数</div>
          <div class="stat-value">{{ stats.available_spots }}</div>
          <div class="stat-trend info">利用率正常</div>
        </div>
      </div>
    </div>
    
    <!-- Charts Row -->
    <div class="charts-grid">
      <div class="chart-card card">
        <div class="card-header">
          <h3>近7日营收趋势</h3>
          <el-tag size="small">实时更新</el-tag>
        </div>
        <div ref="revenueChartRef" class="chart-box"></div>
      </div>
      
      <div class="chart-card card">
        <div class="card-header">
          <h3>车位利用率</h3>
        </div>
        <div ref="utilizationChartRef" class="chart-box"></div>
      </div>
    </div>
    
    <!-- Recent Orders -->
    <div class="table-card card">
      <div class="card-header">
        <h3>最新动态订单</h3>
        <el-button link @click="router.push('/admin/orders')">查看全部</el-button>
      </div>
      <el-table :data="recentOrders" style="width: 100%" stripe>
        <el-table-column prop="order_no" label="订单号" min-width="150" />
        <el-table-column prop="plate_number" label="车牌号" width="120">
          <template #default="{ row }">
            <span class="plate-tag">{{ row.plate_number }}</span>
          </template>
        </el-table-column>
        <el-table-column label="入场时间" min-width="160">
          <template #default="{ row }">
            {{ formatDate(row.in_time) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getOrderStatusType(row.status)" effect="plain">
              {{ getOrderStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="费用" width="100">
          <template #default="{ row }">
            <span class="fee-text">{{ formatCurrency(row.total_fee) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getStats, getAllOrders } from '@/api/admin'
import { formatCurrency, formatDate, getOrderStatusText, getOrderStatusType } from '@/utils/format'
import * as echarts from 'echarts'
import {
  TrendCharts, UserFilled, Document, Location, CaretTop
} from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const stats = ref({
  today_revenue: 0,
  active_users: 0,
  current_orders: 0,
  available_spots: 0,
  revenue_trend: [],
  utilization_rate: 0
})
const recentOrders = ref([])
const revenueChartRef = ref(null)
const utilizationChartRef = ref(null)

const initRevenueChart = () => {
  if (!revenueChartRef.value) return
  const chart = echarts.init(revenueChartRef.value)
  const option = {
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(255, 255, 255, 0.9)' },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: stats.value.revenue_trend.map(item => {
        const date = new Date(item.date)
        return `${date.getMonth() + 1}/${date.getDate()}`
      }),
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    yAxis: { 
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } }
    },
    series: [{
      data: stats.value.revenue_trend.map(item => item.revenue),
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      itemStyle: { color: '#3b82f6' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(59, 130, 246, 0.2)' },
          { offset: 1, color: 'rgba(59, 130, 246, 0)' }
        ])
      },
      lineStyle: { width: 3 }
    }]
  }
  chart.setOption(option)
}

const initUtilizationChart = () => {
  if (!utilizationChartRef.value) return
  const chart = echarts.init(utilizationChartRef.value)
  const utilized = stats.value.utilization_rate
  const available = 100 - utilized
  const option = {
    tooltip: { trigger: 'item' },
    legend: { bottom: '5%', left: 'center', itemWidth: 10, itemHeight: 10 },
    series: [{
      type: 'pie',
      radius: ['60%', '80%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      data: [
        { value: utilized, name: '已使用', itemStyle: { color: '#3b82f6' } },
        { value: available, name: '空闲', itemStyle: { color: '#10b981' } }
      ]
    }]
  }
  chart.setOption(option)
}

const fetchData = async () => {
  loading.value = true
  try {
    const [statsRes, ordersRes] = await Promise.all([
      getStats(),
      getAllOrders(1, 10)
    ])
    stats.value = statsRes.data
    recentOrders.value = ordersRes.data.orders
    setTimeout(() => {
      initRevenueChart()
      initUtilizationChart()
    }, 100)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  gap: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-info { flex: 1; }
.stat-label { font-size: 14px; color: #64748b; margin-bottom: 4px; }
.stat-value { font-size: 24px; font-weight: 700; color: #1e293b; }
.stat-trend { font-size: 12px; margin-top: 4px; color: #94a3b8; }
.stat-trend.success { color: #10b981; }

.charts-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.chart-box { height: 320px; width: 100%; }

.card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header h3 { font-size: 16px; font-weight: 600; color: #334155; }

.plate-tag {
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 6px;
  font-family: monospace;
  color: #475569;
}

.fee-text { font-weight: 600; color: #f97316; }

.table-card { margin-top: 24px; }
</style>
