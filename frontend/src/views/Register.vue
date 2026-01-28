  <template>
  <div class="register-container">
    <div class="register-box card">
      <h2 class="register-title">注册</h2>
      
      <el-form :model="registerForm" :rules="rules" ref="registerFormRef">
        <el-form-item prop="user_no">
          <el-input v-model="registerForm.user_no" placeholder="学号/工号" size="large" @keyup.enter="handleRegister" />
        </el-form-item>
        
        <el-form-item prop="username">
          <el-input v-model="registerForm.username" placeholder="真实姓名 (需与官方库一致)" size="large" @keyup.enter="handleRegister" />
        </el-form-item>
        
        <div class="identity-tip">
          <el-icon><InfoFilled /></el-icon>
          系统将自动验证您的校内身份并分配权限
        </div>
        
        <el-form-item prop="password">
          <el-input 
            v-model="registerForm.password" 
            type="password" 
            placeholder="设置登录密码" 
            size="large" 
            show-password 
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input 
            v-model="registerForm.confirmPassword" 
            type="password" 
            placeholder="确认登录密码" 
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
import { InfoFilled } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const registerFormRef = ref(null)
const loading = ref(false)

const registerForm = reactive({
  user_no: '',
  username: '',
  password: '',
  confirmPassword: ''
})

const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致!'))
  } else {
    callback()
  }
}

const rules = {
  user_no: [{ required: true, message: '请输入学号/工号', trigger: 'blur' }],
  username: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validatePass2, trigger: 'blur' }
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

.identity-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(102, 126, 234, 0.1);
  padding: 10px 14px;
  border-radius: 8px;
  color: #4c51bf;
  font-size: 13px;
  margin-bottom: 22px;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.identity-tip .el-icon {
  font-size: 16px;
}
</style>
