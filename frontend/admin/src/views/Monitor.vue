<template>
  <div class="ai-monitor-center">
    <!-- AI风格顶部控制栏 -->
    <div class="monitor-header">
      <div class="header-left">
        <h1 class="ai-title">
          <span class="ai-icon">🤖</span>
          康养跌倒检测监控中心
          <span class="subtitle">Fall Detection Monitoring Center</span>
        </h1>
        <div class="time-display">
          <span class="current-time">{{ currentTime }}</span>
          <span class="current-date">{{ currentDate }}</span>
        </div>
      </div>
      <div class="header-right">
        <div class="ai-status-indicators">
          <div class="status-item ai-active">
            <span class="status-dot"></span>
            <span>AI检测服务</span>
            <span class="status-label">运行中</span>
          </div>
          <div class="quick-controls">
            <button class="ai-btn primary" @click="refreshAll">
              <span class="btn-icon">🔄</span>
              刷新监控
            </button>
            <button class="ai-btn secondary" @click="toggleFullscreen">
              <span class="btn-icon">📺</span>
              全屏模式
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 实时统计面板 -->
    <div class="real-time-stats">
      <div class="stat-card danger">
        <div class="stat-icon">🚨</div>
        <div class="stat-content">
          <div class="stat-number">{{ statistics.todayAlerts }}</div>
          <div class="stat-label">今日告警</div>
          <div class="stat-trend up">↗️ +{{ statistics.alertIncrease }}%</div>
        </div>
      </div>
      <div class="stat-card warning">
        <div class="stat-icon">⏳</div>
        <div class="stat-content">
          <div class="stat-number">{{ statistics.pendingAlerts }}</div>
          <div class="stat-label">待处理</div>
          <div class="stat-trend down">↘️ -{{ statistics.pendingDecrease }}%</div>
        </div>
      </div>
      <div class="stat-card info">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-number">{{ statistics.totalAlerts }}</div>
          <div class="stat-label">总告警数</div>
          <div class="stat-trend">📈 累计</div>
        </div>
      </div>
      <div class="stat-card success">
        <div class="stat-icon">📹</div>
        <div class="stat-content">
          <div class="stat-number">{{ statistics.activeCameras }}</div>
          <div class="stat-label">活跃设备</div>
          <div class="stat-trend">✅ 正常</div>
        </div>
      </div>
    </div>

    <!-- 楼层监控面板 -->
    <div class="floor-monitoring">
      <div 
        v-for="floor in floors" 
        :key="floor.id"
        class="floor-section"
      >
        <div class="floor-header">
          <h3 class="floor-title">
            <span class="floor-icon">🏢</span>
            {{ floor.name }}
            <span class="floor-status" :class="floor.status">
              {{ getFloorStatus(floor) }}
            </span>
          </h3>
          <div class="floor-stats">
            <span class="camera-count">{{ floor.activeCameras }}/{{ floor.totalCameras }} 在线</span>
            <span class="alert-count" v-if="floor.activeAlerts > 0">
              {{ floor.activeAlerts }} 告警
            </span>
          </div>
        </div>
        
        <div class="camera-grid">
          <div 
            v-for="camera in floor.cameras" 
            :key="camera.id"
            class="camera-card"
            :class="getCameraClass(camera)"
            @click="selectCamera(camera)"
          >
            <div class="camera-header">
              <span class="camera-name">{{ camera.name }}</span>
              <span class="camera-status" :class="camera.status">
                <span class="status-dot"></span>
              </span>
            </div>
            
            <div class="camera-preview">
              <div class="video-placeholder" v-if="!camera.hasVideo">
                <span class="camera-icon">📹</span>
                <span class="camera-label">{{ camera.location }}</span>
              </div>
              <div class="live-indicator" v-if="camera.status === 'online'">
                <span class="live-dot"></span>
                LIVE
              </div>
            </div>
            
            <div class="camera-footer">
              <div class="camera-info">
                <span class="room-number">{{ camera.room }}</span>
                <span class="detection-status" :class="camera.detectionStatus">
                  {{ getDetectionLabel(camera.detectionStatus) }}
                </span>
              </div>
              <div class="camera-alerts" v-if="camera.alertCount > 0">
                <span class="alert-badge">{{ camera.alertCount }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧信息面板 -->
    <div class="info-panels">
      <!-- 实时告警面板 -->
      <div class="info-panel alert-panel">
        <div class="panel-header">
          <h4>🚨 实时告警</h4>
          <div class="auto-refresh" :class="{ active: autoRefresh }">
            <span class="refresh-dot"></span>
            自动刷新
          </div>
        </div>
        <div class="alert-list">
          <div 
            v-for="alert in recentAlerts" 
            :key="alert.id"
            class="alert-item"
            :class="alert.type"
          >
            <div class="alert-icon">
              <span v-if="alert.type === 'fall'">🤕</span>
              <span v-else-if="alert.type === 'fire'">🔥</span>
              <span v-else>💨</span>
            </div>
            <div class="alert-content">
              <div class="alert-title">{{ alert.title }}</div>
              <div class="alert-location">📍 {{ alert.location }}</div>
              <div class="alert-time">🕐 {{ formatTime(alert.time) }}</div>
            </div>
          </div>
          <div v-if="recentAlerts.length === 0" class="no-alerts">
            <span class="no-alert-icon">✅</span>
            <p>当前无告警事件</p>
          </div>
        </div>
      </div>

      <!-- 系统状态面板 -->
      <div class="info-panel system-panel">
        <div class="panel-header">
          <h4>⚙️ 系统状态</h4>
        </div>
        <div class="system-status">
          <div class="status-row">
            <span class="status-label">🤖 AI服务</span>
            <span class="status-value success">✅ 运行正常</span>
          </div>
          <div class="status-row">
            <span class="status-label">⚙️ 后端服务</span>
            <span class="status-value success">✅ 连接正常</span>
          </div>
          <div class="status-row">
            <span class="status-label">🗄️ 数据库</span>
            <span class="status-value success">✅ 运行正常</span>
          </div>
          <div class="status-row">
            <span class="status-label">📹 摄像头</span>
            <span class="status-value warning">⚠️ 2台离线</span>
          </div>
        </div>
      </div>

      <!-- 性能指标面板 -->
      <div class="info-panel performance-panel">
        <div class="panel-header">
          <h4>📊 性能指标</h4>
        </div>
        <div class="performance-metrics">
          <div class="metric-item">
            <span class="metric-label">检测准确率</span>
            <div class="metric-bar">
              <div class="metric-progress" style="width: 94.5%"></div>
            </div>
            <span class="metric-value">94.5%</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">响应时间</span>
            <div class="metric-bar">
              <div class="metric-progress" style="width: 85%"></div>
            </div>
            <span class="metric-value">0.25s</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">误报率</span>
            <div class="metric-bar error">
              <div class="metric-progress" style="width: 3.2%"></div>
            </div>
            <span class="metric-value">3.2%</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">系统负载</span>
            <div class="metric-bar">
              <div class="metric-progress" style="width: 42%"></div>
            </div>
            <span class="metric-value">42%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 快速操作面板 -->
    <div class="quick-actions">
      <button class="action-card" @click="exportReport">
        <span class="action-icon">📄</span>
        <span class="action-label">导出报告</span>
      </button>
      <button class="action-card" @click="systemSettings">
        <span class="action-icon">⚙️</span>
        <span class="action-label">系统设置</span>
      </button>
      <button class="action-card" @click="viewHistory">
        <span class="action-icon">📚</span>
        <span class="action-label">历史记录</span>
      </button>
      <button class="action-card" @click="helpCenter">
        <span class="action-icon">❓</span>
        <span class="action-label">帮助中心</span>
      </button>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, onUnmounted } from 'vue'
import dayjs from 'dayjs'

export default defineComponent({
  name: 'AIMonitorCenter',
  setup() {
    const currentTime = ref('')
    const currentDate = ref('')
    const autoRefresh = ref(true)
    const timeInterval = ref(null)
    
    // 统计数据
    const statistics = ref({
      todayAlerts: 17,
      alertIncrease: 12,
      pendingAlerts: 3,
      pendingDecrease: 8,
      totalAlerts: 186,
      activeCameras: 22
    })
    
    // 楼层数据 - 三层楼，每层8个房间
    const floors = ref([
      {
        id: 1,
        name: '一层楼',
        status: 'normal',
        activeCameras: 8,
        totalCameras: 8,
        activeAlerts: 1,
        cameras: [
          { id: 101, name: '摄像头-01', room: '101', location: '客厅', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 102, name: '摄像头-02', room: '102', location: '卧室', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 103, name: '摄像头-03', room: '103', location: '卫生间', status: 'offline', detectionStatus: 'offline', alertCount: 0, hasVideo: false },
          { id: 104, name: '摄像头-04', room: '104', location: '厨房', status: 'online', detectionStatus: 'alert', alertCount: 1, hasVideo: false },
          { id: 105, name: '摄像头-05', room: '105', location: '客厅', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 106, name: '摄像头-06', room: '106', location: '卧室', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 107, name: '摄像头-07', room: '107', location: '客厅', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 108, name: '摄像头-08', room: '108', location: '卧室', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false }
        ]
      },
      {
        id: 2,
        name: '二层楼',
        status: 'normal',
        activeCameras: 7,
        totalCameras: 8,
        activeAlerts: 0,
        cameras: [
          { id: 201, name: '摄像头-09', room: '201', location: '客厅', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 202, name: '摄像头-10', room: '202', location: '卧室', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 203, name: '摄像头-11', room: '203', location: '卫生间', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 204, name: '摄像头-12', room: '204', location: '厨房', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 205, name: '摄像头-13', room: '205', location: '客厅', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 206, name: '摄像头-14', room: '206', location: '卧室', status: 'offline', detectionStatus: 'offline', alertCount: 0, hasVideo: false },
          { id: 207, name: '摄像头-15', room: '207', location: '客厅', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 208, name: '摄像头-16', room: '208', location: '卧室', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false }
        ]
      },
      {
        id: 3,
        name: '三层楼',
        status: 'normal',
        activeCameras: 7,
        totalCameras: 8,
        activeAlerts: 2,
        cameras: [
          { id: 301, name: '摄像头-17', room: '301', location: '客厅', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 302, name: '摄像头-18', room: '302', location: '卧室', status: 'online', detectionStatus: 'alert', alertCount: 1, hasVideo: false },
          { id: 303, name: '摄像头-19', room: '303', location: '卫生间', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 304, name: '摄像头-20', room: '304', location: '厨房', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 305, name: '摄像头-21', room: '305', location: '客厅', status: 'online', detectionStatus: 'alert', alertCount: 1, hasVideo: false },
          { id: 306, name: '摄像头-22', room: '306', location: '卧室', status: 'offline', detectionStatus: 'offline', alertCount: 0, hasVideo: false },
          { id: 307, name: '摄像头-23', room: '307', location: '客厅', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false },
          { id: 308, name: '摄像头-24', room: '308', location: '卧室', status: 'online', detectionStatus: 'normal', alertCount: 0, hasVideo: false }
        ]
      }
    ])
    
    // 最新告警
    const recentAlerts = ref([
      {
        id: 1,
        type: 'fall',
        title: '跌倒告警',
        location: '301房间',
        time: new Date().toISOString()
      },
      {
        id: 2,
        type: 'fire',
        title: '火焰告警',
        location: '104厨房区域',
        time: new Date(Date.now() - 300000).toISOString()
      },
      {
        id: 3,
        type: 'fall',
        title: '跌倒告警',
        location: '305房间',
        time: new Date(Date.now() - 600000).toISOString()
      }
    ])
    
    const updateTime = () => {
      const now = dayjs()
      currentTime.value = now.format('HH:mm:ss')
      currentDate.value = now.format('YYYY年MM月DD日 dddd')
    }
    
    const getCameraClass = (camera) => {
      const classes = []
      if (camera.status === 'offline') classes.push('offline')
      if (camera.detectionStatus === 'alert') classes.push('alert')
      if (camera.alertCount > 0) classes.push('has-alerts')
      return classes.join(' ')
    }
    
    const getFloorStatus = (floor) => {
      if (floor.activeAlerts > 0) return '⚠️ 有告警'
      if (floor.activeCameras < floor.totalCameras) return '⚠️ 设备离线'
      return '✅ 正常运行'
    }
    
    const getDetectionLabel = (status) => {
      switch (status) {
        case 'normal': return '正常检测'
        case 'alert': return '检测告警'
        case 'offline': return '离线'
        default: return '未知状态'
      }
    }
    
    const formatTime = (time) => {
      return dayjs(time).format('HH:mm:ss')
    }
    
    const selectCamera = (camera) => {
      console.log('选择摄像头:', camera)
    }
    
    const refreshAll = () => {
      console.log('刷新所有监控')
    }
    
    const toggleFullscreen = () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen()
      } else {
        document.exitFullscreen()
      }
    }
    
    const exportReport = () => {
      console.log('导出报告')
    }
    
    const systemSettings = () => {
      console.log('系统设置')
    }
    
    const viewHistory = () => {
      console.log('查看历史')
    }
    
    const helpCenter = () => {
      console.log('帮助中心')
    }
    
    onMounted(() => {
      updateTime()
      timeInterval.value = setInterval(updateTime, 1000)
    })
    
    onUnmounted(() => {
      if (timeInterval.value) {
        clearInterval(timeInterval.value)
      }
    })
    
    return {
      currentTime,
      currentDate,
      autoRefresh,
      statistics,
      floors,
      recentAlerts,
      getCameraClass,
      getFloorStatus,
      getDetectionLabel,
      formatTime,
      selectCamera,
      refreshAll,
      toggleFullscreen,
      exportReport,
      systemSettings,
      viewHistory,
      helpCenter
    }
  }
})
</script>

<style scoped>
.ai-monitor-center {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  color: white;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  position: relative;
  overflow-x: hidden;
}

/* AI风格顶部控制栏 */
.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px 30px;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(59, 130, 246, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.ai-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 15px;
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #1d4ed8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.ai-icon {
  font-size: 2rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.subtitle {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 400;
  margin-left: 10px;
}

.time-display {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-top: 10px;
}

.current-time {
  font-size: 24px;
  font-weight: 700;
  color: #60a5fa;
  font-family: 'Courier New', monospace;
}

.current-date {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

.ai-status-indicators {
  display: flex;
  align-items: center;
  gap: 20px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 12px;
  font-size: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  animation: blink 2s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
}

.status-label {
  color: #10b981;
  font-weight: 500;
}

.quick-controls {
  display: flex;
  gap: 10px;
}

.ai-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.ai-btn.primary {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
}

.ai-btn.secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.ai-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
}

/* 实时统计面板 */
.real-time-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 25px;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(59, 130, 246, 0.2);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.stat-card.danger::before {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.stat-card.warning::before {
  background: linear-gradient(90deg, #f59e0b, #d97706);
}

.stat-card.info::before {
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
}

.stat-card.success::before {
  background: linear-gradient(90deg, #10b981, #059669);
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.stat-icon {
  font-size: 2.5rem;
  opacity: 0.8;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 700;
  color: white;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #94a3b8;
  margin-bottom: 5px;
}

.stat-trend {
  font-size: 12px;
  font-weight: 500;
}

.stat-trend.up {
  color: #10b981;
}

.stat-trend.down {
  color: #ef4444;
}

/* 楼层监控面板 */
.floor-monitoring {
  display: flex;
  flex-direction: column;
  gap: 30px;
  margin-bottom: 30px;
}

.floor-section {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(59, 130, 246, 0.2);
  padding: 25px;
  transition: all 0.3s ease;
}

.floor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.floor-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.floor-icon {
  font-size: 1.5rem;
}

.floor-status {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  margin-left: 15px;
}

.floor-stats {
  display: flex;
  gap: 15px;
  font-size: 14px;
  color: #94a3b8;
}

.camera-count {
  color: #10b981;
}

.alert-count {
  color: #ef4444;
  font-weight: 500;
}

.camera-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.camera-card {
  background: rgba(30, 41, 59, 0.8);
  border-radius: 16px;
  border: 1px solid rgba(59, 130, 246, 0.2);
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.camera-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
  border-color: rgba(59, 130, 246, 0.5);
}

.camera-card.offline {
  opacity: 0.6;
  border-color: rgba(100, 116, 139, 0.3);
}

.camera-card.alert {
  border-color: rgba(239, 68, 68, 0.5);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
}

.camera-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.camera-name {
  font-size: 14px;
  font-weight: 500;
  color: white;
}

.camera-status.online .status-dot {
  background: #10b981;
  box-shadow: 0 0 10px #10b981;
}

.camera-status.offline .status-dot {
  background: #64748b;
}

.camera-preview {
  height: 120px;
  background: #1e293b;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
  position: relative;
  border: 2px dashed rgba(59, 130, 246, 0.3);
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #64748b;
}

.camera-icon {
  font-size: 2rem;
}

.camera-label {
  font-size: 12px;
}

.live-indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(239, 68, 68, 0.9);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
}

.live-dot {
  width: 6px;
  height: 6px;
  background: white;
  border-radius: 50%;
  animation: blink 1s infinite;
}

.camera-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.room-number {
  font-size: 16px;
  font-weight: 600;
  color: #60a5fa;
}

.detection-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-top: 4px;
}

.detection-status.normal {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.detection-status.alert {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.detection-status.offline {
  background: rgba(100, 116, 139, 0.2);
  color: #64748b;
}

.alert-badge {
  background: #ef4444;
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 600;
}

/* 右侧信息面板 */
.info-panels {
  position: fixed;
  right: 20px;
  top: 120px;
  width: 350px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  z-index: 100;
}

.info-panel {
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(59, 130, 246, 0.2);
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.panel-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.auto-refresh {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #64748b;
}

.auto-refresh.active {
  color: #10b981;
}

.refresh-dot {
  width: 6px;
  height: 6px;
  background: #10b981;
  border-radius: 50%;
  animation: blink 2s infinite;
}

.alert-list {
  max-height: 300px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 10px;
  background: rgba(30, 41, 59, 0.5);
  border-left: 3px solid;
}

.alert-item.fall {
  border-left-color: #ef4444;
}

.alert-item.fire {
  border-left-color: #f97316;
}

.alert-item.smoke {
  border-left-color: #6b7280;
}

.alert-icon {
  font-size: 1.2rem;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 13px;
  font-weight: 600;
  color: white;
  margin-bottom: 4px;
}

.alert-location, .alert-time {
  font-size: 11px;
  color: #94a3b8;
  margin-bottom: 2px;
}

.no-alerts {
  text-align: center;
  padding: 20px;
  color: #64748b;
}

.no-alert-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 8px;
}

.system-status {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.status-label {
  font-size: 13px;
  color: #cbd5e1;
}

.status-value {
  font-size: 12px;
  font-weight: 500;
}

.status-value.success {
  color: #10b981;
}

.status-value.warning {
  color: #f59e0b;
}

.performance-metrics {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.metric-label {
  font-size: 12px;
  color: #cbd5e1;
}

.metric-bar {
  height: 6px;
  background: rgba(100, 116, 139, 0.3);
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}

.metric-progress {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #059669);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.metric-bar.error .metric-progress {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.metric-value {
  font-size: 11px;
  color: #60a5fa;
  font-weight: 600;
}

/* 快速操作面板 */
.quick-actions {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 15px;
  z-index: 100;
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 15px 20px;
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
  text-decoration: none;
}

.action-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
  border-color: rgba(59, 130, 246, 0.5);
}

.action-icon {
  font-size: 1.5rem;
}

.action-label {
  font-size: 12px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .camera-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .info-panels {
    position: relative;
    right: auto;
    top: auto;
    width: 100%;
    margin-top: 30px;
  }
}

@media (max-width: 1024px) {
  .real-time-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .camera-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .quick-actions {
    position: relative;
    bottom: auto;
    left: auto;
    transform: none;
    margin-top: 30px;
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .monitor-header {
    flex-direction: column;
    gap: 20px;
    align-items: stretch;
  }
  
  .real-time-stats {
    grid-template-columns: 1fr;
  }
  
  .camera-grid {
    grid-template-columns: 1fr;
  }
  
  .quick-actions {
    flex-wrap: wrap;
  }
  
  .ai-title {
    font-size: 20px;
  }
  
  .info-panels {
    gap: 15px;
  }
}
</style>