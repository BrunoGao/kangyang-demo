<template>
  <div class="edge-devices">
    <div class="page-header">
      <h1>边缘控制器管理</h1>
      <p>管理22路摄像头的两个边缘控制器设备</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon online">📡</div>
        <div class="stat-content">
          <h3>{{ statistics.online_controllers }}</h3>
          <p>在线控制器</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon offline">⚠️</div>
        <div class="stat-content">
          <h3>{{ statistics.offline_controllers }}</h3>
          <p>离线控制器</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon cameras">📷</div>
        <div class="stat-content">
          <h3>{{ statistics.total_cameras }}</h3>
          <p>总摄像头数</p>
        </div>
      </div>
    </div>

    <!-- 控制器列表 -->
    <div class="controllers-section">
      <div class="section-header">
        <h2>边缘控制器列表</h2>
        <div class="section-actions">
          <button @click="loadControllers" class="btn-primary">刷新</button>
          <button @click="batchHealthCheck" class="btn-secondary">批量检查</button>
        </div>
      </div>
      
      <div class="controllers-grid">
        <div 
          v-for="controller in controllers" 
          :key="controller.controller_id"
          class="controller-card"
          :class="{ 'online': controller.is_online, 'offline': !controller.is_online }"
        >
          <div class="controller-header">
            <div class="controller-status">
              <span class="status-indicator" :class="{ 'online': controller.is_online }"></span>
              <h3>{{ controller.controller_name }}</h3>
            </div>
            <div class="controller-actions">
              <button @click="viewController(controller)" class="btn-primary">详情</button>
              <button @click="configController(controller)" class="btn-secondary">配置</button>
              <button @click="testAIDetection(controller)" class="btn-test">AI检测</button>
            </div>
          </div>

          <div class="controller-info">
            <div class="info-item">
              <label>控制器ID:</label>
              <span>{{ controller.controller_id }}</span>
            </div>
            <div class="info-item">
              <label>最后心跳:</label>
              <span>{{ formatTime(controller.last_heartbeat) }}</span>
            </div>
            <div class="info-item">
              <label>摄像头数:</label>
              <span>{{ controller.camera_count || 0 }}</span>
            </div>
          </div>

          <!-- 系统状态 -->
          <div v-if="controller.system_stats" class="system-stats">
            <h4>系统状态</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <span class="label">CPU使用率:</span>
                <span class="value">{{ controller.system_stats.cpu_usage || 'N/A' }}%</span>
              </div>
              <div class="stat-item">
                <span class="label">内存使用:</span>
                <span class="value">{{ controller.system_stats.memory_usage || 'N/A' }}%</span>
              </div>
              <div class="stat-item">
                <span class="label">平均FPS:</span>
                <span class="value">{{ controller.system_stats.average_fps || 'N/A' }}</span>
              </div>
              <div class="stat-item">
                <span class="label">总检测数:</span>
                <span class="value">{{ controller.system_stats.total_detections || 0 }}</span>
              </div>
            </div>
          </div>

          <!-- 摄像头列表预览 -->
          <div class="cameras-preview">
            <h4>摄像头 ({{ (controller.cameras || []).length }})</h4>
            <div class="camera-items">
              <div 
                v-for="camera in (controller.cameras || []).slice(0, 3)" 
                :key="camera.id"
                class="camera-item"
                :class="{ 'online': camera.status === 'online' }"
              >
                <span class="camera-name">{{ camera.name }}</span>
                <span class="camera-status">{{ camera.status }}</span>
              </div>
              <div v-if="(controller.cameras || []).length > 3" class="more-cameras">
                +{{ (controller.cameras || []).length - 3 }} 更多...
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 控制器详情模态框 -->
    <div v-if="selectedController" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ selectedController.controller_name }} - 详情</h2>
          <button @click="closeModal" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="detail-section">
            <h3>基本信息</h3>
            <div class="detail-grid">
              <div class="detail-item">
                <label>控制器ID:</label>
                <span>{{ selectedController.controller_id }}</span>
              </div>
              <div class="detail-item">
                <label>状态:</label>
                <span :class="{ 'status-online': selectedController.is_online, 'status-offline': !selectedController.is_online }">
                  {{ selectedController.is_online ? '在线' : '离线' }}
                </span>
              </div>
              <div class="detail-item">
                <label>最后心跳:</label>
                <span>{{ formatTime(selectedController.last_heartbeat) }}</span>
              </div>
              <div class="detail-item">
                <label>运行时间:</label>
                <span>{{ formatUptime(selectedController.system_stats?.uptime_seconds) }}</span>
              </div>
            </div>
          </div>

          <!-- 摄像头管理 -->
          <div class="detail-section">
            <div class="section-header">
              <h3>摄像头管理</h3>
              <button @click="addCamera" class="btn-primary">添加摄像头</button>
            </div>
            
            <div class="cameras-table">
              <table>
                <thead>
                  <tr>
                    <th>摄像头ID</th>
                    <th>名称</th>
                    <th>位置</th>
                    <th>状态</th>
                    <th>算法</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="camera in selectedController.cameras" :key="camera.id">
                    <td>{{ camera.id }}</td>
                    <td>{{ camera.name }}</td>
                    <td>{{ camera.location }}</td>
                    <td>
                      <span class="status-badge" :class="camera.status">
                        {{ camera.status }}
                      </span>
                    </td>
                    <td>{{ (camera.enabled_algorithms || []).join(', ') }}</td>
                    <td>
                      <button @click="startCamera(camera)" class="btn-small btn-success">启动</button>
                      <button @click="stopCamera(camera)" class="btn-small btn-warning">停止</button>
                      <button @click="removeCamera(camera)" class="btn-small btn-danger">移除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'

export default {
  name: 'EdgeDevices',
  setup() {
    const controllers = ref([])
    const statistics = ref({
      total_controllers: 0,
      online_controllers: 0,
      offline_controllers: 0,
      total_cameras: 0
    })
    const selectedController = ref(null)
    const loading = ref(false)

    // 获取边缘控制器列表
    const loadControllers = async () => {
      try {
        loading.value = true
        // 从新的API端点获取边缘设备数据
        const response = await fetch('/api/edge-devices')
        const data = await response.json()
        controllers.value = data || []
        
        // 获取详细信息
        for (let controller of controllers.value) {
          await loadControllerDetail(controller.deviceId || controller.controller_id)
        }
      } catch (error) {
        console.error('加载控制器列表失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    // 模拟AI检测功能
    const simulateAIDetection = async (deviceId, detectionType = 'fall') => {
      try {
        const detectionData = {
          type: detectionType,
          location: `${deviceId}-测试位置`,
          confidence: 0.95
        }
        
        const response = await fetch(`/api/edge-devices/${deviceId}/simulate-detection`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(detectionData)
        })
        
        const result = await response.json()
        if (result.success) {
          alert(`AI${detectionType === 'fall' ? '跌倒' : detectionType === 'fire' ? '火焰' : '烟雾'}检测模拟成功！`)
        } else {
          alert('检测模拟失败')
        }
      } catch (error) {
        console.error('模拟AI检测失败:', error)
        alert('检测模拟失败')
      }
    }
    
    // 批量健康检查
    const batchHealthCheck = async () => {
      try {
        loading.value = true
        const response = await fetch('/api/edge-devices/health-check', {
          method: 'POST'
        })
        const result = await response.json()
        alert(`批量健康检查完成，共检查 ${result.results?.length || 0} 个设备`)
        await loadControllers()
      } catch (error) {
        console.error('批量健康检查失败:', error)
        alert('批量健康检查失败')
      } finally {
        loading.value = false
      }
    }
    
    // 测试AI检测功能
    const testAIDetection = async (controller) => {
      const detectionTypes = ['fall', 'fire', 'smoke']
      const selectedType = detectionTypes[Math.floor(Math.random() * detectionTypes.length)]
      await simulateAIDetection(controller.deviceId || controller.controller_id, selectedType)
    }

    // 获取控制器详情
    const loadControllerDetail = async (controllerId) => {
      try {
        const response = await fetch(`/api/edge/controllers/${controllerId}`)
        const data = await response.json()
        
        const index = controllers.value.findIndex(c => c.controller_id === controllerId)
        if (index !== -1) {
          controllers.value[index] = { ...controllers.value[index], ...data }
        }
      } catch (error) {
        console.error(`加载控制器详情失败: ${controllerId}`, error)
      }
    }

    // 获取统计信息
    const loadStatistics = async () => {
      try {
        const response = await fetch('/api/edge/statistics')
        const data = await response.json()
        statistics.value = data
      } catch (error) {
        console.error('加载统计信息失败:', error)
      }
    }

    // 查看控制器详情
    const viewController = async (controller) => {
      selectedController.value = controller
      await loadControllerDetail(controller.controller_id)
    }

    // 配置控制器
    const configController = (controller) => {
      // TODO: 实现配置功能
      alert(`配置控制器: ${controller.controller_name}`)
    }

    // 关闭模态框
    const closeModal = () => {
      selectedController.value = null
    }

    // 添加摄像头
    const addCamera = () => {
      // TODO: 实现添加摄像头功能
      alert('添加摄像头功能')
    }

    // 启动摄像头
    const startCamera = async (camera) => {
      try {
        const response = await fetch(
          `/api/edge/controllers/${selectedController.value.controller_id}/cameras/${camera.id}/stream?action=start`,
          { method: 'POST' }
        )
        if (response.ok) {
          alert('摄像头启动成功')
          await loadControllerDetail(selectedController.value.controller_id)
        }
      } catch (error) {
        console.error('启动摄像头失败:', error)
      }
    }

    // 停止摄像头
    const stopCamera = async (camera) => {
      try {
        const response = await fetch(
          `/api/edge/controllers/${selectedController.value.controller_id}/cameras/${camera.id}/stream?action=stop`,
          { method: 'POST' }
        )
        if (response.ok) {
          alert('摄像头停止成功')
          await loadControllerDetail(selectedController.value.controller_id)
        }
      } catch (error) {
        console.error('停止摄像头失败:', error)
      }
    }

    // 移除摄像头
    const removeCamera = async (camera) => {
      if (confirm(`确定要移除摄像头 ${camera.name} 吗？`)) {
        try {
          const response = await fetch(
            `/api/edge/controllers/${selectedController.value.controller_id}/cameras/${camera.id}`,
            { method: 'DELETE' }
          )
          if (response.ok) {
            alert('摄像头移除成功')
            await loadControllerDetail(selectedController.value.controller_id)
          }
        } catch (error) {
          console.error('移除摄像头失败:', error)
        }
      }
    }

    // 格式化时间
    const formatTime = (timeStr) => {
      if (!timeStr) return 'N/A'
      try {
        return new Date(timeStr).toLocaleString()
      } catch {
        return timeStr
      }
    }

    // 格式化运行时间
    const formatUptime = (seconds) => {
      if (!seconds) return 'N/A'
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      return `${hours}小时${minutes}分钟`
    }

    onMounted(() => {
      loadControllers()
      loadStatistics()
      
      // 定时刷新
      setInterval(() => {
        loadControllers()
        loadStatistics()
      }, 30000)
    })

    return {
      controllers,
      statistics,
      selectedController,
      loading,
      viewController,
      configController,
      closeModal,
      addCamera,
      startCamera,
      stopCamera,
      removeCamera,
      formatTime,
      formatUptime,
      loadControllers,
      batchHealthCheck,
      testAIDetection,
      simulateAIDetection
    }
  }
}
</script>

<style scoped>
.edge-devices {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.page-header p {
  color: #7f8c8d;
  font-size: 16px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  font-size: 24px;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.stat-icon.online { background: #e8f5e8; }
.stat-icon.offline { background: #fee; }
.stat-icon.cameras { background: #e6f3ff; }

.stat-content h3 {
  font-size: 28px;
  margin: 0;
  color: #2c3e50;
}

.stat-content p {
  margin: 5px 0 0 0;
  color: #7f8c8d;
}

.controllers-section h2 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.controllers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.controller-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  border-left: 4px solid #ddd;
}

.controller-card.online {
  border-left-color: #27ae60;
}

.controller-card.offline {
  border-left-color: #e74c3c;
}

.controller-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.controller-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #e74c3c;
}

.status-indicator.online {
  background: #27ae60;
}

.controller-actions {
  display: flex;
  gap: 10px;
}

.btn-primary, .btn-secondary, .btn-test {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  margin-right: 8px;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-test {
  background: #f39c12;
  color: white;
}

.section-actions {
  display: flex;
  gap: 12px;
}

.controller-info {
  margin-bottom: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #ecf0f1;
}

.info-item label {
  font-weight: 600;
  color: #7f8c8d;
}

.system-stats h4 {
  color: #2c3e50;
  margin-bottom: 10px;
  font-size: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 6px;
}

.cameras-preview h4 {
  color: #2c3e50;
  margin-bottom: 10px;
  font-size: 16px;
}

.camera-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.camera-item {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #e74c3c;
}

.camera-item.online {
  border-left-color: #27ae60;
}

.more-cameras {
  color: #7f8c8d;
  font-style: italic;
  text-align: center;
  padding: 8px;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #ecf0f1;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #7f8c8d;
}

.modal-body {
  padding: 20px;
}

.detail-section {
  margin-bottom: 30px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detail-item label {
  font-weight: 600;
  color: #7f8c8d;
}

.status-online {
  color: #27ae60;
  font-weight: 600;
}

.status-offline {
  color: #e74c3c;
  font-weight: 600;
}

.cameras-table {
  overflow-x: auto;
}

.cameras-table table {
  width: 100%;
  border-collapse: collapse;
}

.cameras-table th,
.cameras-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ecf0f1;
}

.cameras-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #2c3e50;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.online {
  background: #d4edda;
  color: #155724;
}

.status-badge.offline {
  background: #f8d7da;
  color: #721c24;
}

.btn-small {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin-right: 5px;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-warning {
  background: #ffc107;
  color: #212529;
}

.btn-danger {
  background: #dc3545;
  color: white;
}
</style>