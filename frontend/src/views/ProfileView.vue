<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const API_BASE = 'http://127.0.0.1:5001/api'
const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

// 表单与数据
const carForm = ref({ plate: '' })
const savedPlates = ref([]) 

// 1. 初始化：获取用户信息和车牌
const fetchUserData = async () => {
    if(!user.value) return router.push('/login')
    try {
        const res = await axios.get(`${API_BASE}/auth/profile?user_id=${user.value.id}`)
        user.value.balance = res.data.data.balance
        user.value.credit = res.data.data.credit
        
        // 从后端获取车牌列表
        savedPlates.value = res.data.data.plates 
        
        // 更新本地缓存的用户基本信息
        localStorage.setItem('user', JSON.stringify(user.value))
    } catch (e) { console.error(e) }
}

onMounted(fetchUserData)

// 2. 充值
const handleRecharge = async () => {
    try {
        const { value } = await ElMessageBox.prompt('请输入充值金额', '钱包充值', { inputPattern: /^[0-9]+$/ })
        await axios.post(`${API_BASE}/auth/recharge`, { user_id: user.value.id, amount: value })
        ElMessage.success('充值成功')
        fetchUserData() // 刷新余额
    } catch (e) { if(e!=='cancel') ElMessage.error('充值失败') }
}

// 3. 添加车辆 (调用后端)
const addCar = async () => {
    if(!carForm.value.plate) return ElMessage.warning('请输入车牌')
    try {
        const res = await axios.post(`${API_BASE}/auth/plate/update`, {
            user_id: user.value.id,
            action: 'add',
            plate: carForm.value.plate
        })
        savedPlates.value = res.data.plates // 更新列表
        carForm.value.plate = ''
        ElMessage.success('添加成功')
    } catch (e) { ElMessage.error('添加失败，可能车牌已存在') }
}

// 4. 删除车辆 (调用后端)
const removeCar = async (plate) => {
    try {
        const res = await axios.post(`${API_BASE}/auth/plate/update`, {
            user_id: user.value.id,
            action: 'remove',
            plate: plate
        })
        savedPlates.value = res.data.plates // 更新列表
        ElMessage.success('已删除')
    } catch (e) { ElMessage.error('删除失败') }
}

const goBack = () => router.push('/dashboard')
</script>

<template>
  <div class="profile-container">
    <div class="header">
        <el-page-header @back="goBack">
            <template #content><span class="text-large font-600 mr-3"> 👤 个人中心 </span></template>
        </el-page-header>
    </div>
    <div class="content-wrapper">
        <el-row :gutter="20">
            <el-col :span="8">
                <el-card class="mb-20">
                    <template #header>我的名片</template>
                    <div class="avatar-section">
                        <el-avatar :size="80" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" />
                        <h3>{{ user?.real_name }}</h3>
                        <el-tag>{{ user?.role==='admin'?'管理员':'普通用户' }}</el-tag>
                    </div>
                    <div class="info">账号: {{ user?.username }}</div>
                    <div class="info">信用: <span :style="{color:user?.credit<80?'red':'green'}">{{ user?.credit }}</span></div>
                </el-card>
                <el-card>
                    <template #header>💰 钱包余额</template>
                    <div class="wallet">
                        <div class="balance">¥ {{ user?.balance }}</div>
                        <el-button type="primary" block @click="handleRecharge">立即充值</el-button>
                    </div>
                </el-card>
            </el-col>

            <el-col :span="16">
                <el-card>
                    <template #header>🚘 车辆管理 (云端同步)</template>
                    <div class="add-box">
                        <el-input v-model="carForm.plate" placeholder="输入车牌号" style="width:200px;margin-right:10px" />
                        <el-button type="success" @click="addCar">绑定新车</el-button>
                    </div>
                    <el-divider content-position="left">已绑定车辆</el-divider>
                    <div class="car-list">
                        <el-tag v-for="p in savedPlates" :key="p" closable @close="removeCar(p)" size="large" style="margin:5px">
                            🚗 {{ p }}
                        </el-tag>
                        <el-empty v-if="savedPlates.length===0" description="暂无车辆，请添加" image-size="60" />
                    </div>
                </el-card>
            </el-col>
        </el-row>
    </div>
  </div>
</template>

<style scoped>
.profile-container { padding: 20px; background: #f5f7fa; min-height: 100vh; }
.header { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; }
.mb-20 { margin-bottom: 20px; }
.avatar-section { text-align: center; margin-bottom: 20px; }
.wallet { text-align: center; }
.balance { font-size: 32px; font-weight: bold; color: #E6A23C; margin-bottom: 15px; }
</style>