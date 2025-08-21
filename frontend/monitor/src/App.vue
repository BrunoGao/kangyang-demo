<template>
  <div class="monitor-screen">
    <!-- 标题栏 -->
    <div class="header">
      <div class="title">
        <h1>康养跌倒检测监控中心</h1>
        <div class="subtitle">Fall Detection Monitoring Center</div>
      </div>
      <div class="datetime">
        <div class="time">{{ currentTime }}</div>
        <div class="date">{{ currentDate }}</div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧区域 -->
      <div class="left-panel">
        <!-- 实时统计 -->
        <div class="panel stats-panel">
          <div class="panel-title">实时统计</div>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-icon today">
                <el-icon size="30"><Warning /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ statistics.todayEvents || 0 }}</div>
                <div class="stat-label">今日告警</div>
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-icon pending">
                <el-icon size="30"><Clock /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ statistics.pendingEvents || 0 }}</div>
                <div class="stat-label">待处理</div>
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-icon total">
                <el-icon size="30"><DataAnalysis /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ statistics.totalEvents || 0 }}</div>
                <div class="stat-label">总告警</div>
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-icon cameras">
                <el-icon size="30"><VideoCamera /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ activeCameras }}</div>
                <div class="stat-label">在线摄像头</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 告警趋势图 -->
        <div class="panel chart-panel">
          <div class="panel-title">告警趋势</div>
          <div ref="trendChart" class="chart"></div>
        </div>

        <!-- 电子围栏状态 -->
        <div class="panel fence-panel">
          <div class="panel-title">电子围栏</div>
          <div class="fence-status">
            <div class="fence-item" v-for="fence in electronicFences" :key="fence.id">
              <div class="fence-info">
                <div class="fence-name">{{ fence.name }}</div>
                <div class="fence-area">{{ fence.area }}</div>
              </div>
              <div class="fence-indicator" :class="fence.status">
                <el-icon><Lock v-if="fence.status === 'active'" /><Warning v-else /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间区域 -->
      <div class="center-panel">
        <!-- 视频监控 -->
        <div class="panel video-panel">
          <div class="panel-title">实时监控</div>
          <div class="video-grid">
            <div class="video-item" v-for="camera in cameras" :key="camera.id">
              <div class="video-container">
                <div class="video-placeholder">
                  <el-icon size="60"><VideoCamera /></el-icon>
                  <div class="camera-info">
                    <div class="camera-name">{{ camera.name }}</div>
                    <div class="camera-location">{{ camera.location }}</div>
                    <div class="camera-status" :class="camera.status">
                      <el-icon><CircleCheck v-if="camera.status === 'online'" /><Warning v-else /></el-icon>
                      {{ camera.status === 'online' ? '在线' : '离线' }}
                    </div>
                  </div>
                </div>
                <!-- 电子围栏覆盖层 -->
                <div class="fence-overlay" v-if="camera.hasFence">
                  <svg class="fence-svg" viewBox="0 0 100 100">
                    <polygon 
                      :points="camera.fencePoints" 
                      fill="rgba(0, 212, 255, 0.1)" 
                      stroke="#00d4ff" 
                      stroke-width="0.5"
                      stroke-dasharray="2,2"
                    />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 运动轨迹图 -->
        <div class="panel trajectory-panel">
          <div class="panel-title">运动轨迹</div>
          <div ref="trajectoryChart" class="chart"></div>
        </div>
      </div>

      <!-- 右侧区域 -->
      <div class="right-panel">
        <!-- 实时告警 -->
        <div class="panel alerts-panel">
          <div class="panel-title">
            实时告警
            <div class="alert-indicator" :class="{ 'active': hasNewAlert }">
              <el-icon><Bell /></el-icon>
            </div>
          </div>
          <div class="alerts-list">
            <div 
              v-for="alert in recentAlerts" 
              :key="alert.id" 
              class="alert-item"
              :class="alert.severity"
            >
              <div class="alert-time">{{ formatTime(alert.createdTime) }}</div>
              <div class="alert-content">
                <div class="alert-title">{{ getEventTypeText(alert.eventType) }}</div>
                <div class="alert-location">{{ alert.location }}</div>
                <div class="alert-severity">{{ getSeverityText(alert.severity) }}</div>
              </div>
              <div class="alert-status" :class="{ 'handled': alert.isHandled }">
                {{ alert.isHandled ? '已处理' : '待处理' }}
              </div>
            </div>
          </div>
        </div>

        <!-- 系统状态 -->
        <div class="panel system-panel">
          <div class="panel-title">系统状态</div>
          <div class="system-status">
            <div class="status-item">
              <div class="status-label">AI检测服务</div>
              <div class="status-value online">正常</div>
            </div>
            <div class="status-item">
              <div class="status-label">数据库连接</div>
              <div class="status-value online">正常</div>
            </div>
            <div class="status-item">
              <div class="status-label">消息队列</div>
              <div class="status-value online">正常</div>
            </div>
            <div class="status-item">
              <div class="status-label">系统负载</div>
              <div class="status-value">{{ systemLoad }}%</div>
            </div>
          </div>
        </div>

        <!-- 严重程度分布 -->
        <div class="panel pie-chart-panel">
          <div class="panel-title">告警分布</div>
          <div ref="pieChart" class="chart"></div>
        </div>
      </div>
    </div>

    <!-- 全屏告警弹窗 -->
    <el-dialog
      v-model="alertDialogVisible"
      title="紧急告警"
      width="500px"
      :before-close="handleAlertClose"
      class="alert-dialog"
    >
      <div v-if="currentAlert" class="alert-content-dialog">
        <div class="alert-icon">
          <el-icon size="60" color="#F56C6C"><WarningFilled /></el-icon>
        </div>
        <div class="alert-details">
          <h3>检测到跌倒事件</h3>
          <p><strong>位置：</strong>{{ currentAlert.location }}</p>
          <p><strong>时间：</strong>{{ formatTime(currentAlert.timestamp) }}</p>
          <p><strong>严重程度：</strong>{{ getSeverityText(currentAlert.severity) }}</p>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="acknowledgeAlert">确认告警</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, onUnmounted, nextTick } from 'vue'
import { 
  Warning, Clock, DataAnalysis, VideoCamera, Bell, 
  CircleCheck, WarningFilled, Lock 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import axios from 'axios'

export default defineComponent({
  name: 'MonitorScreen',
  components: {
    Warning, Clock, DataAnalysis, VideoCamera, Bell,
    CircleCheck, WarningFilled, Lock
  },
  setup() {
    const currentTime = ref('')
    const currentDate = ref('')
    const statistics = ref({})
    const recentAlerts = ref([])
    const activeCameras = ref(1)
    const systemLoad = ref(15)
    const hasNewAlert = ref(false)
    const alertDialogVisible = ref(false)
    const currentAlert = ref(null)
    
    const trendChart = ref(null)
    const pieChart = ref(null)
    const trajectoryChart = ref(null)
    let trendChartInstance = null
    let pieChartInstance = null
    let trajectoryChartInstance = null
    let timeInterval = null

    // 模拟摄像头数据
    const cameras = ref([
      {
        id: 1,
        name: '摄像头-01',
        location: '客厅',
        status: 'online',
        hasFence: true,
        fencePoints: '20,20 80,20 80,80 20,80'
      },
      {
        id: 2,
        name: '摄像头-02', 
        location: '卧室',
        status: 'online',
        hasFence: true,
        fencePoints: '10,30 90,30 90,70 10,70'
      },
      {
        id: 3,
        name: '摄像头-03',
        location: '卫生间',
        status: 'offline',
        hasFence: false
      },
      {
        id: 4,
        name: '摄像头-04',
        location: '厨房',
        status: 'online',
        hasFence: true,
        fencePoints: '25,15 75,15 75,85 25,85'
      }
    ])

    // 电子围栏数据
    const electronicFences = ref([
      {
        id: 1,
        name: '客厅安全区',
        area: '客厅',
        status: 'active'
      },
      {
        id: 2,
        name: '卧室监护区',
        area: '卧室',
        status: 'active'
      },
      {
        id: 3,
        name: '厨房警戒区',
        area: '厨房',
        status: 'warning'
      }
    ])

    // 更新时间
    const updateTime = () => {
      const now = dayjs()
      currentTime.value = now.format('HH:mm:ss')
      currentDate.value = now.format('YYYY年MM月DD日 dddd')
    }

    // 初始化趋势图
    const initTrendChart = () => {
      if (!trendChart.value) return
      
      trendChartInstance = echarts.init(trendChart.value)
      const option = {
        grid: {
          top: 20,
          left: 40,
          right: 20,
          bottom: 30
        },
        xAxis: {
          type: 'category',
          data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
          axisLine: { lineStyle: { color: '#4a9eff' } },
          axisLabel: { color: '#ffffff' }
        },
        yAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: '#4a9eff' } },
          axisLabel: { color: '#ffffff' },
          splitLine: { lineStyle: { color: '#2a4a6b' } }
        },
        series: [{
          data: [2, 0, 1, 3, 1, 0],
          type: 'line',
          smooth: true,
          itemStyle: { color: '#00d4ff' },
          lineStyle: { color: '#00d4ff', width: 3 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(0, 212, 255, 0.3)' },
                { offset: 1, color: 'rgba(0, 212, 255, 0)' }
              ]
            }
          }
        }]
      }
      trendChartInstance.setOption(option)
    }

    // 初始化饼图
    const initPieChart = () => {
      if (!pieChart.value) return
      
      pieChartInstance = echarts.init(pieChart.value)
      const option = {
        series: [{
          name: '告警分布',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '60%'],
          data: [
            { value: 3, name: '紧急', itemStyle: { color: '#ff4757' } },
            { value: 5, name: '严重', itemStyle: { color: '#ffa726' } }
          ],
          label: {
            color: '#ffffff',
            fontSize: 12
          },
          labelLine: {
            lineStyle: { color: '#ffffff' }
          }
        }]
      }
      pieChartInstance.setOption(option)
    }

    // 初始化运动轨迹图
    const initTrajectoryChart = () => {
      if (!trajectoryChart.value) return
      
      trajectoryChartInstance = echarts.init(trajectoryChart.value)
      const option = {
        grid: {
          top: 20,
          left: 30,
          right: 20,
          bottom: 30
        },
        xAxis: {
          type: 'value',
          min: 0,
          max: 100,
          axisLine: { lineStyle: { color: '#4a9eff' } },
          axisLabel: { show: false },
          splitLine: { lineStyle: { color: '#2a4a6b' } }
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 100,
          axisLine: { lineStyle: { color: '#4a9eff' } },
          axisLabel: { show: false },
          splitLine: { lineStyle: { color: '#2a4a6b' } }
        },
        series: [
          {
            name: '运动轨迹',
            type: 'line',
            data: [
              [20, 30], [25, 35], [30, 40], [35, 45], [40, 50],
              [45, 55], [50, 60], [55, 65], [60, 70], [65, 75]
            ],
            lineStyle: { color: '#00d4ff', width: 2 },
            itemStyle: { color: '#00d4ff' },
            symbol: 'circle',
            symbolSize: 4
          },
          {
            name: '当前位置',
            type: 'scatter',
            data: [[65, 75]],
            itemStyle: { 
              color: '#ff4757',
              borderColor: '#ffffff',
              borderWidth: 2
            },
            symbolSize: 8,
            animation: true,
            animationType: 'scale'
          },
          {
            name: '安全区域',
            type: 'polygon',
            data: [[20, 20], [80, 20], [80, 80], [20, 80]],
            itemStyle: {
              color: 'rgba(0, 212, 255, 0.1)',
              borderColor: '#00d4ff',
              borderWidth: 1,
              borderType: 'dashed'
            }
          }
        ]
      }
      trajectoryChartInstance.setOption(option)
    }

    // 加载数据
    const loadData = async () => {
      try {
        const response = await axios.get('/api/events/statistics')
        statistics.value = response.data
        recentAlerts.value = response.data.recentEvents || []
      } catch (error) {
        console.error('加载数据失败:', error)
        // 使用模拟数据
        statistics.value = {
          todayEvents: 8,
          pendingEvents: 3,
          totalEvents: 156
        }
        recentAlerts.value = [
          {
            id: 1,
            eventType: 'fall_detected',
            severity: 'immediate',
            location: '201房间',
            createdTime: new Date().toISOString(),
            isHandled: false
          }
        ]
      }
    }

    // 模拟实时告警
    const simulateAlert = () => {
      const mockAlert = {
        id: Date.now(),
        eventType: 'fall_detected',
        severity: 'immediate',
        location: '201房间',
        timestamp: new Date().toISOString()
      }
      
      currentAlert.value = mockAlert
      alertDialogVisible.value = true
      hasNewAlert.value = true
      
      // 添加到告警列表
      recentAlerts.value.unshift({
        ...mockAlert,
        createdTime: mockAlert.timestamp,
        isHandled: false
      })
      
      // 保持最多10条记录
      if (recentAlerts.value.length > 10) {
        recentAlerts.value = recentAlerts.value.slice(0, 10)
      }
    }

    const acknowledgeAlert = () => {
      alertDialogVisible.value = false
      hasNewAlert.value = false
      currentAlert.value = null
    }

    const handleAlertClose = () => {
      acknowledgeAlert()
    }

    const formatTime = (time) => {
      return dayjs(time).format('HH:mm:ss')
    }

    const getEventTypeText = (type) => {
      return type === 'fall_detected' ? '跌倒检测' : '长时间躺倒'
    }

    const getSeverityText = (severity) => {
      return severity === 'immediate' ? '紧急' : '严重'
    }

    onMounted(() => {
      updateTime()
      timeInterval = setInterval(updateTime, 1000)
      
      loadData()
      
      nextTick(() => {
        initTrendChart()
        initPieChart()
        initTrajectoryChart()
      })

      // 模拟告警，30秒后触发一次
      setTimeout(simulateAlert, 30000)
    })

    onUnmounted(() => {
      if (timeInterval) {
        clearInterval(timeInterval)
      }
      if (trendChartInstance) {
        trendChartInstance.dispose()
      }
      if (pieChartInstance) {
        pieChartInstance.dispose()
      }
      if (trajectoryChartInstance) {
        trajectoryChartInstance.dispose()
      }
    })

    return {
      currentTime,
      currentDate,
      statistics,
      recentAlerts,
      activeCameras,
      systemLoad,
      hasNewAlert,
      alertDialogVisible,
      currentAlert,
      cameras,
      electronicFences,
      trendChart,
      pieChart,
      trajectoryChart,
      acknowledgeAlert,
      handleAlertClose,
      formatTime,
      getEventTypeText,
      getSeverityText
    }
  }
})
</script>

<style scoped>
.monitor-screen {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #0c1e35 0%, #1a365d 100%);
  color: #ffffff;
  overflow: hidden;
}

.header {
  height: 80px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 2px solid #4a9eff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
}

.title h1 {
  font-size: 28px;
  margin: 0;
  background: linear-gradient(45deg, #4a9eff, #00d4ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  font-size: 14px;
  color: #8fb5db;
  margin-top: 5px;
}

.datetime {
  text-align: right;
}

.time {
  font-size: 24px;
  font-weight: bold;
  color: #00d4ff;
}

.date {
  font-size: 14px;
  color: #8fb5db;
  margin-top: 5px;
}

.main-content {
  height: calc(100vh - 80px);
  display: flex;
  gap: 20px;
  padding: 20px;
}

.left-panel, .right-panel {
  width: 350px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}

.center-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.panel {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid #4a9eff;
  border-radius: 8px;
  padding: 20px;
}

.panel-title {
  font-size: 18px;
  font-weight: bold;
  color: #00d4ff;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #2a4a6b;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.stat-item {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.05);
  padding: 15px;
  border-radius: 6px;
  border: 1px solid rgba(74, 158, 255, 0.3);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
}

.stat-icon.today { background: #ff4757; }
.stat-icon.pending { background: #ffa726; }
.stat-icon.total { background: #4caf50; }
.stat-icon.cameras { background: #9c27b0; }

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #00d4ff;
}

.stat-label {
  font-size: 12px;
  color: #8fb5db;
  margin-top: 2px;
}

.chart {
  height: 200px;
}

.fence-panel {
  flex-shrink: 0;
}

.fence-status {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.fence-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  border: 1px solid rgba(74, 158, 255, 0.3);
}

.fence-info {
  flex: 1;
}

.fence-name {
  font-size: 14px;
  font-weight: bold;
  color: #ffffff;
  margin-bottom: 3px;
}

.fence-area {
  font-size: 12px;
  color: #8fb5db;
}

.fence-indicator {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fence-indicator.active {
  background: #4caf50;
  color: #ffffff;
}

.fence-indicator.warning {
  background: #ffa726;
  color: #ffffff;
}

.fence-indicator.inactive {
  background: #f44336;
  color: #ffffff;
}

.fence-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.fence-svg {
  width: 100%;
  height: 100%;
}

.trajectory-panel {
  flex-shrink: 0;
  height: 250px;
}

.trajectory-panel .chart {
  height: 180px;
}

.video-panel {
  flex: 1;
}

.video-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  height: calc(100% - 60px);
}

.video-item {
  background: rgba(0, 0, 0, 0.6);
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #4a9eff;
}

.video-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.video-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8fb5db;
}

.camera-info {
  text-align: center;
  margin-top: 10px;
}

.camera-name {
  font-weight: bold;
  font-size: 14px;
}

.camera-location {
  font-size: 12px;
  color: #8fb5db;
  margin: 5px 0;
}

.camera-status {
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.camera-status.online { color: #4caf50; }
.camera-status.offline { color: #f44336; }

.alerts-list {
  max-height: 400px;
  overflow-y: auto;
}

.alert-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 10px;
  border-left: 4px solid #ffa726;
}

.alert-item.immediate {
  border-left-color: #ff4757;
}

.alert-time {
  font-size: 12px;
  color: #8fb5db;
  margin-bottom: 5px;
}

.alert-content {
  margin-bottom: 10px;
}

.alert-title {
  font-weight: bold;
  color: #ffffff;
  margin-bottom: 3px;
}

.alert-location {
  font-size: 12px;
  color: #8fb5db;
}

.alert-severity {
  font-size: 12px;
  color: #ffa726;
}

.alert-status {
  font-size: 12px;
  color: #ff4757;
}

.alert-status.handled {
  color: #4caf50;
}

.alert-indicator {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  transition: all 0.3s;
}

.alert-indicator.active {
  background: #ff4757;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(255, 71, 87, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0); }
}

.system-status {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.status-label {
  color: #8fb5db;
  font-size: 14px;
}

.status-value {
  font-weight: bold;
  font-size: 14px;
}

.status-value.online {
  color: #4caf50;
}

.alert-dialog {
  color: #333;
}

.alert-content-dialog {
  display: flex;
  align-items: center;
  gap: 20px;
}

.alert-details h3 {
  color: #f56c6c;
  margin-bottom: 15px;
}

.alert-details p {
  margin: 8px 0;
  color: #666;
}
</style>