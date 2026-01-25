<template>
  <div class="admin-layout">
    <!-- Sidebar -->
    <div class="sidebar">
      <div class="logo">
        <el-icon><OfficeBuilding /></el-icon>
        <div class="logo-text">
          <p>Smart Campus</p>
          <p>Parking System</p>
        </div>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        background-color="#1e293b"
        text-color="#ffffff" 
        active-text-color="#60a5fa"
        @select="handleMenuSelect"
      >
        <el-menu-item index="/admin/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/parking">
          <el-icon><Location /></el-icon>
          <span>车位管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/orders">
          <el-icon><Document /></el-icon>
          <span>订单管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </div>
    
    <!-- Content Area -->
    <div class="main-container">
      <div class="admin-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>管理中心</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <span class="user-info">管理员</span>
          <el-button size="small" @click="handleLogout">退出</el-button>
        </div>
      </div>
      
      <div class="admin-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { 
  OfficeBuilding, DataAnalysis, User, Location, Document, Setting 
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

const currentPageTitle = computed(() => {
  const titles = {
    '/admin/dashboard': '仪表盘',
    '/admin/users': '用户管理',
    '/admin/parking': '车位管理',
    '/admin/orders': '订单管理'
  }
  return titles[route.path] || '管理中心'
})

const handleMenuSelect = (index) => {
  router.push(index)
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: #f8fafc;
}

.sidebar {
  width: 250px;
  background-color: #1e293b;
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.logo {
  height: 100px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 12px;
  color: white;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.logo-text p {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.2;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  padding-top: 10px;
}

:deep(.el-menu-item) {
  height: 54px;
  font-size: 15px !important;
  color: #ffffff !important; /* 强制白色高对比度 */
  opacity: 0.8;
}

:deep(.el-menu-item.is-active) {
  background-color: #2d3e50 !important;
  opacity: 1;
  color: #60a5fa !important;
}

:deep(.el-menu-item:hover) {
  background-color: rgba(255,255,255,0.05) !important;
  opacity: 1;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.admin-header {
  height: 64px;
  background-color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  border-bottom: 1px solid #e2e8f0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
}

.admin-content {
  flex: 1;
  overflow-y: auto;
  padding: 25px;
  background-color: #f1f5f9;
}
</style>
