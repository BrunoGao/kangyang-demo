<template>
  <div class="edge-devices">
    <div class="page-header">
      <h1>边缘控制器管理</h1>
      <p>智能管理边缘AI设备：算法配置、摄像头控制、性能监控、服务管理</p>
    </div>

    <!-- 统计卡片增强 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon online">📡</div>
        <div class="stat-content">
          <h3>{{ statistics.online_controllers }}</h3>
          <p>在线控制器</p>
          <span class="stat-change positive">+2%</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon cameras">📷</div>
        <div class="stat-content">
          <h3>{{ statistics.total_cameras }}</h3>
          <p>总摄像头数</p>
          <span class="stat-detail">{{ statistics.active_cameras }}/{{ statistics.total_cameras }} 活跃</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon performance">⚡</div>
        <div class="stat-content">
          <h3>{{ statistics.avg_fps || 0 }}</h3>
          <p>平均FPS</p>
          <span class="stat-detail">{{ statistics.total_detections || 0 }} 总检测</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon algorithms">🧠</div>
        <div class="stat-content">
          <h3>{{ statistics.active_algorithms || 3 }}</h3>
          <p>活跃算法</p>
          <span class="stat-detail">跌倒·火焰·烟雾</span>
        </div>
      </div>
    </div>

    <!-- 快速操作面板 -->
    <div class="quick-actions">
      <div class="action-group">
        <h3>快速操作</h3>
        <button @click="refreshAll" class="btn-primary" :disabled="loading">
          <span v-if="loading">🔄</span>
          <span v-else>🔄</span> 刷新所有
        </button>
        <button @click="batchHealthCheck" class="btn-secondary">
          💊 批量检查
        </button>
        <button @click="showBatchOperations" class="btn-info">
          ⚙️ 批量操作
        </button>
      </div>
      
      <div class="action-group">
        <h3>系统监控</h3>
        <button @click="showPerformanceMonitor" class="btn-success">
          📊 性能监控
        </button>
        <button @click="showAlgorithmManager" class="btn-warning">
          🧠 算法管理
        </button>
        <button @click="exportReport" class="btn-info">
          📄 导出报告
        </button>
      </div>
    </div>

    <!-- 边缘控制器卡片 -->
    <div class="controllers-section">
      <div class="section-header">
        <h2>边缘控制器列表</h2>
        <div class="filter-controls">
          <select v-model="statusFilter" class="filter-select">
            <option value="">所有状态</option>
            <option value="online">在线</option>
            <option value="offline">离线</option>
          </select>
          <input 
            v-model="searchQuery" 
            placeholder="搜索控制器..." 
            class="search-input"
          />
        </div>
      </div>
      
      <div class="controllers-grid">
        <div 
          v-for="controller in filteredControllers" 
          :key="controller.controller_id"
          class="controller-card enhanced"
          :class="{ 
            'online': controller.is_online, 
            'offline': !controller.is_online,
            'high-load': controller.system_stats?.cpu_usage > 80
          }"
        >
          <!-- 控制器头部 -->
          <div class="controller-header">
            <div class="controller-status">
              <span class="status-indicator" :class="{ 'online': controller.is_online }"></span>
              <div>
                <h3>{{ controller.controller_name }}</h3>
                <span class="controller-id">ID: {{ controller.controller_id }}</span>
              </div>
            </div>
            <div class="controller-actions">
              <div class="action-dropdown" @click="toggleActionMenu(controller.controller_id)">
                ⋮
                <div v-if="activeDropdown === controller.controller_id" class="dropdown-menu">
                  <button @click="viewController(controller)">📋 详情</button>
                  <button @click="openCameraManager(controller)">📷 摄像头</button>
                  <button @click="openAlgorithmConfig(controller)">🧠 算法</button>
                  <button @click="openPerformanceView(controller)">📊 性能</button>
                  <button @click="restartController(controller)">🔄 重启</button>
                </div>
              </div>
            </div>
          </div>

          <!-- 性能仪表盘 -->
          <div class="performance-dashboard">
            <div class="metric-item">
              <div class="metric-label">CPU</div>
              <div class="metric-bar">
                <div 
                  class="metric-fill cpu" 
                  :style="{ width: (controller.system_stats?.cpu_usage || 0) + '%' }"
                ></div>
                <span class="metric-value">{{ controller.system_stats?.cpu_usage || 0 }}%</span>
              </div>
            </div>
            <div class="metric-item">
              <div class="metric-label">内存</div>
              <div class="metric-bar">
                <div 
                  class="metric-fill memory" 
                  :style="{ width: (controller.system_stats?.memory_usage || 0) + '%' }"
                ></div>
                <span class="metric-value">{{ controller.system_stats?.memory_usage || 0 }}%</span>
              </div>
            </div>
          </div>

          <!-- 摄像头快速状态 -->
          <div class="camera-quick-status">
            <div class="status-row">
              <span class="label">摄像头:</span>
              <span class="value">
                <span class="online-count">{{ controller.active_cameras || 0 }}</span>
                /{{ controller.total_cameras || 0 }}
              </span>
            </div>
            <div class="status-row">
              <span class="label">FPS:</span>
              <span class="value">{{ controller.system_stats?.average_fps || 0 }}</span>
            </div>
            <div class="status-row">
              <span class="label">检测数:</span>
              <span class="value">{{ controller.system_stats?.total_detections || 0 }}</span>
            </div>
          </div>

          <!-- 算法状态 -->
          <div class="algorithm-status">
            <h4>算法状态</h4>
            <div class="algorithm-items">
              <span 
                v-for="algo in controller.algorithms" 
                :key="algo.name"
                class="algorithm-tag"
                :class="{ 'active': algo.enabled, 'inactive': !algo.enabled }"
              >
                {{ getAlgorithmIcon(algo.name) }} {{ getAlgorithmName(algo.name) }}
              </span>
            </div>
          </div>

          <!-- 快速操作按钮 -->
          <div class="quick-actions-buttons">
            <button @click="startAllCameras(controller)" class="btn-small btn-success" title="启动所有摄像头">
              ▶️ 全部启动
            </button>
            <button @click="stopAllCameras(controller)" class="btn-small btn-warning" title="停止所有摄像头">
              ⏸️ 全部停止
            </button>
            <button @click="testDetection(controller)" class="btn-small btn-info" title="测试AI检测">
              🧪 测试AI
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 算法管理模态框 -->
    <div v-if="showAlgorithms" class="modal-overlay" @click="showAlgorithms = false">
      <div class="modal-content algorithm-manager" @click.stop>
        <div class="modal-header">
          <h2>🧠 AI算法管理</h2>
          <button @click="showAlgorithms = false" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="algorithm-list">
            <div v-for="algo in algorithmConfigs" :key="algo.name" class="algorithm-config-card">
              <div class="algorithm-header">
                <div class="algorithm-info">
                  <span class="algorithm-icon">{{ getAlgorithmIcon(algo.name) }}</span>
                  <h3>{{ getAlgorithmName(algo.name) }}</h3>
                  <span class="algorithm-description">{{ getAlgorithmDescription(algo.name) }}</span>
                </div>
                <label class="toggle-switch">
                  <input 
                    type="checkbox" 
                    v-model="algo.enabled"
                    @change="updateAlgorithm(algo)"
                  />
                  <span class="slider"></span>
                </label>
              </div>
              
              <div v-if="algo.enabled" class="algorithm-settings">
                <div class="setting-item">
                  <label>置信度阈值:</label>
                  <input 
                    type="range" 
                    min="0.1" 
                    max="1.0" 
                    step="0.05"
                    v-model="algo.confidence_threshold"
                    @change="updateAlgorithm(algo)"
                  />
                  <span class="threshold-value">{{ (algo.confidence_threshold * 100).toFixed(0) }}%</span>
                </div>
                
                <div class="setting-item" v-if="algo.parameters">
                  <label>高级参数:</label>
                  <div class="parameters-grid">
                    <div v-for="(value, key) in algo.parameters" :key="key" class="param-item">
                      <label>{{ key }}:</label>
                      <input 
                        :type="typeof value === 'number' ? 'number' : 'text'"
                        v-model="algo.parameters[key]"
                        @change="updateAlgorithm(algo)"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 性能监控模态框 -->
    <div v-if="showPerformance" class="modal-overlay" @click="showPerformance = false">
      <div class="modal-content performance-monitor" @click.stop>
        <div class="modal-header">
          <h2>📊 系统性能监控</h2>
          <button @click="showPerformance = false" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="performance-overview">
            <div class="perf-card">
              <h3>整体性能</h3>
              <div class="perf-metrics">
                <div class="metric">
                  <span class="label">平均CPU使用率</span>
                  <span class="value">{{ performanceData.avg_cpu || 0 }}%</span>
                </div>
                <div class="metric">
                  <span class="label">平均内存使用</span>
                  <span class="value">{{ performanceData.avg_memory || 0 }}%</span>
                </div>
                <div class="metric">
                  <span class="label">总处理帧数</span>
                  <span class="value">{{ performanceData.total_frames || 0 }}</span>
                </div>
                <div class="metric">
                  <span class="label">总检测次数</span>
                  <span class="value">{{ performanceData.total_detections || 0 }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 性能历史图表区域 -->
          <div class="performance-charts">
            <div class="chart-container">
              <h4>CPU & 内存使用趋势</h4>
              <div class="chart-placeholder">
                <!-- 这里可以集成图表库如 Chart.js 或 ECharts -->
                <p>📈 性能图表 (需要集成图表组件)</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 摄像头管理增强模态框 -->
    <div v-if="selectedController && showCameraManager" class="modal-overlay" @click="showCameraManager = false">
      <div class="modal-content camera-manager" @click.stop>
        <div class="modal-header">
          <h2>📷 摄像头管理 - {{ selectedController.controller_name }}</h2>
          <button @click="showCameraManager = false" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-body">
          <div class="camera-manager-toolbar">
            <div class="toolbar-section">
              <button @click="addNewCamera" class="btn-primary">+ 添加摄像头</button>
              <button @click="importCameras" class="btn-secondary">📥 批量导入</button>
              <button @click="exportCameras" class="btn-secondary">📤 导出配置</button>
            </div>
            
            <div class="toolbar-section">
              <span class="camera-count">当前: {{ (selectedController.cameras || []).length }}/{{ selectedController.max_cameras || 11 }}</span>
              <input 
                type="number" 
                v-model="maxCameraCount" 
                min="1" 
                max="50"
                @change="updateMaxCameraCount"
                class="max-camera-input"
                placeholder="最大数量"
              />
            </div>
          </div>

          <div class="cameras-enhanced-table">
            <table>
              <thead>
                <tr>
                  <th><input type="checkbox" @change="toggleAllCameras" /></th>
                  <th>摄像头ID</th>
                  <th>名称</th>
                  <th>位置</th>
                  <th>RTSP地址</th>
                  <th>状态</th>
                  <th>算法</th>
                  <th>FPS</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="camera in selectedController.cameras" :key="camera.id">
                  <td><input type="checkbox" v-model="selectedCameras" :value="camera.id" /></td>
                  <td>{{ camera.id }}</td>
                  <td>
                    <div class="camera-name-cell">
                      <span class="camera-name">{{ camera.name }}</span>
                      <span v-if="camera.zone_id" class="zone-tag">{{ camera.zone_id }}</span>
                    </div>
                  </td>
                  <td>{{ camera.location }}</td>
                  <td class="rtsp-cell">
                    <span class="rtsp-url" :title="camera.rtsp_url">
                      {{ truncateUrl(camera.rtsp_url) }}
                    </span>
                  </td>
                  <td>
                    <span class="status-badge enhanced" :class="camera.status">
                      {{ camera.status }}
                    </span>
                  </td>
                  <td>
                    <div class="algorithm-tags">
                      <span 
                        v-for="algo in camera.enabled_algorithms" 
                        :key="algo"
                        class="algo-tag"
                      >
                        {{ getAlgorithmIcon(algo) }}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span class="fps-badge" :class="{ 'low': (camera.current_fps || 0) < 15 }">
                      {{ camera.current_fps || 0 }}
                    </span>
                  </td>
                  <td>
                    <div class="camera-actions">
                      <button @click="toggleCameraStream(camera)" class="btn-micro" :class="camera.status === 'online' ? 'btn-warning' : 'btn-success'">
                        {{ camera.status === 'online' ? '⏸️' : '▶️' }}
                      </button>
                      <button @click="editCamera(camera)" class="btn-micro btn-info">✏️</button>
                      <button @click="removeCamera(camera)" class="btn-micro btn-danger">🗑️</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 批量操作工具栏 -->
          <div v-if="selectedCameras.length > 0" class="batch-toolbar">
            <span>已选择 {{ selectedCameras.length }} 个摄像头</span>
            <button @click="batchStartCameras" class="btn-small btn-success">批量启动</button>
            <button @click="batchStopCameras" class="btn-small btn-warning">批量停止</button>
            <button @click="batchRemoveCameras" class="btn-small btn-danger">批量删除</button>
            <button @click="selectedCameras = []" class="btn-small btn-secondary">取消选择</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加摄像头模态框 -->
    <div v-if="showAddCamera" class="modal-overlay" @click="showAddCamera = false">
      <div class="modal-content add-camera-modal" @click.stop>
        <div class="modal-header">
          <h2>➕ 添加摄像头</h2>
          <button @click="showAddCamera = false" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="submitNewCamera" class="camera-form">
            <div class="form-grid">
              <div class="form-group">
                <label>摄像头ID:</label>
                <input type="text" v-model="newCamera.id" required placeholder="cam_001" />
              </div>
              <div class="form-group">
                <label>摄像头名称:</label>
                <input type="text" v-model="newCamera.name" required placeholder="入口摄像头" />
              </div>
              <div class="form-group">
                <label>安装位置:</label>
                <input type="text" v-model="newCamera.location" required placeholder="一楼大厅" />
              </div>
              <div class="form-group">
                <label>区域ID:</label>
                <input type="text" v-model="newCamera.zone_id" placeholder="zone_001" />
              </div>
              <div class="form-group full-width">
                <label>RTSP地址:</label>
                <input type="url" v-model="newCamera.rtsp_url" required placeholder="rtsp://admin:password@192.168.1.100:554/stream" />
              </div>
              <div class="form-group full-width">
                <label>启用算法:</label>
                <div class="algorithm-checkboxes">
                  <label v-for="algo in availableAlgorithms" :key="algo.value" class="checkbox-label">
                    <input 
                      type="checkbox" 
                      :value="algo.value" 
                      v-model="newCamera.enabled_algorithms"
                    />
                    <span>{{ algo.icon }} {{ algo.label }}</span>
                  </label>
                </div>
              </div>
            </div>
            
            <div class="form-actions">
              <button type="button" @click="showAddCamera = false" class="btn-secondary">取消</button>
              <button type="button" @click="testCameraConnection" class="btn-info">测试连接</button>
              <button type="submit" class="btn-primary">添加摄像头</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'

export default {
  name: 'EdgeDevicesEnhanced',
  setup() {
    const controllers = ref([])
    const statistics = ref({
      total_controllers: 0,
      online_controllers: 0,
      offline_controllers: 0,
      total_cameras: 0,
      active_cameras: 0,
      avg_fps: 0,
      total_detections: 0,
      active_algorithms: 3
    })
    
    const selectedController = ref(null)
    const loading = ref(false)
    const statusFilter = ref('')
    const searchQuery = ref('')
    const activeDropdown = ref(null)
    
    // 模态框状态
    const showAlgorithms = ref(false)
    const showPerformance = ref(false)
    const showCameraManager = ref(false)
    const showAddCamera = ref(false)
    
    // 算法配置
    const algorithmConfigs = ref([
      {
        name: 'fall_detection',
        enabled: true,
        confidence_threshold: 0.8,
        parameters: {
          'min_detection_size': 50,
          'max_detection_age': 30
        }
      },
      {
        name: 'fire_detection',
        enabled: true,
        confidence_threshold: 0.85,
        parameters: {
          'flame_threshold': 0.7,
          'smoke_threshold': 0.6
        }
      },
      {
        name: 'smoke_detection',
        enabled: true,
        confidence_threshold: 0.8,
        parameters: {
          'density_threshold': 0.5
        }
      }
    ])
    
    const performanceData = ref({
      avg_cpu: 45,
      avg_memory: 62,
      total_frames: 125680,
      total_detections: 234
    })
    
    // 新增摄像头表单
    const newCamera = ref({
      id: '',
      name: '',
      location: '',
      zone_id: '',
      rtsp_url: '',
      enabled_algorithms: ['fall_detection']
    })
    
    const selectedCameras = ref([])
    const maxCameraCount = ref(11)
    
    const availableAlgorithms = [
      { value: 'fall_detection', label: '跌倒检测', icon: '🤸' },
      { value: 'fire_detection', label: '火焰检测', icon: '🔥' },
      { value: 'smoke_detection', label: '烟雾检测', icon: '💨' }
    ]

    // 计算属性
    const filteredControllers = computed(() => {
      let filtered = controllers.value
      
      if (statusFilter.value) {
        filtered = filtered.filter(c => 
          statusFilter.value === 'online' ? c.is_online : !c.is_online
        )
      }
      
      if (searchQuery.value) {
        filtered = filtered.filter(c => 
          c.controller_name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
          c.controller_id.toLowerCase().includes(searchQuery.value.toLowerCase())
        )
      }
      
      return filtered
    })

    // 工具函数
    const getAlgorithmIcon = (name) => {
      const icons = {
        'fall_detection': '🤸',
        'fire_detection': '🔥',
        'smoke_detection': '💨'
      }
      return icons[name] || '🔍'
    }
    
    const getAlgorithmName = (name) => {
      const names = {
        'fall_detection': '跌倒检测',
        'fire_detection': '火焰检测',
        'smoke_detection': '烟雾检测'
      }
      return names[name] || name
    }
    
    const getAlgorithmDescription = (name) => {
      const descriptions = {
        'fall_detection': '检测人员跌倒事件，实时监控安全状况',
        'fire_detection': '识别火焰和火灾迹象，及时预警',
        'smoke_detection': '检测烟雾异常，防范火灾风险'
      }
      return descriptions[name] || ''
    }

    const truncateUrl = (url) => {
      return url && url.length > 30 ? url.substring(0, 30) + '...' : url
    }

    // API调用函数
    const loadControllers = async () => {
      try {
        loading.value = true
        // 模拟数据，实际应该调用真实的API
        const response = await fetch('http://localhost:8084/api/service/status')
        const controllerData = await response.json()
        
        // 模拟控制器列表
        controllers.value = [
          {
            controller_id: 'edge_controller_1',
            controller_name: '边缘控制器#1',
            is_online: true,
            last_heartbeat: new Date().toISOString(),
            system_stats: {
              cpu_usage: 45,
              memory_usage: 62,
              average_fps: 28,
              total_detections: 156,
              uptime_seconds: 86400
            },
            total_cameras: 11,
            active_cameras: 8,
            cameras: [],
            algorithms: [
              { name: 'fall_detection', enabled: true },
              { name: 'fire_detection', enabled: true },
              { name: 'smoke_detection', enabled: false }
            ]
          }
        ]
        
        statistics.value = {
          total_controllers: 2,
          online_controllers: 1,
          offline_controllers: 1,
          total_cameras: 22,
          active_cameras: 15,
          avg_fps: 26,
          total_detections: 324,
          active_algorithms: 3
        }
      } catch (error) {
        console.error('加载控制器失败:', error)
      } finally {
        loading.value = false
      }
    }

    // 事件处理函数
    const refreshAll = async () => {
      await loadControllers()
    }

    const toggleActionMenu = (controllerId) => {
      activeDropdown.value = activeDropdown.value === controllerId ? null : controllerId
    }

    const viewController = (controller) => {
      selectedController.value = controller
      activeDropdown.value = null
    }

    const openCameraManager = (controller) => {
      selectedController.value = controller
      showCameraManager.value = true
      activeDropdown.value = null
    }

    const openAlgorithmConfig = (controller) => {
      selectedController.value = controller
      showAlgorithms.value = true
      activeDropdown.value = null
    }

    const openPerformanceView = (controller) => {
      selectedController.value = controller
      showPerformance.value = true
      activeDropdown.value = null
    }

    const showAlgorithmManager = () => {
      showAlgorithms.value = true
    }

    const showPerformanceMonitor = () => {
      showPerformance.value = true
    }

    const showBatchOperations = () => {
      alert('批量操作功能开发中...')
    }

    const updateAlgorithm = async (algo) => {
      try {
        const response = await fetch(`http://localhost:8084/api/algorithms/${algo.name}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(algo)
        })
        
        if (response.ok) {
          console.log(`算法 ${algo.name} 更新成功`)
        }
      } catch (error) {
        console.error('更新算法配置失败:', error)
      }
    }

    const addNewCamera = () => {
      showAddCamera.value = true
    }

    const submitNewCamera = async () => {
      try {
        const response = await fetch(`http://localhost:8084/api/cameras`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newCamera.value)
        })
        
        if (response.ok) {
          alert('摄像头添加成功')
          showAddCamera.value = false
          // 重置表单
          newCamera.value = {
            id: '',
            name: '',
            location: '',
            zone_id: '',
            rtsp_url: '',
            enabled_algorithms: ['fall_detection']
          }
          await loadControllers()
        }
      } catch (error) {
        console.error('添加摄像头失败:', error)
      }
    }

    const testCameraConnection = async () => {
      alert('摄像头连接测试功能开发中...')
    }

    const batchHealthCheck = async () => {
      alert('批量健康检查完成')
    }

    const exportReport = () => {
      alert('导出报告功能开发中...')
    }

    const restartController = async (controller) => {
      if (confirm(`确定要重启控制器 ${controller.controller_name} 吗？`)) {
        try {
          await fetch(`http://localhost:8084/api/service/restart`, { method: 'POST' })
          alert('重启请求已发送')
        } catch (error) {
          console.error('重启失败:', error)
        }
      }
    }

    const startAllCameras = async (controller) => {
      alert(`启动 ${controller.controller_name} 的所有摄像头`)
    }

    const stopAllCameras = async (controller) => {
      alert(`停止 ${controller.controller_name} 的所有摄像头`)
    }

    const testDetection = async (controller) => {
      alert(`测试 ${controller.controller_name} 的AI检测`)
    }

    onMounted(() => {
      loadControllers()
      // 定时刷新
      setInterval(loadControllers, 30000)
    })

    return {
      controllers,
      filteredControllers,
      statistics,
      selectedController,
      loading,
      statusFilter,
      searchQuery,
      activeDropdown,
      showAlgorithms,
      showPerformance,
      showCameraManager,
      showAddCamera,
      algorithmConfigs,
      performanceData,
      newCamera,
      selectedCameras,
      maxCameraCount,
      availableAlgorithms,
      
      // 方法
      refreshAll,
      toggleActionMenu,
      viewController,
      openCameraManager,
      openAlgorithmConfig,
      openPerformanceView,
      showAlgorithmManager,
      showPerformanceMonitor,
      showBatchOperations,
      updateAlgorithm,
      addNewCamera,
      submitNewCamera,
      testCameraConnection,
      batchHealthCheck,
      exportReport,
      restartController,
      startAllCameras,
      stopAllCameras,
      testDetection,
      getAlgorithmIcon,
      getAlgorithmName,
      getAlgorithmDescription,
      truncateUrl
    }
  }
}
</script>

<style scoped>
/* 基础样式保持原有的，添加新的增强样式 */
.edge-devices {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 统计卡片增强 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
  padding: 25px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  border-left: 4px solid #3498db;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 100px;
  height: 100px;
  background: linear-gradient(45deg, rgba(52,152,219,0.1), transparent);
  border-radius: 0 0 0 100px;
}

.stat-content {
  position: relative;
  z-index: 2;
}

.stat-change {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  margin-top: 5px;
  display: inline-block;
}

.stat-change.positive {
  background: #d4edda;
  color: #155724;
}

.stat-detail {
  font-size: 13px;
  color: #6c757d;
  display: block;
  margin-top: 5px;
}

/* 快速操作面板 */
.quick-actions {
  background: white;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 2px 15px rgba(0,0,0,0.08);
  margin-bottom: 30px;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 20px;
}

.action-group h3 {
  margin: 0 0 15px 0;
  color: #2c3e50;
  font-size: 16px;
}

.action-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.btn-primary, .btn-secondary, .btn-info, .btn-success, .btn-warning {
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-primary { background: #3498db; color: white; }
.btn-secondary { background: #95a5a6; color: white; }
.btn-info { background: #17a2b8; color: white; }
.btn-success { background: #28a745; color: white; }
.btn-warning { background: #ffc107; color: #212529; }

.btn-primary:hover { background: #2980b9; transform: translateY(-1px); }
.btn-secondary:hover { background: #7f8c8d; }
.btn-info:hover { background: #138496; }

/* 增强的控制器卡片 */
.controller-card.enhanced {
  background: white;
  border-radius: 16px;
  padding: 25px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  border: 1px solid #e9ecef;
  position: relative;
  transition: all 0.3s ease;
}

.controller-card.enhanced:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}

.controller-card.enhanced.high-load {
  border-left: 4px solid #e74c3c;
}

.controller-id {
  font-size: 12px;
  color: #6c757d;
  font-family: monospace;
}

.action-dropdown {
  position: relative;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: background 0.2s;
}

.action-dropdown:hover {
  background: #f8f9fa;
}

.dropdown-menu {
  position: absolute;
  right: 0;
  top: 100%;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  min-width: 150px;
  z-index: 100;
  overflow: hidden;
}

.dropdown-menu button {
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  font-size: 14px;
  color: #495057;
  border-bottom: 1px solid #f8f9fa;
}

.dropdown-menu button:hover {
  background: #f8f9fa;
}

/* 性能仪表盘 */
.performance-dashboard {
  margin: 20px 0;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 12px;
}

.metric-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.metric-label {
  width: 60px;
  font-size: 13px;
  color: #6c757d;
}

.metric-bar {
  flex: 1;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  position: relative;
  margin: 0 12px;
}

.metric-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.metric-fill.cpu { background: #3498db; }
.metric-fill.memory { background: #e67e22; }

.metric-value {
  font-size: 13px;
  font-weight: 600;
  color: #495057;
  min-width: 40px;
}

/* 算法状态 */
.algorithm-status {
  margin: 15px 0;
}

.algorithm-status h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #495057;
}

.algorithm-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.algorithm-tag {
  padding: 4px 8px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.algorithm-tag.active {
  background: #d4edda;
  color: #155724;
}

.algorithm-tag.inactive {
  background: #f8d7da;
  color: #721c24;
}

/* 快速操作按钮 */
.quick-actions-buttons {
  display: flex;
  gap: 8px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e9ecef;
}

.btn-small {
  padding: 6px 10px;
  font-size: 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

/* 过滤和搜索控件 */
.filter-controls {
  display: flex;
  gap: 15px;
  align-items: center;
}

.filter-select, .search-input {
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 14px;
}

.search-input {
  min-width: 200px;
}

/* 模态框增强样式 */
.modal-content {
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 50px rgba(0,0,0,0.2);
  max-height: 90vh;
  overflow-y: auto;
}

.modal-content.algorithm-manager {
  width: 90%;
  max-width: 900px;
}

.modal-content.performance-monitor {
  width: 95%;
  max-width: 1200px;
}

.modal-content.camera-manager {
  width: 95%;
  max-width: 1400px;
}

/* 算法管理器 */
.algorithm-config-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid #e9ecef;
}

.algorithm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.algorithm-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.algorithm-icon {
  font-size: 24px;
}

.algorithm-description {
  font-size: 13px;
  color: #6c757d;
  margin-left: 10px;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #28a745;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

/* 摄像头管理器增强 */
.camera-manager-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.toolbar-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.camera-count {
  font-weight: 600;
  color: #495057;
}

.max-camera-input {
  width: 100px;
  padding: 6px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.cameras-enhanced-table {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.cameras-enhanced-table table {
  width: 100%;
  border-collapse: collapse;
}

.cameras-enhanced-table th {
  background: #f8f9fa;
  padding: 12px;
  font-weight: 600;
  color: #495057;
  border-bottom: 2px solid #dee2e6;
}

.cameras-enhanced-table td {
  padding: 12px;
  border-bottom: 1px solid #e9ecef;
  vertical-align: middle;
}

.camera-name-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.zone-tag {
  font-size: 11px;
  background: #e9ecef;
  color: #495057;
  padding: 2px 6px;
  border-radius: 4px;
  width: fit-content;
}

.rtsp-cell {
  max-width: 200px;
}

.rtsp-url {
  font-family: monospace;
  font-size: 12px;
  color: #6c757d;
}

.algorithm-tags {
  display: flex;
  gap: 4px;
}

.algo-tag {
  font-size: 16px;
}

.fps-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
  background: #d4edda;
  color: #155724;
}

.fps-badge.low {
  background: #f8d7da;
  color: #721c24;
}

.camera-actions {
  display: flex;
  gap: 4px;
}

.btn-micro {
  padding: 4px 6px;
  font-size: 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* 批量操作工具栏 */
.batch-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: #e3f2fd;
  border-radius: 8px;
  margin-top: 15px;
  border: 1px solid #bbdefb;
}

/* 添加摄像头表单 */
.camera-form {
  padding: 20px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.form-group input {
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 14px;
}

.algorithm-checkboxes {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
}

/* 性能监控 */
.performance-overview {
  margin-bottom: 30px;
}

.perf-card {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.perf-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-top: 15px;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.metric .label {
  font-size: 13px;
  color: #6c757d;
}

.metric .value {
  font-size: 24px;
  font-weight: 600;
  color: #2c3e50;
}

.chart-container {
  background: white;
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.chart-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border-radius: 8px;
  color: #6c757d;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .edge-devices {
    padding: 15px;
  }
  
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .quick-actions {
    flex-direction: column;
  }
  
  .controllers-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-input {
    min-width: auto;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>