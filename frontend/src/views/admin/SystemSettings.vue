<template>
  <div class="system-settings-view">
    <!-- Header Section -->
    <div class="settings-header">
      <div class="title-section">
        <el-icon class="main-icon"><Setting /></el-icon>
        <div class="text">
          <h2>系统业务参数配置</h2>
          <p>动态调整全局计费、信用阈值及违约规则</p>
        </div>
      </div>
      <div class="action-section">
        <el-button v-if="!isEditing" type="primary" size="large" @click="startEdit">
          <el-icon><Edit /></el-icon>
          进入编辑模式
        </el-button>
        <div v-else class="edit-actions">
          <el-button @click="cancelEdit">取消</el-button>
          <el-button type="success" :loading="saving" @click="handleSave">
            <el-icon><Check /></el-icon>
            保存并实时应用
          </el-button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="settings-body" v-loading="loading">
      <el-form :model="form" label-position="top" :disabled="!isEditing">
        <el-row :gutter="24">
          <!-- Left Column: Core Rules -->
          <el-col :span="14">
            <div class="config-card section-primary">
              <div class="card-title">
                <el-icon><Connection /></el-icon> 核心业务阈值
              </div>
              <div class="grid-layout">
                <el-form-item label="信用极佳阈值" class="compact-item">
                  <el-input-number v-model="form.credit_thresholds.perfect" :min="form.credit_thresholds.good + 1" :max="100" />
                  <span class="unit">分</span>
                </el-form-item>
                <el-form-item label="信用良好阈值" class="compact-item">
                  <el-input-number v-model="form.credit_thresholds.good" :min="form.credit_thresholds.min + 1" :max="form.credit_thresholds.perfect - 1" />
                  <span class="unit">分</span>
                </el-form-item>
                <el-form-item label="信用及格线 (限制线)" class="compact-item full-width">
                  <el-input-number v-model="form.credit_thresholds.min" :min="0" :max="form.credit_thresholds.good - 1" />
                  <span class="unit">分</span>
                  <div class="item-desc">低于该分数的用户将失去车位预约权限</div>
                </el-form-item>
                <el-form-item label="自动取消预约时限" class="compact-item full-width">
                  <el-input-number v-model="form.reservation_timeout" :min="5" :max="1440" :step="5" />
                  <span class="unit">分钟</span>
                  <div class="item-desc">预约成功后未在此时限内入场，系统将自动取消订单</div>
                </el-form-item>
              </div>
            </div>

            <div class="config-card section-warning">
              <div class="card-title">
                <el-icon><Warning /></el-icon> 惩罚与时限规则
              </div>
              <div class="grid-layout">
                <el-form-item label="离场支付超时时限" class="compact-item">
                  <el-input-number v-model="form.payment_timeout" :min="1" :max="168" />
                  <span class="unit">小时</span>
                </el-form-item>
                <el-form-item label="单次违约行政扣费" class="compact-item">
                   <el-input-number v-model="form.violation_fee" :min="0" :precision="2" :step="0.5" />
                   <span class="unit">元</span>
                </el-form-item>
                <el-form-item label="入场逾期扣分" class="compact-item">
                   <el-input-number v-model="form.penalty_delay" :min="0" :max="100" />
                   <span class="unit">分</span>
                </el-form-item>
                <el-form-item label="账单逾期扣分" class="compact-item">
                   <el-input-number v-model="form.penalty_timeout" :min="0" :max="100" />
                   <span class="unit">分</span>
                </el-form-item>
              </div>
            </div>
          </el-col>

          <!-- Right Column: Billing -->
          <el-col :span="10">
            <div class="config-card section-success">
              <div class="card-title">
                <el-icon><Coin /></el-icon> 计费与折扣矩阵
              </div>
              <el-form-item label="基础费用乘数 (Multiplier)" class="big-item">
                <el-input-number v-model="form.fee_multiplier" :min="0.1" :precision="1" :step="0.5" style="width: 100%" />
                <div class="formula">
                  <span>最终时费</span> = <span>基准价</span> × <strong class="highlight">{{ form.fee_multiplier }}x</strong> × <span>折扣</span>
                </div>
              </el-form-item>
              
              <el-divider>子角色折扣率 (精度: 0.01)</el-divider>
              
              <div class="discount-list">
                <div class="discount-row">
                  <div class="role-tag teacher">教职工</div>
                  <el-input-number v-model="form.roles['2']" :min="0" :max="1" :precision="2" :step="0.01" />
                </div>
                <div class="discount-row">
                  <div class="role-tag student">学生</div>
                  <el-input-number v-model="form.roles['1']" :min="0" :max="1" :precision="2" :step="0.01" />
                </div>
                <div class="discount-row disabled">
                  <div class="role-tag guest">校外/访客</div>
                  <span class="fixed-val">1.00 (无折扣)</span>
                </div>
              </div>
            </div>

            <div class="info-alert">
              <el-icon><InfoFilled /></el-icon>
              <div class="alert-content">
                <h4>关于配置同步</h4>
                <p>修改操作将直接更新数据库 sys_config 表。此操作不修改代码文件，配置实时对后续所有订单生效。</p>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getAdminConfig, updateAdminConfig } from '@/api/admin'
import { Setting, Edit, Check, Connection, Warning, Coin, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const isEditing = ref(false)

const form = reactive({
    credit_thresholds: { min: 70, good: 85, perfect: 100 },
    roles: { '1': 0.9, '2': 0.8 },
    violation_fee: 5.0,
    reservation_timeout: 30,
    fee_multiplier: 10.0,
    payment_timeout: 24,
    penalty_timeout: 30,
    penalty_delay: 10
})

let originalData = null

const fetchConfigs = async () => {
  loading.value = true
  try {
    const res = await getAdminConfig()
    if (res.success) {
      Object.assign(form, res.data)
      originalData = JSON.parse(JSON.stringify(res.data))
    }
  } catch (e) {
      ElMessage.error('获取配置失败')
  } finally {
    loading.value = false
  }
}

const startEdit = () => {
    isEditing.value = true
}

const cancelEdit = () => {
    isEditing.value = false
    if (originalData) {
        Object.assign(form, JSON.parse(JSON.stringify(originalData)))
    }
}

const handleSave = async () => {
    saving.value = true
    try {
        const res = await updateAdminConfig(form)
        if (res.success) {
            ElMessage.success('配置已更新并实时生效')
            isEditing.value = false
            originalData = JSON.parse(JSON.stringify(form))
        }
    } finally {
        saving.value = false
    }
}

onMounted(fetchConfigs)
</script>

<style scoped>
.system-settings-view {
  padding: 10px;
  max-width: 1200px;
  margin: 0 auto;
}

/* Header Styling */
.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 0 4px;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.main-icon {
  font-size: 32px;
  color: #3b82f6;
  background: white;
  padding: 10px;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
}

.title-section h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  color: #1e293b;
}

.title-section p {
  margin: 4px 0 0;
  font-size: 13px;
  color: #64748b;
}

/* Card Styling */
.config-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  transition: all 0.3s;
}

.config-card:hover {
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #334155;
  margin-bottom: 20px;
}

.card-title .el-icon {
  font-size: 18px;
  color: #3b82f6;
}

/* Layout Utilities */
.grid-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px 24px;
}

.compact-item {
  margin-bottom: 4px !important;
}

.full-width {
  grid-column: span 2;
}

.item-desc {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}

.unit {
  font-size: 13px;
  color: #64748b;
  margin-left: 8px;
}

.big-item {
  background: #f8fafc;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 20px !important;
}

.formula {
  margin-top: 12px;
  font-size: 13px;
  color: #64748b;
  background: white;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px dashed #cbd5e1;
}

.highlight {
  color: #ef4444;
}

/* Discount List */
.discount-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.discount-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f1f5f9;
  border-radius: 8px;
}

.discount-row.disabled {
  opacity: 0.6;
  background: #f8fafc;
}

.role-tag {
  font-size: 13px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 4px;
}

.teacher { color: #3b82f6; background: #dbeafe; }
.student { color: #10b981; background: #dcfce7; }
.guest { color: #64748b; background: #f1f5f9; }

.fixed-val {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}

/* Info Alert */
.info-alert {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 12px;
  margin-top: 10px;
}

.info-alert .el-icon {
  font-size: 20px;
  color: #1d4ed8;
}

.alert-content h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #1e3a8a;
}

.alert-content p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #1e40af;
  line-height: 1.5;
}

/* Form Overrides */
:deep(.el-form-item__label) {
  font-weight: 600 !important;
  color: #475569 !important;
  font-size: 13px !important;
  padding-bottom: 4px !important;
}

:deep(.el-input-number) {
  width: 140px;
}
</style>
