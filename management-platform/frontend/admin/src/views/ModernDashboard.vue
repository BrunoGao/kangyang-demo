<template>
  <div class="modern-dashboard">
    <!-- 页面头部 -->
    <div class="dashboard-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">🏥 康养监控中心</h1>
          <p class="page-subtitle">实时跌倒检测与火焰监控系统</p>
        </div>
        <div class="header-actions">
          <el-button type="primary" :icon="Refresh" @click="refreshData" :loading="loading">
            刷新数据
          </el-button>
          <el-button type="success" :icon="VideoCamera" @click="openVideoTest">
            视频测试
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片区域 -->
    <div class="stats-section">
      <div class="stats-grid">
        <!-- 今日告警 -->
        <div class="stat-card today-alerts">
          <div class="card-icon">
            <i class="icon-alert">🚨</i>
          </div>
          <div class="card-content">
            <div class="stat-number">{{ statistics.todayAlerts || 0 }}</div>
            <div class="stat-label">今日告警</div>
            <div class="stat-trend">
              <span class="trend-icon">↗️</span>
              <span class="trend-text">较昨日 +12%</span>
            </div>
          </div>
          <div class="card-glow today"></div>
        </div>

        <!-- 待处理事件 -->
        <div class="stat-card pending-events">
          <div class="card-icon">
            <i class="icon-pending">⏳</i>
          </div>
          <div class="card-content">
            <div class="stat-number">{{ statistics.pendingEvents || 0 }}</div>
            <div class="stat-label">待处理</div>
            <div class="stat-trend">
              <span class="trend-icon">↘️</span>
              <span class="trend-text">较昨日 -8%</span>
            </div>
          </div>
          <div class="card-glow pending"></div>
        </div>

        <!-- 总监控数 -->
        <div class="stat-card total-monitors">
          <div class="card-icon">
            <i class="icon-total">📊</i>
          </div>
          <div class="card-content">
            <div class="stat-number">{{ statistics.totalAlerts || 0 }}</div>
            <div class="stat-label">总告警数</div>
            <div class="stat-trend">
              <span class="trend-icon">📈</span>
              <span class="trend-text">累计增长</span>
            </div>
          </div>
          <div class="card-glow total"></div>
        </div>

        <!-- 活跃设备 -->
        <div class="stat-card active-devices">
          <div class="card-icon">
            <i class="icon-devices">📹</i>
          </div>
          <div class="card-content">
            <div class="stat-number">{{ statistics.activeCameras || 1 }}</div>
            <div class="stat-label">活跃摄像头</div>
            <div class="stat-trend">
              <span class="trend-icon">✅</span>
              <span class="trend-text">运行正常</span>
            </div>
          </div>
          <div class="card-glow devices"></div>
        </div>
      </div>
    </div>

    <!-- 图表分析区域 -->
    <div class="analytics-section">
      <div class="charts-grid">
        <!-- 告警趋势图 -->
        <div class="chart-card trend-chart">
          <div class="chart-header">
            <h3 class="chart-title">📈 告警趋势分析</h3>
            <div class="chart-controls">
              <el-radio-group v-model="trendPeriod" size="small">
                <el-radio-button label="7d">7天</el-radio-button>
                <el-radio-button label="30d">30天</el-radio-button>
                <el-radio-button label="90d">90天</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div ref="trendChart" class="chart-container"></div>
        </div>

        <!-- 告警类型分布 -->
        <div class="chart-card type-chart">
          <div class="chart-header">
            <h3 class="chart-title">🔥 告警类型分布</h3>
            <div class="chart-legend">
              <span class="legend-item fall">
                <span class="legend-dot"></span>跌倒检测
              </span>
              <span class="legend-item fire">
                <span class="legend-dot"></span>火焰检测
              </span>
              <span class="legend-item smoke">
                <span class="legend-dot"></span>烟雾检测
              </span>
            </div>
          </div>
          <div ref="typeChart" class="chart-container"></div>
        </div>
      </div>
    </div>

    <!-- 实时监控面板 -->
    <div class="monitoring-section">
      <div class="section-header">
        <h2 class="section-title">🎯 实时监控面板</h2>
        <div class="section-controls">
          <el-switch
            v-model="autoRefresh"
            active-text="自动刷新"
            inactive-text="手动刷新"
          />
        </div>
      </div>

      <div class="monitoring-grid">
        <!-- 最新告警 -->
        <div class="monitor-card recent-alerts">
          <div class="card-header">
            <h4>🚨 最新告警</h4>
            <el-tag type="danger" size="small">实时</el-tag>
          </div>
          <div class="alerts-list">
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
                <div class="alert-title">{{ alert.message }}</div>
                <div class="alert-meta">
                  <span class="alert-location">📍 {{ alert.location }}</span>
                  <span class="alert-time">🕐 {{ formatTime(alert.timestamp) }}</span>
                </div>
              </div>
              <div class="alert-status">
                <el-tag 
                  :type="alert.severity === 'CRITICAL' ? 'danger' : 'warning'"
                  size="small"
                >
                  {{ alert.severity }}
                </el-tag>
              </div>
            </div>
            <div v-if="recentAlerts.length === 0" class="no-alerts">
              <i class="no-data-icon">✅</i>
              <p>暂无新告警</p>
            </div>
          </div>
        </div>

        <!-- 系统状态 -->
        <div class="monitor-card system-status">
          <div class="card-header">
            <h4>⚙️ 系统状态</h4>
            <el-tag type="success" size="small">正常</el-tag>
          </div>
          <div class="status-grid">
            <div class="status-item">
              <div class="status-icon ai">🤖</div>
              <div class="status-info">
                <div class="status-name">AI检测服务</div>
                <div class="status-value">运行中</div>
              </div>
              <div class="status-indicator online"></div>
            </div>
            <div class="status-item">
              <div class="status-icon backend">⚙️</div>
              <div class="status-info">
                <div class="status-name">后端服务</div>
                <div class="status-value">正常</div>
              </div>
              <div class="status-indicator online"></div>
            </div>
            <div class="status-item">
              <div class="status-icon database">🗄️</div>
              <div class="status-info">
                <div class="status-name">数据库</div>
                <div class="status-value">连接正常</div>
              </div>
              <div class="status-indicator online"></div>
            </div>
            <div class="status-item">
              <div class="status-icon camera">📹</div>
              <div class="status-info">
                <div class="status-name">摄像头</div>
                <div class="status-value">1/1 在线</div>
              </div>
              <div class="status-indicator online"></div>
            </div>
          </div>
        </div>

        <!-- 性能指标 -->
        <div class="monitor-card performance">
          <div class="card-header">
            <h4>📊 性能指标</h4>
            <el-progress 
              :percentage="75" 
              status="success" 
              :stroke-width="6"
              style="width: 100px;"
            />
          </div>
          <div class="performance-grid">
            <div class="perf-item">
              <div class="perf-label">检测准确率</div>
              <div class="perf-value">94.5%</div>
              <div class="perf-bar">
                <div class="perf-fill" style="width: 94.5%"></div>
              </div>
            </div>
            <div class="perf-item">
              <div class="perf-label">响应时间</div>
              <div class="perf-value">0.25s</div>
              <div class="perf-bar">
                <div class="perf-fill good" style="width: 85%"></div>
              </div>
            </div>
            <div class="perf-item">
              <div class="perf-label">误报率</div>
              <div class="perf-value">3.2%</div>
              <div class="perf-bar">
                <div class="perf-fill excellent" style="width: 20%"></div>
              </div>
            </div>
            <div class="perf-item">
              <div class="perf-label">系统负载</div>
              <div class="perf-value">42%</div>
              <div class="perf-bar">
                <div class="perf-fill good" style="width: 42%"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快速操作区域 -->
    <div class="actions-section">
      <div class="actions-grid">
        <div class="action-card" @click="exportReport">
          <div class="action-icon">📄</div>
          <div class="action-title">导出报告</div>
          <div class="action-desc">生成详细分析报告</div>
        </div>
        <div class="action-card" @click="openSettings">
          <div class="action-icon">⚙️</div>
          <div class="action-title">系统设置</div>
          <div class="action-desc">配置检测参数</div>
        </div>
        <div class="action-card" @click="viewHistory">
          <div class="action-icon">📚</div>
          <div class="action-title">历史记录</div>
          <div class="action-desc">查看所有告警历史</div>
        </div>
        <div class="action-card" @click="helpCenter">
          <div class="action-icon">❓</div>
          <div class="action-title">帮助中心</div>
          <div class="action-desc">使用说明和支持</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, nextTick, onUnmounted } from 'vue'
import { Refresh, VideoCamera } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'

export default defineComponent({
  name: 'ModernDashboard',
  components: {
    Refresh,
    VideoCamera
  },
  setup() {
    const loading = ref(false)
    const autoRefresh = ref(true)
    const trendPeriod = ref('7d')
    const trendChart = ref(null)
    const typeChart = ref(null)
    
    const statistics = ref({
      todayAlerts: 17,
      pendingEvents: 3,
      totalAlerts: 186,
      activeCameras: 1
    })
    
    const recentAlerts = ref([
      {
        id: 1,
        type: 'fall',
        message: '检测到跌倒事件',
        location: '201房间',
        timestamp: new Date().toISOString(),
        severity: 'HIGH'
      },
      {
        id: 2,
        type: 'fire',
        message: '检测到火焰',
        location: '厨房区域',
        timestamp: new Date(Date.now() - 300000).toISOString(),
        severity: 'CRITICAL'
      },
      {
        id: 3,
        type: 'smoke',
        message: '检测到烟雾',
        location: '休息区',
        timestamp: new Date(Date.now() - 600000).toISOString(),
        severity: 'HIGH'
      }
    ])

    let refreshInterval = null

    const initTrendChart = () => {
      if (!trendChart.value) return
      
      const chart = echarts.init(trendChart.value)
      const option = {
        grid: {
          top: '15%',
          left: '5%',
          right: '5%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
          axisLine: {
            lineStyle: { color: '#E4E7ED' }
          },
          axisLabel: {
            color: '#606266'
          }
        },
        yAxis: {
          type: 'value',
          axisLine: {
            lineStyle: { color: '#E4E7ED' }
          },
          axisLabel: {
            color: '#606266'
          },
          splitLine: {
            lineStyle: { color: '#F5F7FA' }
          }
        },
        series: [{
          data: [8, 12, 15, 9, 13, 18, 11],
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            width: 3,
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 1, y2: 0,
              colorStops: [
                { offset: 0, color: '#409EFF' },
                { offset: 1, color: '#67C23A' }
              ]
            }
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
                { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
              ]
            }
          }
        }]
      }
      chart.setOption(option)
    }

    const initTypeChart = () => {
      if (!typeChart.value) return
      
      const chart = echarts.init(typeChart.value)
      const option = {
        grid: {
          top: '15%',
          left: '5%',
          right: '5%',
          bottom: '15%',
          containLabel: true
        },
        legend: {
          show: false
        },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '50%'],
          data: [
            { value: 12, name: '跌倒检测', itemStyle: { color: '#F56C6C' } },
            { value: 3, name: '火焰检测', itemStyle: { color: '#E6A23C' } },
            { value: 2, name: '烟雾检测', itemStyle: { color: '#909399' } }
          ],
          label: {
            show: true,
            formatter: '{b}: {c}',
            fontSize: 12,
            color: '#606266'
          },
          emphasis: {
            scale: true,
            scaleSize: 10
          }
        }]
      }
      chart.setOption(option)
    }

    const refreshData = async () => {
      loading.value = true
      try {
        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // 更新统计数据
        statistics.value = {
          todayAlerts: Math.floor(Math.random() * 20) + 10,
          pendingEvents: Math.floor(Math.random() * 5),
          totalAlerts: statistics.value.totalAlerts + Math.floor(Math.random() * 3),
          activeCameras: 1
        }
        
        ElMessage.success('数据刷新成功')
      } catch (error) {
        ElMessage.error('数据刷新失败')
      } finally {
        loading.value = false
      }
    }

    const formatTime = (time) => {
      return dayjs(time).format('HH:mm:ss')
    }

    const openVideoTest = () => {
      const videoTestUrl = import.meta.env.VITE_VIDEO_TEST_URL || 'http://localhost:5557'
      window.open(videoTestUrl, '_blank')
    }

    const exportReport = () => {
      ElMessage.info('报告导出功能开发中...')
    }

    const openSettings = () => {
      ElMessage.info('系统设置功能开发中...')
    }

    const viewHistory = () => {
      ElMessage.info('历史记录功能开发中...')
    }

    const helpCenter = () => {
      ElMessage.info('帮助中心功能开发中...')
    }

    const startAutoRefresh = () => {
      if (autoRefresh.value) {
        refreshInterval = setInterval(() => {
          refreshData()
        }, 30000) // 30秒刷新一次
      }
    }

    const stopAutoRefresh = () => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
        refreshInterval = null
      }
    }

    onMounted(async () => {
      await nextTick()
      initTrendChart()
      initTypeChart()
      
      if (autoRefresh.value) {
        startAutoRefresh()
      }
    })

    onUnmounted(() => {
      stopAutoRefresh()
    })

    // 监听自动刷新开关
    const toggleAutoRefresh = () => {
      if (autoRefresh.value) {
        startAutoRefresh()
      } else {
        stopAutoRefresh()
      }
    }

    return {
      loading,
      autoRefresh,
      trendPeriod,
      trendChart,
      typeChart,
      statistics,
      recentAlerts,
      refreshData,
      formatTime,
      openVideoTest,
      exportReport,
      openSettings,
      viewHistory,
      helpCenter,
      toggleAutoRefresh
    }
  }
})
</script>

<style scoped>
.modern-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

/* 页面头部 */
.dashboard-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 20px 30px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  margin: 5px 0 0 0;
  color: #6b7280;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 统计卡片区域 */
.stats-section {
  padding: 30px;
  max-width: 1400px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.stat-card {
  position: relative;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 25px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.card-icon {
  font-size: 2.5rem;
  margin-bottom: 15px;
}

.stat-number {
  font-size: 2.8rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 10px;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #059669;
}

.card-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  opacity: 0.1;
  pointer-events: none;
}

.card-glow.today { background: #f56565; }
.card-glow.pending { background: #ed8936; }
.card-glow.total { background: #38b2ac; }
.card-glow.devices { background: #667eea; }

/* 图表分析区域 */
.analytics-section {
  padding: 0 30px 30px;
  max-width: 1400px;
  margin: 0 auto;
}

.charts-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.chart-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 25px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.chart-container {
  height: 300px;
}

.chart-legend {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #6b7280;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-item.fall .legend-dot { background: #F56C6C; }
.legend-item.fire .legend-dot { background: #E6A23C; }
.legend-item.smoke .legend-dot { background: #909399; }

/* 实时监控面板 */
.monitoring-section {
  padding: 0 30px 30px;
  max-width: 1400px;
  margin: 0 auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: white;
  margin: 0;
}

.monitoring-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
}

.monitor-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.card-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

/* 告警列表 */
.alerts-list {
  max-height: 300px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 8px;
  background: #f9fafb;
  border-left: 4px solid;
}

.alert-item.fall { border-left-color: #f56565; }
.alert-item.fire { border-left-color: #ed8936; }
.alert-item.smoke { border-left-color: #9ca3af; }

.alert-icon {
  font-size: 1.5rem;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.alert-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #6b7280;
}

.no-alerts {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
}

.no-data-icon {
  font-size: 2rem;
  margin-bottom: 10px;
  display: block;
}

/* 系统状态 */
.status-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 8px;
  background: #f9fafb;
}

.status-icon {
  font-size: 1.5rem;
}

.status-info {
  flex: 1;
}

.status-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.status-value {
  font-size: 12px;
  color: #6b7280;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-indicator.online { background: #10b981; }
.status-indicator.offline { background: #ef4444; }

/* 性能指标 */
.performance-grid {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.perf-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.perf-label {
  font-size: 12px;
  color: #6b7280;
}

.perf-value {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.perf-bar {
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
}

.perf-fill {
  height: 100%;
  background: #3b82f6;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.perf-fill.good { background: #10b981; }
.perf-fill.excellent { background: #059669; }

/* 快速操作区域 */
.actions-section {
  padding: 0 30px 30px;
  max-width: 1400px;
  margin: 0 auto;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.action-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 15px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.action-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15);
}

.action-icon {
  font-size: 2rem;
  margin-bottom: 10px;
}

.action-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 5px;
}

.action-desc {
  font-size: 12px;
  color: #6b7280;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .monitoring-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .monitoring-grid {
    grid-template-columns: 1fr;
  }
  
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .header-content {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>