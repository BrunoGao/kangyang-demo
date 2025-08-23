<template>
  <div class="edge-devices-dashboard">
    <div class="page-header">
      <h1>边缘控制器性能监控</h1>
      <p>实时监控边缘设备的GPU、CPU、IO、网络、温度和磁盘状态</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card cpu">
        <div class="stat-icon">💻</div>
        <div class="stat-content">
          <h3>{{ systemMetrics.cpu?.usage_percent || 0 }}%</h3>
          <p>CPU使用率</p>
          <small>{{ systemMetrics.cpu?.count_logical || 0 }}核心</small>
        </div>
      </div>
      
      <div class="stat-card memory">
        <div class="stat-icon">💾</div>
        <div class="stat-content">
          <h3>{{ Math.round(systemMetrics.memory?.virtual?.percent || 0) }}%</h3>
          <p>内存使用率</p>
          <small>{{ formatBytes(systemMetrics.memory?.virtual?.used || 0) }} / {{ formatBytes(systemMetrics.memory?.virtual?.total || 0) }}</small>
        </div>
      </div>
      
      <div class="stat-card gpu" v-if="hasGPU">
        <div class="stat-icon">🎮</div>
        <div class="stat-content">
          <h3>{{ getGPUUtilization() }}%</h3>
          <p>GPU使用率</p>
          <small>{{ getGPUTemperature() }}°C</small>
        </div>
      </div>
      
      <div class="stat-card disk">
        <div class="stat-icon">💽</div>
        <div class="stat-content">
          <h3>{{ getDiskUsage() }}%</h3>
          <p>磁盘使用率</p>
          <small>{{ formatBytes(getDiskUsed()) }} / {{ formatBytes(getDiskTotal()) }}</small>
        </div>
      </div>
      
      <div class="stat-card network">
        <div class="stat-icon">🌐</div>
        <div class="stat-content">
          <h3>{{ getNetworkSpeed() }}</h3>
          <p>网络速度</p>
          <small>↑{{ formatSpeed(systemMetrics.network?.io?.bytes_sent_per_sec || 0) }} ↓{{ formatSpeed(systemMetrics.network?.io?.bytes_recv_per_sec || 0) }}</small>
        </div>
      </div>
      
      <div class="stat-card temperature">
        <div class="stat-icon">🌡️</div>
        <div class="stat-content">
          <h3>{{ getSystemTemperature() }}°C</h3>
          <p>系统温度</p>
          <small>{{ getTemperatureStatus() }}</small>
        </div>
      </div>
    </div>

    <!-- 性能图表区域 -->
    <div class="charts-section">
      <div class="section-header">
        <h2>实时性能监控</h2>
        <div class="chart-controls">
          <el-button @click="toggleAutoRefresh" :type="autoRefresh ? 'success' : 'default'" size="small">
            {{ autoRefresh ? '自动刷新开' : '自动刷新关' }}
          </el-button>
          <el-button @click="refreshMetrics" :loading="loading" size="small">刷新数据</el-button>
          <el-select v-model="refreshInterval" size="small" style="width: 100px;">
            <el-option label="1秒" :value="1000"></el-option>
            <el-option label="3秒" :value="3000"></el-option>
            <el-option label="5秒" :value="5000"></el-option>
            <el-option label="10秒" :value="10000"></el-option>
          </el-select>
        </div>
      </div>

      <!-- 图表网格 -->
      <div class="charts-grid">
        <!-- CPU使用率图表 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>CPU使用率</h3>
            <div class="chart-info">
              <span class="current-value">{{ systemMetrics.cpu?.usage_percent || 0 }}%</span>
            </div>
          </div>
          <div ref="cpuChart" class="chart-container"></div>
        </div>

        <!-- 内存使用率图表 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>内存使用率</h3>
            <div class="chart-info">
              <span class="current-value">{{ Math.round(systemMetrics.memory?.virtual?.percent || 0) }}%</span>
            </div>
          </div>
          <div ref="memoryChart" class="chart-container"></div>
        </div>

        <!-- GPU使用率图表 -->
        <div class="chart-card" v-if="hasGPU">
          <div class="chart-header">
            <h3>GPU使用率</h3>
            <div class="chart-info">
              <span class="current-value">{{ getGPUUtilization() }}%</span>
            </div>
          </div>
          <div ref="gpuChart" class="chart-container"></div>
        </div>

        <!-- 磁盘IO图表 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>磁盘IO</h3>
            <div class="chart-info">
              <span class="current-value">{{ formatSpeed(systemMetrics.io?.disk?.read_speed_bps || 0) }} / {{ formatSpeed(systemMetrics.io?.disk?.write_speed_bps || 0) }}</span>
            </div>
          </div>
          <div ref="diskIOChart" class="chart-container"></div>
        </div>

        <!-- 网络IO图表 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>网络IO</h3>
            <div class="chart-info">
              <span class="current-value">{{ formatSpeed(systemMetrics.network?.io?.bytes_recv_per_sec || 0) }} / {{ formatSpeed(systemMetrics.network?.io?.bytes_sent_per_sec || 0) }}</span>
            </div>
          </div>
          <div ref="networkIOChart" class="chart-container"></div>
        </div>

        <!-- 温度监控图表 -->
        <div class="chart-card">
          <div class="chart-header">
            <h3>温度监控</h3>
            <div class="chart-info">
              <span class="current-value">{{ getSystemTemperature() }}°C</span>
            </div>
          </div>
          <div ref="temperatureChart" class="chart-container"></div>
        </div>
      </div>
    </div>

    <!-- 详细信息表格 -->
    <div class="details-section">
      <div class="section-header">
        <h2>系统详细信息</h2>
      </div>
      
      <!-- 详细信息标签页 -->
      <el-tabs v-model="activeTab">
        <el-tab-pane label="CPU信息" name="cpu">
          <div class="detail-grid">
            <div class="detail-item">
              <label>逻辑核心数:</label>
              <span>{{ systemMetrics.cpu?.count_logical || 'N/A' }}</span>
            </div>
            <div class="detail-item">
              <label>物理核心数:</label>
              <span>{{ systemMetrics.cpu?.count_physical || 'N/A' }}</span>
            </div>
            <div class="detail-item">
              <label>当前频率:</label>
              <span>{{ systemMetrics.cpu?.frequency?.current || 'N/A' }} MHz</span>
            </div>
            <div class="detail-item">
              <label>负载平均值 (1/5/15min):</label>
              <span>{{ systemMetrics.load_average?.join(' / ') || 'N/A' }}</span>
            </div>
          </div>
          
          <!-- CPU按核心使用率 -->
          <div v-if="systemMetrics.cpu?.per_core" class="core-usage">
            <h4>各核心使用率</h4>
            <div class="core-grid">
              <div v-for="(usage, index) in systemMetrics.cpu.per_core" :key="index" class="core-item">
                <span class="core-label">Core {{ index }}</span>
                <el-progress :percentage="usage" :stroke-width="12" :text-inside="true" :show-text="false"></el-progress>
                <span class="core-value">{{ usage }}%</span>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="内存信息" name="memory">
          <div class="memory-details">
            <div class="memory-section">
              <h4>虚拟内存</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>总计:</label>
                  <span>{{ formatBytes(systemMetrics.memory?.virtual?.total || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>已用:</label>
                  <span>{{ formatBytes(systemMetrics.memory?.virtual?.used || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>可用:</label>
                  <span>{{ formatBytes(systemMetrics.memory?.virtual?.available || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>空闲:</label>
                  <span>{{ formatBytes(systemMetrics.memory?.virtual?.free || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>缓存:</label>
                  <span>{{ formatBytes(systemMetrics.memory?.virtual?.cached || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>缓冲区:</label>
                  <span>{{ formatBytes(systemMetrics.memory?.virtual?.buffers || 0) }}</span>
                </div>
              </div>
            </div>

            <div class="memory-section" v-if="systemMetrics.memory?.swap?.total > 0">
              <h4>交换内存</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>总计:</label>
                  <span>{{ formatBytes(systemMetrics.memory?.swap?.total || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>已用:</label>
                  <span>{{ formatBytes(systemMetrics.memory?.swap?.used || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>使用率:</label>
                  <span>{{ systemMetrics.memory?.swap?.percent || 0 }}%</span>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="GPU信息" name="gpu" v-if="hasGPU">
          <div v-for="(gpu, key) in systemMetrics.gpu" :key="key" class="gpu-section">
            <h4>{{ gpu.name || key }}</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <label>GPU使用率:</label>
                <span>{{ gpu.utilization?.gpu || 0 }}%</span>
              </div>
              <div class="detail-item">
                <label>显存使用率:</label>
                <span>{{ gpu.utilization?.memory || 0 }}%</span>
              </div>
              <div class="detail-item">
                <label>显存总量:</label>
                <span>{{ formatBytes(gpu.memory?.total || 0) }}</span>
              </div>
              <div class="detail-item">
                <label>显存已用:</label>
                <span>{{ formatBytes(gpu.memory?.used || 0) }}</span>
              </div>
              <div class="detail-item">
                <label>温度:</label>
                <span>{{ gpu.temperature || 'N/A' }}°C</span>
              </div>
              <div class="detail-item">
                <label>功耗:</label>
                <span>{{ gpu.power?.draw || 'N/A' }}W</span>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="磁盘信息" name="disk">
          <div class="disk-details">
            <div v-if="systemMetrics.disk?.usage" class="disk-usage">
              <h4>磁盘使用情况</h4>
              <div v-for="(disk, device) in systemMetrics.disk.usage" :key="device" class="disk-item">
                <div class="disk-header">
                  <strong>{{ device }}</strong>
                  <span class="mount-point">{{ disk.mountpoint }}</span>
                  <span class="fs-type">{{ disk.fstype }}</span>
                </div>
                <div class="disk-progress">
                  <el-progress :percentage="disk.percent" :stroke-width="20" :text-inside="true" 
                              :color="disk.percent > 90 ? '#f56c6c' : disk.percent > 70 ? '#e6a23c' : '#67c23a'">
                  </el-progress>
                </div>
                <div class="disk-stats">
                  <span>{{ formatBytes(disk.used) }} / {{ formatBytes(disk.total) }}</span>
                  <span>空闲: {{ formatBytes(disk.free) }}</span>
                </div>
              </div>
            </div>

            <div v-if="systemMetrics.io?.disk" class="disk-io">
              <h4>磁盘IO统计</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>读取速度:</label>
                  <span>{{ formatSpeed(systemMetrics.io.disk.read_speed_bps || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>写入速度:</label>
                  <span>{{ formatSpeed(systemMetrics.io.disk.write_speed_bps || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>读取总量:</label>
                  <span>{{ formatBytes(systemMetrics.io.disk.read_bytes || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>写入总量:</label>
                  <span>{{ formatBytes(systemMetrics.io.disk.write_bytes || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>读取次数:</label>
                  <span>{{ (systemMetrics.io.disk.read_count || 0).toLocaleString() }}</span>
                </div>
                <div class="detail-item">
                  <label>写入次数:</label>
                  <span>{{ (systemMetrics.io.disk.write_count || 0).toLocaleString() }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="网络信息" name="network">
          <div class="network-details">
            <div v-if="systemMetrics.network?.io" class="network-io">
              <h4>网络IO统计</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>下载速度:</label>
                  <span>{{ formatSpeed(systemMetrics.network.io.bytes_recv_per_sec || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>上传速度:</label>
                  <span>{{ formatSpeed(systemMetrics.network.io.bytes_sent_per_sec || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>总下载量:</label>
                  <span>{{ formatBytes(systemMetrics.network.io.bytes_recv || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>总上传量:</label>
                  <span>{{ formatBytes(systemMetrics.network.io.bytes_sent || 0) }}</span>
                </div>
                <div class="detail-item">
                  <label>连接数:</label>
                  <span>{{ systemMetrics.network?.connections || 0 }}</span>
                </div>
              </div>
            </div>

            <div v-if="systemMetrics.network?.interfaces" class="network-interfaces">
              <h4>网络接口</h4>
              <div v-for="(interface_info, name) in systemMetrics.network.interfaces" :key="name" class="interface-item">
                <div class="interface-header">
                  <strong>{{ name }}</strong>
                  <el-tag :type="interface_info.is_up ? 'success' : 'danger'" size="small">
                    {{ interface_info.is_up ? '启用' : '禁用' }}
                  </el-tag>
                </div>
                <div class="interface-details">
                  <div class="detail-item" v-if="interface_info.speed">
                    <label>速度:</label>
                    <span>{{ interface_info.speed }} Mbps</span>
                  </div>
                  <div class="detail-item" v-if="interface_info.mtu">
                    <label>MTU:</label>
                    <span>{{ interface_info.mtu }}</span>
                  </div>
                  <div class="addresses">
                    <div v-for="(addr, idx) in interface_info.addresses" :key="idx" class="address-item">
                      <span class="address">{{ addr.address }}</span>
                      <small class="netmask" v-if="addr.netmask">/ {{ addr.netmask }}</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="温度传感器" name="temperature">
          <div class="temperature-details">
            <div v-for="(sensors, sensorName) in systemMetrics.temperature" :key="sensorName" class="sensor-group" v-if="Array.isArray(sensors)">
              <h4>{{ sensorName }}</h4>
              <div v-for="(sensor, idx) in sensors" :key="idx" class="sensor-item">
                <div class="sensor-header">
                  <span class="sensor-label">{{ sensor.label }}</span>
                  <span class="sensor-temp" :class="getTempClass(sensor.current)">{{ sensor.current }}°C</span>
                </div>
                <div class="sensor-limits" v-if="sensor.high || sensor.critical">
                  <small v-if="sensor.high">警告: {{ sensor.high }}°C</small>
                  <small v-if="sensor.critical" class="critical">危险: {{ sensor.critical }}°C</small>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import * as echarts from 'echarts'

export default {
  name: 'EdgeDevicesWithCharts',
  setup() {
    const systemMetrics = ref({})
    const loading = ref(false)
    const activeTab = ref('cpu')
    const autoRefresh = ref(true)
    const refreshInterval = ref(3000)
    
    // 图表实例
    const charts = ref({})
    
    // 历史数据（用于图表）
    const metricsHistory = ref({
      cpu: [],
      memory: [],
      gpu: [],
      disk_io: [],
      network_io: [],
      temperature: [],
      timestamps: []
    })
    
    let refreshTimer = null
    const maxDataPoints = 50 // 最多保存50个数据点

    // 计算属性
    const hasGPU = computed(() => {
      const gpu = systemMetrics.value.gpu
      return gpu && typeof gpu === 'object' && !gpu.message && !gpu.error
    })

    // 格式化函数
    const formatBytes = (bytes) => {
      if (!bytes) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const formatSpeed = (bps) => {
      if (!bps) return '0 B/s'
      return formatBytes(bps) + '/s'
    }

    // GPU相关函数
    const getGPUUtilization = () => {
      if (!hasGPU.value) return 0
      const gpu = Object.values(systemMetrics.value.gpu)[0]
      return gpu?.utilization?.gpu || 0
    }

    const getGPUTemperature = () => {
      if (!hasGPU.value) return 0
      const gpu = Object.values(systemMetrics.value.gpu)[0]
      return gpu?.temperature || 0
    }

    // 磁盘相关函数
    const getDiskUsage = () => {
      const diskUsage = systemMetrics.value.disk?.usage
      if (!diskUsage) return 0
      const mainDisk = Object.values(diskUsage)[0]
      return Math.round(mainDisk?.percent || 0)
    }

    const getDiskUsed = () => {
      const diskUsage = systemMetrics.value.disk?.usage
      if (!diskUsage) return 0
      const mainDisk = Object.values(diskUsage)[0]
      return mainDisk?.used || 0
    }

    const getDiskTotal = () => {
      const diskUsage = systemMetrics.value.disk?.usage
      if (!diskUsage) return 0
      const mainDisk = Object.values(diskUsage)[0]
      return mainDisk?.total || 0
    }

    // 网络相关函数
    const getNetworkSpeed = () => {
      const recv = systemMetrics.value.network?.io?.bytes_recv_per_sec || 0
      const sent = systemMetrics.value.network?.io?.bytes_sent_per_sec || 0
      const total = recv + sent
      return formatSpeed(total)
    }

    // 温度相关函数
    const getSystemTemperature = () => {
      const temp = systemMetrics.value.temperature
      if (!temp || temp.message || temp.error) return 'N/A'
      
      // 查找第一个有效的温度读数
      for (const sensorGroup of Object.values(temp)) {
        if (Array.isArray(sensorGroup)) {
          for (const sensor of sensorGroup) {
            if (sensor.current && sensor.current > 0) {
              return Math.round(sensor.current)
            }
          }
        }
      }
      return 'N/A'
    }

    const getTemperatureStatus = () => {
      const temp = getSystemTemperature()
      if (temp === 'N/A') return '无传感器'
      if (temp > 80) return '过热'
      if (temp > 60) return '偏高'
      return '正常'
    }

    const getTempClass = (temp) => {
      if (temp > 80) return 'temp-critical'
      if (temp > 60) return 'temp-warning'
      return 'temp-normal'
    }

    // 获取系统指标
    const refreshMetrics = async () => {
      try {
        loading.value = true
        const response = await fetch('/api/performance/metrics')
        const data = await response.json()
        
        if (data.success) {
          systemMetrics.value = data.system_metrics
          
          // 更新历史数据
          updateMetricsHistory()
          
          // 更新图表
          await nextTick()
          updateCharts()
        }
      } catch (error) {
        console.error('获取系统指标失败:', error)
      } finally {
        loading.value = false
      }
    }

    // 更新历史数据
    const updateMetricsHistory = () => {
      const now = new Date()
      
      // 添加新数据点
      metricsHistory.value.timestamps.push(now)
      metricsHistory.value.cpu.push(systemMetrics.value.cpu?.usage_percent || 0)
      metricsHistory.value.memory.push(systemMetrics.value.memory?.virtual?.percent || 0)
      metricsHistory.value.gpu.push(getGPUUtilization())
      metricsHistory.value.disk_io.push({
        read: systemMetrics.value.io?.disk?.read_speed_bps || 0,
        write: systemMetrics.value.io?.disk?.write_speed_bps || 0
      })
      metricsHistory.value.network_io.push({
        recv: systemMetrics.value.network?.io?.bytes_recv_per_sec || 0,
        sent: systemMetrics.value.network?.io?.bytes_sent_per_sec || 0
      })
      metricsHistory.value.temperature.push(getSystemTemperature())
      
      // 限制数据点数量
      Object.keys(metricsHistory.value).forEach(key => {
        if (metricsHistory.value[key].length > maxDataPoints) {
          metricsHistory.value[key] = metricsHistory.value[key].slice(-maxDataPoints)
        }
      })
    }

    // 初始化图表
    const initCharts = () => {
      const chartRefs = ['cpuChart', 'memoryChart', 'gpuChart', 'diskIOChart', 'networkIOChart', 'temperatureChart']
      
      chartRefs.forEach(ref => {
        const element = document.querySelector(`[data-ref="${ref}"]`) || document.getElementsByClassName(ref.replace('Chart', '-chart'))[0]
        if (element) {
          charts.value[ref] = echarts.init(element)
        }
      })
    }

    // 更新图表
    const updateCharts = () => {
      const timestamps = metricsHistory.value.timestamps.map(t => t.toLocaleTimeString())
      
      // CPU图表
      if (charts.value.cpuChart) {
        const option = {
          title: { show: false },
          tooltip: { trigger: 'axis' },
          xAxis: { 
            type: 'category', 
            data: timestamps,
            axisLabel: { rotate: 45 }
          },
          yAxis: { 
            type: 'value',
            min: 0,
            max: 100,
            axisLabel: { formatter: '{value}%' }
          },
          series: [{
            name: 'CPU使用率',
            type: 'line',
            data: metricsHistory.value.cpu,
            smooth: true,
            areaStyle: { opacity: 0.3 },
            lineStyle: { color: '#409EFF' },
            areaStyle: { color: '#409EFF' }
          }]
        }
        charts.value.cpuChart.setOption(option)
      }
      
      // 内存图表
      if (charts.value.memoryChart) {
        const option = {
          title: { show: false },
          tooltip: { trigger: 'axis' },
          xAxis: { 
            type: 'category', 
            data: timestamps,
            axisLabel: { rotate: 45 }
          },
          yAxis: { 
            type: 'value',
            min: 0,
            max: 100,
            axisLabel: { formatter: '{value}%' }
          },
          series: [{
            name: '内存使用率',
            type: 'line',
            data: metricsHistory.value.memory,
            smooth: true,
            areaStyle: { opacity: 0.3 },
            lineStyle: { color: '#67C23A' },
            areaStyle: { color: '#67C23A' }
          }]
        }
        charts.value.memoryChart.setOption(option)
      }
      
      // GPU图表
      if (charts.value.gpuChart && hasGPU.value) {
        const option = {
          title: { show: false },
          tooltip: { trigger: 'axis' },
          xAxis: { 
            type: 'category', 
            data: timestamps,
            axisLabel: { rotate: 45 }
          },
          yAxis: { 
            type: 'value',
            min: 0,
            max: 100,
            axisLabel: { formatter: '{value}%' }
          },
          series: [{
            name: 'GPU使用率',
            type: 'line',
            data: metricsHistory.value.gpu,
            smooth: true,
            areaStyle: { opacity: 0.3 },
            lineStyle: { color: '#E6A23C' },
            areaStyle: { color: '#E6A23C' }
          }]
        }
        charts.value.gpuChart.setOption(option)
      }
      
      // 磁盘IO图表
      if (charts.value.diskIOChart) {
        const option = {
          title: { show: false },
          tooltip: { 
            trigger: 'axis',
            formatter: function(params) {
              let result = params[0].name + '<br/>'
              params.forEach(param => {
                const value = formatSpeed(param.value)
                result += `${param.seriesName}: ${value}<br/>`
              })
              return result
            }
          },
          legend: { data: ['读取', '写入'] },
          xAxis: { 
            type: 'category', 
            data: timestamps,
            axisLabel: { rotate: 45 }
          },
          yAxis: { 
            type: 'value',
            axisLabel: { 
              formatter: function(value) {
                return formatSpeed(value)
              }
            }
          },
          series: [
            {
              name: '读取',
              type: 'line',
              data: metricsHistory.value.disk_io.map(d => d.read),
              smooth: true,
              lineStyle: { color: '#409EFF' }
            },
            {
              name: '写入',
              type: 'line',
              data: metricsHistory.value.disk_io.map(d => d.write),
              smooth: true,
              lineStyle: { color: '#F56C6C' }
            }
          ]
        }
        charts.value.diskIOChart.setOption(option)
      }
      
      // 网络IO图表
      if (charts.value.networkIOChart) {
        const option = {
          title: { show: false },
          tooltip: { 
            trigger: 'axis',
            formatter: function(params) {
              let result = params[0].name + '<br/>'
              params.forEach(param => {
                const value = formatSpeed(param.value)
                result += `${param.seriesName}: ${value}<br/>`
              })
              return result
            }
          },
          legend: { data: ['下载', '上传'] },
          xAxis: { 
            type: 'category', 
            data: timestamps,
            axisLabel: { rotate: 45 }
          },
          yAxis: { 
            type: 'value',
            axisLabel: { 
              formatter: function(value) {
                return formatSpeed(value)
              }
            }
          },
          series: [
            {
              name: '下载',
              type: 'line',
              data: metricsHistory.value.network_io.map(d => d.recv),
              smooth: true,
              lineStyle: { color: '#67C23A' }
            },
            {
              name: '上传',
              type: 'line',
              data: metricsHistory.value.network_io.map(d => d.sent),
              smooth: true,
              lineStyle: { color: '#E6A23C' }
            }
          ]
        }
        charts.value.networkIOChart.setOption(option)
      }
      
      // 温度图表
      if (charts.value.temperatureChart) {
        const option = {
          title: { show: false },
          tooltip: { 
            trigger: 'axis',
            formatter: function(params) {
              return `${params[0].name}<br/>温度: ${params[0].value}°C`
            }
          },
          xAxis: { 
            type: 'category', 
            data: timestamps,
            axisLabel: { rotate: 45 }
          },
          yAxis: { 
            type: 'value',
            axisLabel: { formatter: '{value}°C' }
          },
          series: [{
            name: '系统温度',
            type: 'line',
            data: metricsHistory.value.temperature.map(t => t === 'N/A' ? 0 : t),
            smooth: true,
            areaStyle: { opacity: 0.3 },
            lineStyle: { color: '#F56C6C' },
            areaStyle: { color: '#F56C6C' }
          }]
        }
        charts.value.temperatureChart.setOption(option)
      }
    }

    // 切换自动刷新
    const toggleAutoRefresh = () => {
      autoRefresh.value = !autoRefresh.value
      
      if (autoRefresh.value) {
        startAutoRefresh()
      } else {
        stopAutoRefresh()
      }
    }

    // 开始自动刷新
    const startAutoRefresh = () => {
      if (refreshTimer) {
        clearInterval(refreshTimer)
      }
      
      refreshTimer = setInterval(() => {
        refreshMetrics()
      }, refreshInterval.value)
    }

    // 停止自动刷新
    const stopAutoRefresh = () => {
      if (refreshTimer) {
        clearInterval(refreshTimer)
        refreshTimer = null
      }
    }

    // 监听刷新间隔变化
    const watchRefreshInterval = () => {
      if (autoRefresh.value) {
        startAutoRefresh()
      }
    }

    onMounted(async () => {
      await refreshMetrics()
      
      // 延迟初始化图表，确保DOM元素已渲染
      await nextTick()
      setTimeout(() => {
        initCharts()
        updateCharts()
      }, 500)
      
      if (autoRefresh.value) {
        startAutoRefresh()
      }
      
      // 监听窗口大小变化，重新调整图表大小
      window.addEventListener('resize', () => {
        Object.values(charts.value).forEach(chart => {
          if (chart && chart.resize) {
            chart.resize()
          }
        })
      })
    })

    onUnmounted(() => {
      stopAutoRefresh()
      
      // 销毁图表实例
      Object.values(charts.value).forEach(chart => {
        if (chart && chart.dispose) {
          chart.dispose()
        }
      })
      
      window.removeEventListener('resize', () => {})
    })

    return {
      systemMetrics,
      loading,
      activeTab,
      autoRefresh,
      refreshInterval,
      hasGPU,
      
      // 方法
      refreshMetrics,
      toggleAutoRefresh,
      formatBytes,
      formatSpeed,
      getGPUUtilization,
      getGPUTemperature,
      getDiskUsage,
      getDiskUsed,
      getDiskTotal,
      getNetworkSpeed,
      getSystemTemperature,
      getTemperatureStatus,
      getTempClass,
      watchRefreshInterval
    }
  },
  
  watch: {
    refreshInterval() {
      this.watchRefreshInterval()
    }
  }
}
</script>

<style scoped>
.edge-devices-dashboard {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 30px;
  text-align: center;
}

.page-header h1 {
  color: #2c3e50;
  font-size: 2.5rem;
  margin-bottom: 10px;
}

.page-header p {
  color: #7f8c8d;
  font-size: 1.2rem;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  padding: 25px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.3s ease;
  border-left: 5px solid;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}

.stat-card.cpu { border-left-color: #409EFF; }
.stat-card.memory { border-left-color: #67C23A; }
.stat-card.gpu { border-left-color: #E6A23C; }
.stat-card.disk { border-left-color: #F56C6C; }
.stat-card.network { border-left-color: #909399; }
.stat-card.temperature { border-left-color: #F56C6C; }

.stat-icon {
  font-size: 2.5rem;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.stat-content h3 {
  font-size: 2rem;
  margin: 0 0 5px 0;
  color: #2c3e50;
  font-weight: 600;
}

.stat-content p {
  margin: 0 0 5px 0;
  color: #34495e;
  font-weight: 500;
}

.stat-content small {
  color: #7f8c8d;
  font-size: 0.9rem;
}

/* 图表区域 */
.charts-section {
  background: white;
  border-radius: 16px;
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f1f2f6;
}

.section-header h2 {
  color: #2c3e50;
  margin: 0;
  font-size: 1.8rem;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 25px;
}

.chart-card {
  background: #fafbfc;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e9ecef;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.chart-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.2rem;
}

.current-value {
  font-weight: 600;
  color: #409EFF;
  font-size: 1.1rem;
}

.chart-container {
  height: 200px;
  width: 100%;
}

/* 详细信息区域 */
.details-section {
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin: 20px 0;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
}

.detail-item label {
  font-weight: 600;
  color: #495057;
}

.detail-item span {
  color: #2c3e50;
  font-weight: 500;
}

/* CPU核心使用率 */
.core-usage {
  margin-top: 25px;
}

.core-usage h4 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.core-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.core-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
}

.core-label {
  font-weight: 500;
  min-width: 60px;
  color: #495057;
}

.core-value {
  font-weight: 600;
  min-width: 45px;
  text-align: right;
  color: #409EFF;
}

/* 内存详情 */
.memory-details {
  margin-top: 20px;
}

.memory-section {
  margin-bottom: 25px;
}

.memory-section h4 {
  color: #2c3e50;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e9ecef;
}

/* GPU详情 */
.gpu-section {
  margin-bottom: 25px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
}

.gpu-section h4 {
  color: #2c3e50;
  margin-bottom: 15px;
}

/* 磁盘详情 */
.disk-details {
  margin-top: 20px;
}

.disk-usage h4,
.disk-io h4 {
  color: #2c3e50;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e9ecef;
}

.disk-item {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 12px;
}

.disk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.disk-header strong {
  color: #2c3e50;
}

.mount-point {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.fs-type {
  background: #e9ecef;
  color: #495057;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
}

.disk-progress {
  margin: 10px 0;
}

.disk-stats {
  display: flex;
  justify-content: space-between;
  color: #7f8c8d;
  font-size: 0.9rem;
}

/* 网络详情 */
.network-details {
  margin-top: 20px;
}

.network-io h4,
.network-interfaces h4 {
  color: #2c3e50;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e9ecef;
}

.interface-item {
  margin-bottom: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 12px;
}

.interface-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.interface-header strong {
  color: #2c3e50;
}

.interface-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}

.addresses {
  grid-column: 1 / -1;
}

.address-item {
  margin: 5px 0;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border-left: 3px solid #409EFF;
}

.address {
  font-weight: 500;
  color: #2c3e50;
}

.netmask {
  color: #7f8c8d;
  margin-left: 5px;
}

/* 温度详情 */
.temperature-details {
  margin-top: 20px;
}

.sensor-group {
  margin-bottom: 25px;
}

.sensor-group h4 {
  color: #2c3e50;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e9ecef;
}

.sensor-item {
  margin-bottom: 12px;
  padding: 12px 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.sensor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sensor-label {
  font-weight: 500;
  color: #495057;
}

.sensor-temp {
  font-weight: 600;
  font-size: 1.1rem;
}

.temp-normal { color: #67C23A; }
.temp-warning { color: #E6A23C; }
.temp-critical { color: #F56C6C; }

.sensor-limits {
  margin-top: 8px;
  display: flex;
  gap: 15px;
}

.sensor-limits small {
  color: #7f8c8d;
}

.sensor-limits small.critical {
  color: #F56C6C;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-controls {
    flex-direction: column;
    gap: 10px;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
}
</style>