<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon today">
              <el-icon size="30"><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ statistics.todayEvents || 0 }}</div>
              <div class="stat-label">今日告警</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon pending">
              <el-icon size="30"><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ statistics.pendingEvents || 0 }}</div>
              <div class="stat-label">待处理</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon total">
            <el-icon size="30"><DataAnalysis /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ statistics.totalEvents || 0 }}</div>
            <div class="stat-label">总告警数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon cameras">
              <el-icon size="30"><VideoCamera /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">1</div>
              <div class="stat-label">活跃摄像头</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card title="告警趋势">
          <div ref="trendChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card title="告警严重程度分布">
          <div ref="severityChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近告警列表 -->
    <el-card title="最近告警事件" class="recent-events">
      <el-table :data="recentEvents" style="width: 100%">
        <el-table-column prop="createdTime" label="时间" width="180">
          <template #default="scope">
            {{ formatTime(scope.row.createdTime) }}
          </template>
        </el-table-column>
        <el-table-column prop="location" label="位置" />
        <el-table-column prop="eventType" label="事件类型">
          <template #default="scope">
            <el-tag :type="scope.row.eventType === 'fall_detected' ? 'danger' : 'warning'">
              {{ scope.row.eventType === 'fall_detected' ? '跌倒检测' : '长时间躺倒' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度">
          <template #default="scope">
            <el-tag :type="getSeverityType(scope.row.severity)">
              {{ getSeverityText(scope.row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="isHandled" label="状态">
          <template #default="scope">
            <el-tag :type="scope.row.isHandled ? 'success' : 'danger'">
              {{ scope.row.isHandled ? '已处理' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button 
              v-if="!scope.row.isHandled"
              type="primary" 
              size="small" 
              @click="handleEvent(scope.row)"
            >
              处理
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, nextTick } from 'vue'
import { Warning, Clock, DataAnalysis, VideoCamera } from '@element-plus/icons-vue'
import { useEventStore } from '@/stores/event'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'

export default defineComponent({
  name: 'Dashboard',
  components: {
    Warning,
    Clock,
    DataAnalysis,
    VideoCamera
  },
  setup() {
    const eventStore = useEventStore()
    const trendChart = ref(null)
    const severityChart = ref(null)
    const statistics = ref({})
    const recentEvents = ref([])

    const initTrendChart = () => {
      const chart = echarts.init(trendChart.value)
      const option = {
        title: { text: '最近7天告警趋势' },
        xAxis: {
          type: 'category',
          data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        },
        yAxis: { type: 'value' },
        series: [{
          data: [5, 8, 12, 6, 9, 15, 7],
          type: 'line',
          smooth: true,
          itemStyle: { color: '#409EFF' }
        }]
      }
      chart.setOption(option)
    }

    const initSeverityChart = () => {
      const chart = echarts.init(severityChart.value)
      const option = {
        title: { text: '告警严重程度分布' },
        series: [{
          type: 'pie',
          radius: '60%',
          data: [
            { value: statistics.value.severityStats?.immediate || 0, name: '紧急' },
            { value: statistics.value.severityStats?.critical || 0, name: '严重' }
          ],
          itemStyle: {
            color: function(params) {
              return params.name === '紧急' ? '#F56C6C' : '#E6A23C'
            }
          }
        }]
      }
      chart.setOption(option)
    }

    const handleEvent = async (event) => {
      try {
        const { value } = await ElMessageBox.prompt('请输入处理备注', '处理告警', {
          confirmButtonText: '确定',
          cancelButtonText: '取消'
        })
        
        await eventStore.handleEvent(event.id, '管理员', value)
        ElMessage.success('事件处理成功')
        await loadData()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('处理失败')
        }
      }
    }

    const formatTime = (time) => {
      return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
    }

    const getSeverityType = (severity) => {
      return severity === 'immediate' ? 'danger' : 'warning'
    }

    const getSeverityText = (severity) => {
      return severity === 'immediate' ? '紧急' : '严重'
    }

    const loadData = async () => {
      await eventStore.fetchStatistics()
      statistics.value = eventStore.statistics
      recentEvents.value = eventStore.statistics.recentEvents || []
    }

    onMounted(async () => {
      await loadData()
      nextTick(() => {
        initTrendChart()
        initSeverityChart()
      })
    })

    return {
      statistics,
      recentEvents,
      trendChart,
      severityChart,
      handleEvent,
      formatTime,
      getSeverityType,
      getSeverityText
    }
  }
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  color: white;
}

.stat-icon.today { background: #409EFF; }
.stat-icon.pending { background: #E6A23C; }
.stat-icon.total { background: #67C23A; }
.stat-icon.cameras { background: #909399; }

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.charts-row {
  margin-bottom: 20px;
}

.recent-events {
  margin-top: 20px;
}
</style>