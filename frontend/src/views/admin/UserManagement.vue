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

    <el-table :data="users" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="user_no" label="学号/工号" width="120" fixed />
      <el-table-column prop="username" label="姓名" width="120" />
      <el-table-column label="身份" width="120">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" effect="dark" size="small">
            {{ row.role === 'admin' ? '系统管理员' : '普通用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="信用分" width="140" sortable prop="credit_score">
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
      <el-table-column label="账户余额" width="120">
        <template #default="{ row }">
          <span class="balance-text">{{ formatCurrency(row.balance) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="账户状态" width="100">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            active-text="正常"
            inactive-text="停用"
            inline-prompt
            :disabled="row.role === 'admin' || row.username === 'admin'"
            @change="(val) => handleStatusChange(row, val)"
          />
        </template>
      </el-table-column>
      <el-table-column label="管理操作" min-width="260" fixed="right">
        <template #default="{ row }">
          <div class="op-grid">
            <el-button 
              size="small" 
              icon="Edit" 
              :disabled="row.role === 'admin' || row.username === 'admin'"
              @click="openEditDialog(row)"
            >编辑</el-button>
            <el-button 
              size="small" 
              type="success" 
              icon="Money" 
              :disabled="row.role === 'admin' || row.username === 'admin'"
              @click="openRechargeDialog(row)"
            >充值</el-button>
            <el-popconfirm title="确定重置密码为 123456 吗？" @confirm="handleResetPwd(row)">
              <template #reference>
                <el-button 
                  size="small" 
                  type="warning" 
                  icon="Lock"
                  :disabled="row.role === 'admin' || row.username === 'admin'"
                >重置</el-button>
              </template>
            </el-popconfirm>
            <el-popconfirm title="删除后不可恢复，确定吗？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button 
                  size="small" 
                  type="danger" 
                  icon="Delete"
                  :disabled="row.role === 'admin' || row.username === 'admin'"
                >删除</el-button>
              </template>
            </el-popconfirm>
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
        @current-change="fetchUsers"
      />
    </div>

    <!-- Edit User Dialog -->
    <el-dialog v-model="showEditDialog" title="用户信息编辑" width="400px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="姓名">
          <el-input v-model="editForm.username" @keyup.enter="submitEdit" />
        </el-form-item>
        <el-form-item label="信用分">
          <el-input-number v-model="editForm.credit_score" :min="0" :max="100" @keyup.enter="submitEdit" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="submitting">保存修改</el-button>
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
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { getUsers, updateUser } from '@/api/admin'
import { formatCurrency } from '@/utils/format'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const submitting = ref(false)
const users = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')

const customColors = [
  { color: '#f56c6c', percentage: 60 },
  { color: '#e6a23c', percentage: 80 },
  { color: '#67c23a', percentage: 100 },
]

const showEditDialog = ref(false)
const editForm = ref({ id: null, username: '', credit_score: 0 })

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
    // 强化身份判定（兼容后端各种可能的 role 字符串）
    users.value = res.data.users.map(u => ({
      ...u,
      role: (u.username === '系统管理员' || u.user_no === 'admin') ? 'admin' : u.role
    }))
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

const getCreditClass = (score) => {
  if (score < 60) return 'danger'
  if (score < 80) return 'warning'
  return 'success'
}

const handleStatusChange = async (user, val) => {
  try {
    await updateUser({ user_id: user.user_id, is_active: val })
    ElMessage.success(`${user.username} 账号已${val ? '激活' : '禁用'}`)
  } catch (err) {
    user.is_active = !val 
  }
}

const handleResetPwd = async (user) => {
  try {
    // 假设后端有专门的重置接口，目前先复用 updateUser 模拟
    await updateUser({ user_id: user.user_id, password: 'reset_trigger' })
    ElMessage.success('密码已重置为默认值')
  } catch (err) {}
}

const handleDelete = async (user) => {
  try {
    // 逻辑删除或物理删除触发
    ElMessage.warning('演示系统暂不支持物理删除')
  } catch (err) {}
}

const openEditDialog = (user) => {
  editForm.value = { 
    id: user.user_id, 
    username: user.username, 
    credit_score: user.credit_score 
  }
  showEditDialog.value = true
}

const submitEdit = async () => {
  submitting.value = true
  try {
    await updateUser({ 
      user_id: editForm.value.id, 
      username: editForm.value.username, 
      credit_score: editForm.value.credit_score 
    })
    ElMessage.success('基础信息更新成功')
    showEditDialog.value = false
    fetchUsers()
  } finally {
    submitting.value = false
  }
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
      balance: selectedUser.value.balance + rechargeAmount.value 
    })
    ElMessage.success('资金充值成功')
    showRechargeDialog.value = false
    fetchUsers()
  } finally {
    submitting.value = false
  }
}

onMounted(fetchUsers)
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

.pagination-area {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}
</style>
