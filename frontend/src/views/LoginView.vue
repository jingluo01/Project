<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const form = ref({ username: '', password: '' })
const loading = ref(false)

const handleLogin = async () => {
  if(!form.value.username || !form.value.password) return ElMessage.warning('请输入账号密码')
  
  loading.value = true
  try {
    const res = await axios.post('http://127.0.0.1:5001/api/auth/login', form.value)
    
    // 1. 保存用户信息
    const userInfo = res.data.data
    localStorage.setItem('user', JSON.stringify(userInfo))
    
    ElMessage.success(`欢迎回来，${userInfo.real_name}`)
    
    // 2. 关键逻辑：根据角色跳转不同页面
    if (userInfo.role === 'admin') {
        router.push('/admin') // 管理员 -> 去大屏
    } else {
        router.push('/dashboard') // 学生 -> 去预约
    }
    
  } catch (err) {
    ElMessage.error(err.response?.data?.msg || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrapper">
    <div class="poster-section">
        <div class="poster-content">
            <h1>Smart Parking</h1>
            <p>基于Web的校园智能停车管理系统</p>
            <ul>
                <li>⚡️ 实时车位监控</li>
                <li>🛡️ 信用分智能管控</li>
                <li>📊 数据可视化大屏</li>
            </ul>
        </div>
    </div>
    
    <div class="form-section">
        <div class="form-box">
            <h2>账号登录</h2>
            <p class="subtitle">Welcome Back</p>
            
            <el-form label-position="top" size="large">
                <el-form-item label="账号">
                    <el-input v-model="form.username" placeholder="请输入学号/工号" prefix-icon="User" />
                </el-form-item>
                <el-form-item label="密码">
                    <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password @keyup.enter="handleLogin"/>
                </el-form-item>
                <el-button type="primary" class="login-btn" :loading="loading" @click="handleLogin">
                    立即登录
                </el-button>
            </el-form>
            
            <div class="tips">
                <p>测试账号：</p>
                <p>学生：student1 / 123456</p>
                <p>管理员：admin / admin123</p>
            </div>
        </div>
    </div>
  </div>
</template>

<style scoped>
.login-wrapper { display: flex; height: 100vh; width: 100vw; overflow: hidden; }

/* 左侧样式 */
.poster-section { flex: 1; background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%); display: flex; align-items: center; justify-content: center; color: white; position: relative; }
.poster-content h1 { font-size: 48px; margin-bottom: 20px; }
.poster-content ul { list-style: none; padding: 0; font-size: 18px; line-height: 2; opacity: 0.9; }

/* 右侧样式 */
.form-section { flex: 1; display: flex; align-items: center; justify-content: center; background: white; }
.form-box { width: 400px; padding: 40px; }
.form-box h2 { font-size: 32px; margin-bottom: 10px; color: #333; }
.subtitle { color: #999; margin-bottom: 40px; }
.login-btn { width: 100%; height: 50px; font-size: 18px; margin-top: 20px; }
.tips { margin-top: 30px; background: #f5f7fa; padding: 15px; border-radius: 8px; font-size: 13px; color: #666; }
.tips p { margin: 5px 0; }
</style>