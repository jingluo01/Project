<template>
  <div class="user-management card">
    <div class="card-header">
      <div class="header-info">
        <h3>用户账号管理</h3>
        <p class="subtitle">共 {{ total }} 位注册用户</p>
      </div>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索学号/姓名..."
          prefix-icon="Search"
          class="search-input"
          clearable
          @clear="fetchUsers"
          @keyup.enter="fetchUsers"
        />
        <el-button type="primary" icon="Refresh" @click="fetchUsers">刷新列表</el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="user-tabs">
      <el-tab-pane label="校园用户" name="users">
        <el-table :data="regularUsers" v-loading="loading" stripe border style="width: 100%">
          <el-table-column prop="user_no" label="学号/工号" width="130" fixed sortable />
          <el-table-column prop="username" label="姓名" width="120" sortable />
          <el-table-column label="身份" width="120">
            <template #default="{ row }">
              <el-tag :type="getRoleType(row.role)" effect="plain" size="small">
                {{ getRoleName(row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="信用分" width="150" sortable prop="credit_score">
            <template #default="{ row }">
              <div class="credit-wrap">
                <span :class="['credit-num', getCreditClass(row.credit_score)]">{{ row.credit_score }}%</span>
                <el-progress 
                  :percentage="row.credit_score" 
                  :show-text="false"
                  :color="customColors"
                  :stroke-width="12"
                />
              </div>
            </template>
          </el-table-column>
          <el-table-column label="账户余额" width="130" sortable prop="balance">
            <template #default="{ row }">
              <span class="balance-text highlight">{{ formatCurrency(row.balance) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-switch
                v-model="row.is_active"
                active-text="正常"
                inactive-text="停用"
                inline-prompt
                @change="(val) => handleStatusChange(row, val)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="280" fixed="right">
            <template #default="{ row }">
              <div class="op-grid">
                <el-button size="small" icon="Edit" @click="openEditDialog(row)">编辑</el-button>
                <el-button size="small" type="success" icon="Money" @click="openRechargeDialog(row)">充值</el-button>
                <el-popconfirm title="确定重置密码吗？" @confirm="handleResetPwd(row)">
                  <template #reference><el-button size="small" type="warning" icon="Lock">重置</el-button></template>
                </el-popconfirm>
                <el-popconfirm title="确定删除吗？" @confirm="handleDelete(row)">
                  <template #reference><el-button size="small" type="danger" icon="Delete">删除</el-button></template>
                </el-popconfirm>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="管理人员" name="admins">
        <el-table :data="adminUsers" v-loading="loading" stripe border style="width: 100%">
          <el-table-column prop="user_no" label="账号" width="150" sortable />
          <el-table-column prop="username" label="管理称呼" width="150" sortable />
          <el-table-column label="级别" width="150">
            <template #default>
              <el-tag type="danger" effect="dark">系统管理员</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '正常运行' : '锁定' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="备注">
            <template #default>
              <span class="text-secondary">平台超级管理账户</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" :disabled="row.username === 'admin'" @click="handleResetPwd(row)">重置密钥</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <div class="pagination-area" v-if="activeTab === 'users'">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="totalRegular"
        layout="total, prev, pager, next, jumper"
        @current-change="fetchUsers"
      />
    </div>

    <!-- Edit User Dialogue -->
    <el-dialog v-model="showEditDialog" title="用户信息编辑" width="500px">
      <el-form :model="editForm" label-width="90px" :rules="editRules" ref="editFormRef">
        <el-form-item label="学号/工号" prop="user_no">
          <el-input v-model="editForm.user_no" disabled>
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
          <div class="form-tip">账号唯一标识，不可修改</div>
        </el-form-item>
        
        <el-form-item label="姓名" prop="username">
          <el-input v-model="editForm.username" placeholder="请输入真实姓名">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="用户身份" prop="role">
          <el-select v-model="editForm.role" placeholder="选择身份类别" style="width: 100%">
            <el-option label="学生" :value="1" />
            <el-option label="教职工" :value="2" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="信用分" prop="credit_score">
          <el-slider 
            v-model="editForm.credit_score" 
            :min="0" :max="100" 
            :marks="sliderMarks"
            style="margin-bottom: 30px; padding: 0 10px;"
          />
          <div class="credit-control-row">
            <el-input-number 
              v-model="editForm.credit_score" 
              :min="0" :max="100" 
              size="default"
              controls-position="right"
              class="credit-input"
            />
            <el-tag :type="getCreditTagType(editForm.credit_score)" size="large" effect="dark" class="credit-level-tag">
              {{ getCreditLevel(editForm.credit_score) }}
            </el-tag>
          </div>
        </el-form-item>
        
        <el-form-item label="账户余额">
          <div class="balance-readonly">
            <span class="currency">¥</span>
            <span class="amount">{{ editForm.balance }}</span>
          </div>
        </el-form-item>
        
        <el-form-item label="账户状态" prop="is_active">
          <el-switch v-model="editForm.is_active" active-text="正常" inactive-text="锁定" inline-prompt />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="submitEdit" :loading="submitting">
            <el-icon class="mr-1"><Check /></el-icon>保存修改
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Recharge Dialog -->
    <el-dialog v-model="showRechargeDialog" title="模拟余额充值" width="350px">
      <el-form label-position="top">
        <el-form-item label="充值金额 (元)">
          <el-input-number v-model="rechargeAmount" :min="1" style="width: 100%" @keyup.enter="submitRecharge" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRechargeDialog = false">取消</el-button>
        <el-button type="success" @click="submitRecharge" :loading="submitting">立即入账</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, computed } from 'vue'
import { getUsers, updateUser, getAdminConfig } from '@/api/admin'
import { formatCurrency } from '@/utils/format'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Check, Money, Lock, Delete, InfoFilled } from '@element-plus/icons-vue'

const activeTab = ref('users')
const loading = ref(false)
const submitting = ref(false)
const users = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const sysConfig = ref({
  credit_thresholds: { min: 70, perfect: 100, good: 85 }
})

const sliderMarks = computed(() => {
  const { min, good } = sysConfig.value.credit_thresholds
  return {
    0: '0',
    [min]: '及格',
    [good]: '良好',
    100: '优秀'
  }
})

const regularUsers = computed(() => users.value.filter(u => u.role !== 3))
const adminUsers = computed(() => users.value.filter(u => u.role === 3))
const totalRegular = computed(() => total.value - adminUsers.value.length)

const getRoleName = (role) => {
  const map = { 1: '学生', 2: '教职工', 3: '系统管理员' }
  return map[role] || '校园用户'
}

const getRoleType = (role) => {
  if (role === 2) return 'warning'
  if (role === 1) return 'primary'
  return 'info' // 默认返回 info，消除 '' 导致的 Vue 警告
}

const getCreditLevel = (score) => {
  const { min, good } = sysConfig.value.credit_thresholds
  if (score < min) return '状态极差'
  if (score < good) return '信用及格'
  if (score < 100) return '表现良好'
  return '信用极佳'
}

const getCreditTagType = (score) => {
  const { min, good } = sysConfig.value.credit_thresholds
  if (score < min) return 'danger'
  if (score < good) return 'warning'
  return 'success'
}

const customColors = computed(() => {
  const { min, good } = sysConfig.value.credit_thresholds
  return [
    { color: '#f56c6c', percentage: min },
    { color: '#e6a23c', percentage: good },
    { color: '#67c23a', percentage: 100 },
  ]
})

const showEditDialog = ref(false)
const editFormRef = ref(null)
const editForm = ref({ 
  id: null, 
  user_no: '',
  username: '', 
  role: 1,
  credit_score: 100,
  balance: 0,
  is_active: true
})

const editRules = {
  username: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 20, message: '姓名长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择用户身份', trigger: 'change' }
  ],
  credit_score: [
    { required: true, message: '请设置信用分', trigger: 'blur' },
    { type: 'number', min: 0, max: 100, message: '信用分范围为 0-100', trigger: 'blur' }
  ]
}

const showRechargeDialog = ref(false)
const rechargeAmount = ref(100)
const selectedUser = ref(null)

// 键盘事件处理
const handleKeyPress = (e) => {
  if (e.key === 'Enter') {
    if (showEditDialog.value) {
      submitEdit()
    } else if (showRechargeDialog.value) {
      submitRecharge()
    }
  }
}

// 监听对话框状态
watch([showEditDialog, showRechargeDialog], ([edit, recharge]) => {
  if (edit || recharge) {
    document.addEventListener('keypress', handleKeyPress)
  } else {
    document.removeEventListener('keypress', handleKeyPress)
  }
})

onUnmounted(() => {
  document.removeEventListener('keypress', handleKeyPress)
})

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await getUsers(page.value, pageSize.value)
    // 过滤掉系统预留的 'guest' 账户以及 role=0 的外部访客，这些不属于校内人员管理范畴
    users.value = res.data.users.filter(u => u.user_no !== 'guest' && u.role !== 0)
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

const getCreditClass = (score) => {
  const { min, good } = sysConfig.value.credit_thresholds
  if (score < min) return 'danger'
  if (score < good) return 'warning'
  return 'success'
}

const handleStatusChange = async (user, val) => {
  try {
    await updateUser({ user_id: user.user_id, is_active: val })
    ElMessage.success(`${user.username} 账号已${val ? '激活' : '锁定'}`)
  } catch (err) {
    user.is_active = !val 
  }
}

const handleResetPwd = async (user) => {
  try {
    await updateUser({ user_id: user.user_id, password: 'reset_trigger' })
    ElMessage.success('密码已重置为默认值')
  } catch (err) {}
}

const handleDelete = async (user) => {
  try {
    ElMessage.warning('演示系统暂不支持物理删除')
  } catch (err) {}
}

const openEditDialog = (user) => {
  editForm.value = { 
    id: user.user_id,
    user_no: user.user_no,
    username: user.username,
    role: user.role, // 使用整数角色码
    credit_score: user.credit_score,
    balance: user.balance || 0,
    is_active: user.is_active !== false
  }
  showEditDialog.value = true
}

const submitEdit = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      await updateUser({ 
        user_id: editForm.value.id,
        username: editForm.value.username,
        role: editForm.value.role,
        credit_score: editForm.value.credit_score,
        // 这里不再传递 balance，保护私人财产
        is_active: editForm.value.is_active
      })
      ElMessage.success('用户信息更新成功')
      showEditDialog.value = false
      fetchUsers()
    } finally {
      submitting.value = false
    }
  })
}

const openRechargeDialog = (user) => {
  selectedUser.value = user
  rechargeAmount.value = 100
  showRechargeDialog.value = true
}

const submitRecharge = async () => {
  submitting.value = true
  try {
    await updateUser({ 
      user_id: selectedUser.value.user_id, 
      balance: Number(selectedUser.value.balance) + Number(rechargeAmount.value)
    })
    ElMessage.success('资金充值成功')
    showRechargeDialog.value = false
    fetchUsers()
  } finally {
    submitting.value = false
  }
}

const init = async () => {
  await fetchUsers()
  try {
    const res = await getAdminConfig()
    if (res.success) {
      sysConfig.value = res.data
    }
  } catch (err) {
    console.error('获取系统配置失败')
  }
}

onMounted(init)
</script>

<style scoped>
.user-management {
  padding: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
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

.header-actions {
  display: flex;
  gap: 12px;
}

.search-input {
  width: 240px;
}

.credit-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.credit-num {
  font-size: 12px;
  font-weight: 700;
}
.credit-num.success { color: #10b981; }
.credit-num.warning { color: #f59e0b; }
.credit-num.danger { color: #ef4444; }

.balance-text {
  font-weight: 700;
  color: #10b981;
}

.op-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.user-tabs {
  margin-bottom: 24px;
}

.pagination-area {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.balance-text.highlight {
  font-weight: 700;
  color: #10b981;
}

.text-secondary {
  color: #94a3b8;
  font-size: 13px;
}

/* 信用分编辑布局优化 */
.credit-control-row {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-top: 5px;
}

.credit-input {
  width: 130px;
}

.credit-level-tag {
  flex: 1;
  justify-content: center;
  font-weight: 700;
  letter-spacing: 1px;
}

/* 余额只读样式 */
.balance-readonly {
  background: #f8fafc;
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 250px;
}

.currency {
  font-size: 14px;
  color: #64748b;
  font-weight: 600;
}

.amount {
  font-size: 18px;
  font-weight: 800;
  color: #1e293b;
}

/* 表单提示样式 */
.form-tip {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
  line-height: 1.5;
}

/* 对话框底部按钮样式 */
.dialog-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.mr-1 {
  margin-right: 4px;
}

/* 滑块标记样式 - 强制显示并调整文字 */
:deep(.el-slider__marks-text) {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  margin-top: 5px;
  white-space: nowrap;
}

:deep(.el-slider__button) {
  width: 16px;
  height: 16px;
  border: 2px solid #409eff;
  background-color: #fff;
}

:deep(.el-slider__bar) {
  background: linear-gradient(90deg, #f56c6c 0%, #e6a23c 70%, #67c23a 100%);
}

/* 滑块标记样式优化 */
:deep(.el-slider__marks-text) {
  font-size: 12px;
  color: #909399;
}

:deep(.el-slider__button) {
  width: 16px;
  height: 16px;
  border: 2px solid #409eff;
}

:deep(.el-slider__bar) {
  background: linear-gradient(90deg, #f56c6c 0%, #e6a23c 60%, #67c23a 100%);
}
</style>
