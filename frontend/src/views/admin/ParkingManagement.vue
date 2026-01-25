<template>
  <div class="parking-management">
    <!-- Header -->
    <div class="card header-card mb-4">
      <div class="header-content">
        <div class="header-info">
          <h3>车位资源监控</h3>
          <p class="subtitle">管理全校 {{ zones.length }} 个停车区域及实时状态</p>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <span class="label">当前空闲率</span>
            <span class="value success">{{ utilizationRate }}%</span>
          </div>
          <el-button type="primary" icon="Refresh" @click="fetchAllData">全局刷新</el-button>
        </div>
      </div>
    </div>

    <!-- Zones Grid -->
    <div class="zones-container" v-loading="loading">
      <div v-for="zone in zones" :key="zone.zone_id" class="zone-section card mb-4">
        <div class="zone-header">
          <div class="zone-title-box">
            <div class="zone-main-title">
              <el-icon class="icon-loc"><Location /></el-icon>
              <h4>{{ zone.name || ('区域 ' + zone.zone_id) }}</h4>
            </div>
            <div class="zone-meta">
              <el-tag size="small" effect="plain" type="info">ID: {{ zone.zone_id }}</el-tag>
              <el-tag size="small" effect="dark" type="warning" class="fee-tag">
                {{ zone.fee_rate }} 元/小时
              </el-tag>
              <el-button 
                type="primary" 
                link 
                icon="EditPen" 
                size="small" 
                @click="openFeeEdit(zone)"
              >修改费率</el-button>
            </div>
          </div>
          <div class="zone-summary">
            <span class="sum-item">总车位 <b>{{ zone.total_spots }}</b></span>
            <span class="sum-item success">空闲 <b>{{ getAvailableCount(zone.zone_id) }}</b></span>
          </div>
        </div>

        <div class="spots-grid">
          <div 
            v-for="spot in getSpotsByZone(zone.zone_id)" 
            :key="spot.spot_id"
            class="spot-node"
            :class="getStatusClass(spot.status)"
            @click="openSpotEdit(spot)"
          >
            <div class="spot-number">{{ spot.spot_number }}</div>
            <div class="spot-status-icon">
              <el-icon v-if="spot.status === 0"><Check /></el-icon>
              <el-icon v-else-if="spot.status === 1"><Van /></el-icon>
              <el-icon v-else-if="spot.status === 2"><Tools /></el-icon>
              <el-icon v-else><Clock /></el-icon>
            </div>
            <div class="spot-type-tag" v-if="spot.status === 0">空闲</div>
            <div class="spot-plate" v-if="spot.status === 1">{{ spot.current_plate || '停车中' }}</div>
            <div class="spot-plate" v-if="spot.status === 3">{{ spot.current_plate || '已预约' }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Fee Dialog -->
    <el-dialog v-model="showFeeDialog" title="区域费率调整" width="350px">
      <el-form label-position="top">
        <el-form-item :label="`[${selectedZone?.name}] 当前费率 (元/小时)`">
          <el-input-number 
            v-model="feeForm.fee_rate" 
            :min="0" 
            :precision="1" 
            :step="0.5"
            style="width: 100%"
            @keyup.enter="submitFeeUpdate"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFeeDialog = false">取消</el-button>
        <el-button type="primary" @click="submitFeeUpdate" :loading="submitting">保存生效</el-button>
      </template>
    </el-dialog>

    <!-- Edit Spot Dialog -->
    <el-dialog v-model="showEditDialog" title="车位状态手动干预" width="380px" center>
      <div class="dialog-body">
        <el-alert
          title="管理员提示"
          description="手动切换状态后，该车位的物理感应数据将被逻辑覆盖。"
          type="info"
          :closable="false"
          show-icon
          class="mb-3"
        />
        <el-radio-group v-model="editForm.status" class="status-radio-group">
          <el-radio :value="0" border class="radio-item">
            <el-tag type="success" size="small">空闲</el-tag> 正常对外开放
          </el-radio>
          <el-radio :value="1" border class="radio-item">
            <el-tag type="primary" size="small">占用</el-tag> 逻辑标记占用
          </el-radio>
          <el-radio :value="2" border class="radio-item">
            <el-tag type="danger" size="small">故障</el-tag> 设为维护状态
          </el-radio>
        </el-radio-group>
      </div>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="submitSpotUpdate" :loading="submitting">立即执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import { getZones, getSpots } from '@/api/parking'
import { updateParking } from '@/api/admin'
import { Location, Check, Van, Warning, Tools, Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const submitting = ref(false)
const zones = ref([])
const allSpots = ref([])

const showFeeDialog = ref(false)
const selectedZone = ref(null)
const feeForm = ref({ zone_id: null, fee_rate: 0 })

const showEditDialog = ref(false)
const editForm = ref({ spot_id: null, status: 0 })

// 键盘事件处理
const handleKeyPress = (e) => {
  if (e.key === 'Enter') {
    if (showFeeDialog.value) {
      submitFeeUpdate()
    } else if (showEditDialog.value) {
      submitSpotUpdate()
    }
  }
}

// 监听对话框状态
watch([showFeeDialog, showEditDialog], ([fee, edit]) => {
  if (fee || edit) {
    document.addEventListener('keypress', handleKeyPress)
  } else {
    document.removeEventListener('keypress', handleKeyPress)
  }
})

onUnmounted(() => {
  document.removeEventListener('keypress', handleKeyPress)
})

const utilizationRate = computed(() => {
  if (allSpots.value.length === 0) return 0
  const free = allSpots.value.filter(s => s.status === 0).length
  return ((free / allSpots.value.length) * 100).toFixed(1)
})

const fetchAllData = async () => {
  loading.value = true
  try {
    const zoneRes = await getZones()
    zones.value = zoneRes.data
    
    const spotPromises = zones.value.map(z => getSpots(z.zone_id))
    const spotResults = await Promise.all(spotPromises)
    allSpots.value = spotResults.flatMap(r => r.data)
  } finally {
    loading.value = false
  }
}

const getSpotsByZone = (zoneId) => {
  return allSpots.value.filter(s => s.zone_id === zoneId)
}

const getAvailableCount = (zoneId) => {
  return allSpots.value.filter(s => s.zone_id === zoneId && s.status === 0).length
}

const getStatusClass = (status) => {
  if (status === 0) return 'spot-available'
  if (status === 1) return 'spot-occupied'
  if (status === 2) return 'spot-maintenance'
  return 'spot-reserved'
}

const openFeeEdit = (zone) => {
  selectedZone.value = zone
  // FIX: 使用后端正确的字段名 fee_rate
  feeForm.value = { zone_id: zone.zone_id, fee_rate: zone.fee_rate }
  showFeeDialog.value = true
}

const submitFeeUpdate = async () => {
  submitting.value = true
  try {
    // FIX: 提交正确的字段名
    await updateParking({ zone_id: feeForm.value.zone_id, fee_rate: feeForm.value.fee_rate })
    ElMessage.success('区域费率更新成功')
    showFeeDialog.value = false
    fetchAllData()
  } finally {
    submitting.value = false
  }
}

const openSpotEdit = (spot) => {
  editForm.value = { spot_id: spot.spot_id, status: spot.status }
  showEditDialog.value = true
}

const submitSpotUpdate = async () => {
  submitting.value = true
  try {
    await updateParking(editForm.value)
    ElMessage.success('车位状态已成功干预')
    showEditDialog.value = false
    fetchAllData()
  } finally {
    submitting.value = false
  }
}

onMounted(fetchAllData)
</script>

<style scoped>
.parking-management {
  padding: 0;
}

.mb-4 { margin-bottom: 24px; }
.mb-3 { margin-bottom: 16px; }

.card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info h3 {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.subtitle {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 4px;
}

.stat-item .label { font-size: 12px; color: #94a3b8; }
.stat-item .value { font-size: 20px; font-weight: 700; display: block; }
.value.success { color: #10b981; }

.zone-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f1f5f9;
}

.zone-title-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.zone-main-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-loc { color: #3b82f6; font-size: 18px; }
.zone-main-title h4 { margin: 0; font-size: 17px; color: #1e293b; }

.zone-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fee-tag { background: #1e293b !important; color: #fbbf24 !important; border: none; font-weight: 700; }

.zone-summary {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #64748b;
  background: #f8fafc;
  padding: 8px 16px;
  border-radius: 12px;
}

.sum-item b { color: #1e293b; margin-left: 4px; }
.sum-item.success b { color: #10b981; }

.spots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 12px;
}

.spot-node {
  height: 95px;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
}

.spot-node:hover {
  transform: scale(1.03);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.spot-number { font-size: 15px; font-weight: 800; margin-bottom: 2px; }
.spot-status-icon { font-size: 22px; margin-bottom: 2px; }
.spot-type-tag { font-size: 11px; opacity: 0.7; }
.spot-plate { 
  font-size: 11px; 
  padding: 2px 6px; 
  background: rgba(255,255,255,0.4); 
  border-radius: 4px; 
  font-family: monospace;
}

.spot-available { background: #f0fdf4; color: #16a34a; border-color: #dcfce7; }
.spot-occupied { background: #eff6ff; color: #2563eb; border-color: #dbeafe; }
.spot-maintenance { background: #f3f4f6; color: #6b7280; border-color: #e5e7eb; }
.spot-reserved { background: #fff7ed; color: #ea580c; border-color: #ffedd5; }
.spot-maintenance .status-radio-group { width: 100%; display: flex; flex-direction: column; gap: 8px; }
.radio-item { width: 100%; margin: 0 !important; height: auto; padding: 12px !important; }

.dialog-body { padding: 10px 0; }
</style>
