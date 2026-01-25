<template>
  <div class="register-container">
    <div class="register-box card">
      <h2 class="register-title">注册</h2>
      
      <el-form :model="registerForm" :rules="rules" ref="registerFormRef">
        <el-form-item prop="user_no">
          <el-input v-model="registerForm.user_no" placeholder="学号/工号" size="large" @keyup.enter="handleRegister" />
        </el-form-item>
        
        <el-form-item prop="username">
          <el-input v-model="registerForm.username" placeholder="姓名" size="large" @keyup.enter="handleRegister" />
        </el-form-item>
        
        <el-form-item prop="role">
          <el-select v-model="registerForm.role" placeholder="选择身份" size="large" style="width: 100%">
            <el-option label="学生" :value="1" />
            <el-option label="教职工" :value="2" />
          </el-select>
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="registerForm.password" 
            type="password" 
            placeholder="密码" 
            size="large" 
            show-password 
            @keyup.enter="handleRegister"
          />
        </el-form-item>
        
        <el-button type="primary" size="large" class="register-btn" :loading="loading" @click="handleRegister">
          注册
        </el-button>
      </el-form>
      
      <div class="register-footer">
        <router-link to="/login" class="link">已有账号？去登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const registerFormRef = ref(null)
const loading = ref(false)

const registerForm = reactive({
  user_no: '',
  username: '',
  role: 1,
  password: ''
})

const rules = {
  user_no: [{ required: true, message: '请输入学号/工号', trigger: 'blur' }],
  username: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择身份', trigger: 'change' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await userStore.register(registerForm)
      ElMessage.success('注册成功')
      router.push('/parking')
    } catch (error) {
      console.error('Register failed:', error)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-box {
  width: 100%;
  max-width: 420px;
  padding: 40px;
}

.register-title {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 32px;
  text-align: center;
}

.register-btn {
  width: 100%;
  margin-top: 20px;
}

.register-footer {
  text-align: center;
  margin-top: 20px;
}

.link {
  color: #667eea;
  text-decoration: none;
}
</style>
