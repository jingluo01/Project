<template>
  <div class="login-container">
    <div class="login-left">
      <div class="login-illustration">
        <h1 class="slogan">智停校园，畅行无阻</h1>
        <p class="sub-slogan">Smart Campus Parking System</p>
      </div>
    </div>
    
    <div class="login-right">
      <div class="login-box">
        <h2 class="login-title">登录</h2>
        
        <el-form :model="loginForm" :rules="rules" ref="loginFormRef" @submit.prevent="handleLogin">
          <el-form-item prop="user_no">
            <el-input
              v-model="loginForm.user_no"
              placeholder="学号/工号"
              size="large"
              clearable
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              size="large"
              show-password
              @keyup.enter="handleLogin"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form>
        
        <div class="login-footer">
          <router-link to="/register" class="link">访客入口</router-link>
          <router-link to="/register" class="link">忘记密码</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  user_no: '',
  password: ''
})

const rules = {
  user_no: [{ required: true, message: '请输入学号/工号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await userStore.login(loginForm)
      ElMessage.success('登录成功')
      
      // Redirect based on role
      if (userStore.isAdmin) {
        router.push('/admin/dashboard')
      } else {
        router.push('/parking')
      }
    } catch (error) {
      console.error('Login failed:', error)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-left {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600"><rect fill="%234a5568" width="800" height="600"/><g fill="%23ffffff" opacity="0.1"><circle cx="200" cy="150" r="80"/><circle cx="600" cy="400" r="120"/><rect x="100" y="350" width="200" height="150" rx="10"/><rect x="500" y="100" width="150" height="200" rx="10"/></g></svg>') center/cover;
}

.login-illustration {
  text-align: center;
  color: white;
}

.slogan {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 20px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.sub-slogan {
  font-size: 20px;
  opacity: 0.9;
}

.login-right {
  width: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  box-shadow: -10px 0 30px rgba(0,0,0,0.1);
}

.login-box {
  width: 100%;
  max-width: 360px;
  padding: 40px;
}

.login-title {
  font-size: 32px;
  font-weight: 600;
  margin-bottom: 40px;
  color: #1f2937;
}

.login-btn {
  width: 100%;
  margin-top: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-size: 16px;
  height: 48px;
}

.login-btn:hover {
  opacity: 0.9;
}

.login-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 24px;
}

.link {
  color: #667eea;
  text-decoration: none;
  font-size: 14px;
}

.link:hover {
  text-decoration: underline;
}

:deep(.el-input__wrapper) {
  padding: 12px 16px;
}
</style>
