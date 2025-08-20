<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="250px" class="sidebar">
      <div class="logo">
        <h2>康养监护系统</h2>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/events">
          <el-icon><Warning /></el-icon>
          <span>告警事件</span>
        </el-menu-item>
        <el-menu-item index="/cameras">
          <el-icon><VideoCamera /></el-icon>
          <span>摄像头管理</span>
        </el-menu-item>
        <el-menu-item index="/monitor">
          <el-icon><Monitor /></el-icon>
          <span>实时监控</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-content">
          <div class="breadcrumb">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item>康养监护</el-breadcrumb-item>
              <el-breadcrumb-item>{{ $route.meta.title }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-actions">
            <el-badge :value="unhandledCount" class="alert-badge">
              <el-button type="primary" :icon="Bell" @click="showAlerts">
                告警通知
              </el-button>
            </el-badge>
          </div>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import { defineComponent, ref, onMounted } from 'vue'
import { Bell, Odometer, Warning, VideoCamera, Monitor } from '@element-plus/icons-vue'
import { useEventStore } from '@/stores/event'

export default defineComponent({
  name: 'Layout',
  components: {
    Bell,
    Odometer,
    Warning,
    VideoCamera,
    Monitor
  },
  setup() {
    const eventStore = useEventStore()
    const unhandledCount = ref(0)

    const showAlerts = () => {
      // 跳转到事件页面
      router.push('/events')
    }

    onMounted(() => {
      // 获取未处理的告警数量
      eventStore.fetchStatistics().then(() => {
        unhandledCount.value = eventStore.statistics.pendingEvents || 0
      })
    })

    return {
      unhandledCount,
      showAlerts
    }
  }
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  border-right: 1px solid #e6e6e6;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #409EFF;
  color: white;
  margin-bottom: 20px;
}

.logo h2 {
  font-size: 18px;
  font-weight: bold;
}

.sidebar-menu {
  border: none;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.alert-badge {
  margin-right: 20px;
}

.main-content {
  background-color: #f5f5f5;
  padding: 20px;
  overflow-y: auto;
}
</style>