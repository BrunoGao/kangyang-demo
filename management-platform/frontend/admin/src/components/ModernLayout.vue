<template>
  <div class="modern-layout">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="logo-section">
        <div class="logo-icon">🏥</div>
        <div class="logo-text" v-if="!sidebarCollapsed">
          <h2>康养智控</h2>
          <p>AI Detection System</p>
        </div>
      </div>
      
      <nav class="sidebar-nav">
        <router-link 
          v-for="item in menuItems" 
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
        >
          <div class="nav-icon">{{ item.icon }}</div>
          <span class="nav-text" v-if="!sidebarCollapsed">{{ item.title }}</span>
          <div class="nav-indicator" v-if="$route.path === item.path"></div>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-profile" v-if="!sidebarCollapsed">
          <div class="user-avatar">👤</div>
          <div class="user-info">
            <div class="user-name">管理员</div>
            <div class="user-status">在线</div>
          </div>
        </div>
        <button class="collapse-btn" @click="toggleSidebar">
          {{ sidebarCollapsed ? '→' : '←' }}
        </button>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-wrapper">
      <!-- 顶部导航栏 -->
      <header class="top-header">
        <div class="header-left">
          <div class="breadcrumb">
            <span class="breadcrumb-item">🏠 康养监控</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-current">{{ currentPageTitle }}</span>
          </div>
        </div>
        
        <div class="header-right">
          <div class="header-stats">
            <div class="stat-item">
              <span class="stat-icon">🚨</span>
              <span class="stat-text">{{ unhandledCount }} 待处理</span>
            </div>
            <div class="stat-item">
              <span class="stat-icon">📹</span>
              <span class="stat-text">1 设备在线</span>
            </div>
          </div>
          
          <div class="header-actions">
            <button class="action-btn" @click="openVideoTest" title="视频测试">
              🎬
            </button>
            <button class="action-btn notification-btn" @click="showNotifications" title="通知">
              🔔
              <span class="notification-badge" v-if="unhandledCount > 0">{{ unhandledCount }}</span>
            </button>
            <button class="action-btn" @click="toggleFullscreen" title="全屏">
              📺
            </button>
            <div class="user-menu">
              <button class="user-btn">
                <span class="user-avatar-small">👤</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="page-content">
        <router-view />
      </main>
    </div>

    <!-- 通知面板 -->
    <div class="notification-panel" v-if="showNotificationPanel" @click.self="closeNotifications">
      <div class="notification-content">
        <div class="notification-header">
          <h3>📢 系统通知</h3>
          <button class="close-btn" @click="closeNotifications">✕</button>
        </div>
        <div class="notification-list">
          <div 
            v-for="notification in notifications" 
            :key="notification.id"
            class="notification-item"
            :class="notification.type"
          >
            <div class="notification-icon">
              <span v-if="notification.type === 'fall'">🤕</span>
              <span v-else-if="notification.type === 'fire'">🔥</span>
              <span v-else>💨</span>
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-desc">{{ notification.description }}</div>
              <div class="notification-time">{{ formatTime(notification.time) }}</div>
            </div>
          </div>
          <div v-if="notifications.length === 0" class="no-notifications">
            <span class="no-data-icon">✅</span>
            <p>暂无新通知</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'

export default defineComponent({
  name: 'ModernLayout',
  setup() {
    const route = useRoute()
    const router = useRouter()
    
    const sidebarCollapsed = ref(false)
    const showNotificationPanel = ref(false)
    const unhandledCount = ref(3)
    
    const menuItems = [
      { path: '/dashboard', title: '监控中心', icon: '📊' },
      { path: '/events', title: '告警事件', icon: '🚨' },
      { path: '/cameras', title: '设备管理', icon: '📹' },
      { path: '/edge-devices', title: '边缘设备', icon: '🖥️' },
      { path: '/video-test', title: '视频测试', icon: '🎬' },
      { path: '/monitor', title: '实时监控', icon: '🎯' }
    ]
    
    const notifications = ref([
      {
        id: 1,
        type: 'fall',
        title: '跌倒告警',
        description: '201房间检测到跌倒事件',
        time: new Date().toISOString()
      },
      {
        id: 2,
        type: 'fire',
        title: '火焰告警',
        description: '厨房区域检测到火焰',
        time: new Date(Date.now() - 300000).toISOString()
      },
      {
        id: 3,
        type: 'smoke',
        title: '烟雾告警',
        description: '休息区检测到烟雾',
        time: new Date(Date.now() - 600000).toISOString()
      }
    ])
    
    const currentPageTitle = computed(() => {
      const currentMenu = menuItems.find(item => item.path === route.path)
      return currentMenu ? currentMenu.title : '未知页面'
    })
    
    const toggleSidebar = () => {
      sidebarCollapsed.value = !sidebarCollapsed.value
    }
    
    const showNotifications = () => {
      showNotificationPanel.value = true
    }
    
    const closeNotifications = () => {
      showNotificationPanel.value = false
    }
    
    const openVideoTest = () => {
      window.open('http://localhost:5557', '_blank')
    }
    
    const toggleFullscreen = () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen()
      } else {
        document.exitFullscreen()
      }
    }
    
    const formatTime = (time) => {
      return dayjs(time).format('HH:mm:ss')
    }
    
    return {
      sidebarCollapsed,
      showNotificationPanel,
      unhandledCount,
      menuItems,
      notifications,
      currentPageTitle,
      toggleSidebar,
      showNotifications,
      closeNotifications,
      openVideoTest,
      toggleFullscreen,
      formatTime
    }
  }
})
</script>

<style scoped>
.modern-layout {
  display: flex;
  height: 100vh;
  background: #f8fafc;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

/* 侧边栏 */
.sidebar {
  width: 280px;
  background: linear-gradient(180deg, #1e293b 0%, #334155 100%);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 100;
}

.sidebar.collapsed {
  width: 80px;
}

.logo-section {
  display: flex;
  align-items: center;
  padding: 25px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-icon {
  font-size: 2.5rem;
  margin-right: 15px;
}

.logo-text h2 {
  font-size: 20px;
  font-weight: 700;
  color: white;
  margin: 0;
}

.logo-text p {
  font-size: 12px;
  color: #94a3b8;
  margin: 2px 0 0 0;
}

.sidebar-nav {
  flex: 1;
  padding: 20px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  color: #cbd5e1;
  text-decoration: none;
  transition: all 0.3s ease;
  position: relative;
  margin: 2px 10px;
  border-radius: 12px;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  transform: translateX(5px);
}

.nav-item.active {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
}

.nav-icon {
  font-size: 1.5rem;
  margin-right: 15px;
  min-width: 24px;
}

.nav-text {
  font-size: 14px;
  font-weight: 500;
}

.nav-indicator {
  position: absolute;
  right: 10px;
  width: 6px;
  height: 6px;
  background: #60a5fa;
  border-radius: 50%;
  box-shadow: 0 0 10px #60a5fa;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-profile {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.user-avatar {
  font-size: 1.8rem;
  margin-right: 12px;
}

.user-name {
  color: white;
  font-size: 14px;
  font-weight: 500;
}

.user-status {
  color: #94a3b8;
  font-size: 12px;
}

.collapse-btn {
  width: 100%;
  padding: 10px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 主内容区域 */
.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-header {
  height: 70px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.breadcrumb-item {
  color: #64748b;
}

.breadcrumb-separator {
  color: #cbd5e1;
}

.breadcrumb-current {
  color: #1e293b;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-stats {
  display: flex;
  gap: 15px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #f1f5f9;
  border-radius: 20px;
  font-size: 12px;
  color: #475569;
}

.stat-icon {
  font-size: 14px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.action-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 12px;
  background: #f8fafc;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 16px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background: #e2e8f0;
  transform: translateY(-2px);
}

.notification-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: #ef4444;
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
}

.user-menu {
  margin-left: 10px;
}

.user-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
}

.user-avatar-small {
  color: white;
  font-size: 18px;
}

.page-content {
  flex: 1;
  overflow-y: auto;
  background: transparent;
  padding: 0;
}

/* 通知面板 */
.notification-panel {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(5px);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
  align-items: flex-start;
  padding: 20px;
}

.notification-content {
  width: 400px;
  max-height: 80vh;
  background: white;
  border-radius: 20px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 25px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.notification-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.close-btn {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 50%;
  background: #f1f5f9;
  cursor: pointer;
  font-size: 14px;
  color: #64748b;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: #e2e8f0;
}

.notification-list {
  max-height: 400px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  padding: 20px 25px;
  border-bottom: 1px solid #f1f5f9;
  transition: all 0.3s ease;
}

.notification-item:hover {
  background: #f8fafc;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item.fall {
  border-left: 4px solid #ef4444;
}

.notification-item.fire {
  border-left: 4px solid #f97316;
}

.notification-item.smoke {
  border-left: 4px solid #6b7280;
}

.notification-icon {
  font-size: 1.5rem;
  margin-right: 15px;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.notification-desc {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 6px;
}

.notification-time {
  font-size: 11px;
  color: #94a3b8;
}

.no-notifications {
  text-align: center;
  padding: 40px 20px;
  color: #94a3b8;
}

.no-data-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    height: 100vh;
    z-index: 200;
    transform: translateX(-100%);
  }
  
  .sidebar.collapsed {
    transform: translateX(0);
    width: 80px;
  }
  
  .main-wrapper {
    width: 100%;
  }
  
  .header-stats {
    display: none;
  }
  
  .notification-panel {
    padding: 10px;
  }
  
  .notification-content {
    width: 100%;
    max-width: 400px;
  }
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>