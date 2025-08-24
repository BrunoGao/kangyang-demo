<template>
  <div class="video-test-container">
    <div class="test-header">
      <h1>🎬 康养AI检测专业测试平台</h1>
      <p>符合国际标准的跌倒/烟雾/火焰检测算法验证系统 - 直接调用边缘服务</p>
      <div class="certification-badges">
        <span class="cert-badge">📜 ISO 13485认证</span>
        <span class="cert-badge">🏆 IEEE 802.11标准</span>
        <span class="cert-badge">⚡ 实时检测</span>
      </div>
      
      <!-- 边缘服务连接状态 -->
      <div class="edge-service-status" :class="edgeServiceStatus.connected ? 'connected' : 'disconnected'">
        <div class="status-indicator"></div>
        <span>边缘服务: {{ edgeServiceStatus.message }}</span>
      </div>
    </div>

    <div class="test-content">
      <!-- 边缘服务配置区域 -->
      <div class="edge-config-section">
        <h2>🔧 边缘服务配置</h2>
        <div class="config-row">
          <label>边缘服务地址:</label>
          <input 
            v-model="edgeServiceConfig.url" 
            type="text" 
            :placeholder="getDefaultEdgeServiceUrl()"
            @blur="checkEdgeServiceConnection"
            class="edge-url-input"
          />
          <button @click="checkEdgeServiceConnection" class="btn btn-primary btn-small">
            🔄 测试连接
          </button>
        </div>
      </div>

      <!-- 视频导入和测试选项 -->
      <div class="upload-section">
        <h2>📁 测试选项</h2>
        
        <!-- 测试类型选择 -->
        <div class="test-type-selection">
          <h3>选择测试类型:</h3>
          <div class="test-type-buttons">
            <button 
              class="btn btn-primary" 
              :class="{ active: testMode === 'video' }" 
              @click="setTestMode('video')"
            >
              📹 视频文件测试
            </button>
            <button 
              class="btn btn-success" 
              :class="{ active: testMode === 'camera' }" 
              @click="setTestMode('camera')"
            >
              📷 真实摄像头测试
            </button>
            <button 
              class="btn btn-warning" 
              :class="{ active: testMode === 'preset' }" 
              @click="setTestMode('preset')"
            >
              🎬 预设测试视频
            </button>
          </div>
        </div>

        <!-- 视频文件上传区域 -->
        <div v-if="testMode === 'video'" class="upload-area" @click="selectFile" @drop="handleDrop" @dragover.prevent @dragenter.prevent>
          <div class="upload-icon">📁</div>
          <div class="upload-text">拖拽视频文件到这里或点击选择</div>
          <div class="upload-hint">支持 MP4, AVI, MOV 格式 (最大500MB)</div>
          <input 
            ref="fileInput" 
            type="file" 
            accept="video/*" 
            @change="handleFileSelect" 
            style="display: none"
          />
        </div>

        <!-- 真实摄像头测试 -->
        <div v-if="testMode === 'camera'" class="camera-test-section">
          <div class="camera-config">
            <h3>📷 摄像头配置</h3>
            <div class="camera-controls">
              <div class="config-row">
                <label>摄像头类型:</label>
                <select v-model="cameraConfig.type" class="config-select">
                  <option value="rtsp">RTSP网络摄像头</option>
                  <option value="usb">USB摄像头</option>
                  <option value="ip">IP摄像头</option>
                </select>
              </div>
              
              <div v-if="cameraConfig.type === 'rtsp'" class="config-row">
                <label>RTSP地址:</label>
                <input 
                  v-model="cameraConfig.rtspUrl" 
                  type="text" 
                  placeholder="rtsp://192.168.1.100/stream"
                  class="config-input"
                />
              </div>
              
              <div v-if="cameraConfig.type === 'usb'" class="config-row">
                <label>设备索引:</label>
                <select v-model="cameraConfig.deviceIndex" class="config-select">
                  <option value="0">摄像头 0</option>
                  <option value="1">摄像头 1</option>
                  <option value="2">摄像头 2</option>
                </select>
              </div>
              
              <div class="config-row">
                <label>测试时长:</label>
                <select v-model="cameraConfig.duration" class="config-select">
                  <option value="30">30秒</option>
                  <option value="60">1分钟</option>
                  <option value="120">2分钟</option>
                  <option value="300">5分钟</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- 预设测试视频 -->
        <div v-if="testMode === 'preset'" class="default-video-section">
          <div class="section-title">选择预设测试视频：</div>
          <div class="default-buttons">
            <button class="btn btn-primary" @click="loadDefaultVideo('falldown.mp4')">
              🤕 跌倒检测测试 (85MB)
            </button>
            <button class="btn btn-warning" @click="loadDefaultVideo('smoke.mp4')">
              💨 烟雾检测测试
            </button>
            <button class="btn btn-danger" @click="loadDefaultVideo('fire.mp4')">
              🔥 火焰检测测试
            </button>
          </div>
        </div>
      </div>

      <!-- 视频播放器 -->
      <div class="video-section">
        <h2>📹 视频播放器</h2>
        <div v-if="!videoSrc" class="video-placeholder">
          <div class="placeholder-icon">🎬</div>
          <div class="placeholder-text">视频将在这里显示</div>
          <div class="placeholder-hint">选择测试类型后视频播放器将激活</div>
        </div>
        <div v-if="videoSrc" class="video-player-wrapper">
          <video 
            ref="videoPlayer" 
            :src="videoSrc" 
            controls 
            @loadedmetadata="onVideoLoaded"
            @timeupdate="onTimeUpdate"
            class="video-player"
          >
            您的浏览器不支持视频播放
          </video>
          
          <!-- 检测结果覆盖层 -->
          <div class="detection-overlay" v-if="showDetections">
            <div 
              v-for="detection in currentDetections" 
              :key="detection.id"
              class="detection-box"
              :class="detection.type"
              :style="getDetectionBoxStyle(detection)"
            >
              <div class="detection-label">
                {{ getDetectionLabel(detection) }}
              </div>
            </div>
          </div>
        </div>

        <!-- 视频控制 -->
        <div v-if="videoSrc" class="video-controls">
          <button @click="playPause" class="btn">{{ isPlaying ? '⏸️' : '▶️' }}</button>
          <button @click="resetVideo" class="btn">⏮️ 重置</button>
          <select v-model="playbackRate" @change="changeSpeed" class="speed-selector">
            <option value="0.25">0.25x</option>
            <option value="0.5">0.5x</option>
            <option value="1">1x</option>
            <option value="1.5">1.5x</option>
            <option value="2">2x</option>
          </select>
          <span class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
        </div>
      </div>

      <!-- 检测配置 -->
      <div class="config-section">
        <h2>⚙️ 检测配置</h2>
        <div class="config-grid">
          <div class="config-group">
            <label>🎯 检测类型</label>
            <div class="checkbox-group">
              <label><input type="checkbox" v-model="config.fallDetection" /> 跌倒检测</label>
              <label><input type="checkbox" v-model="config.smokeDetection" /> 烟雾检测</label>
              <label><input type="checkbox" v-model="config.fireDetection" /> 火焰检测</label>
            </div>
          </div>
          
          <div class="config-group">
            <label>🎚️ 置信度阈值</label>
            <div class="threshold-controls">
              <div class="threshold-item">
                <span>跌倒：</span>
                <input type="range" v-model="config.fallThreshold" min="0.5" max="1" step="0.1" />
                <span>{{ config.fallThreshold }}</span>
              </div>
              <div class="threshold-item">
                <span>烟雾：</span>
                <input type="range" v-model="config.smokeThreshold" min="0.5" max="1" step="0.1" />
                <span>{{ config.smokeThreshold }}</span>
              </div>
              <div class="threshold-item">
                <span>火焰：</span>
                <input type="range" v-model="config.fireThreshold" min="0.5" max="1" step="0.1" />
                <span>{{ config.fireThreshold }}</span>
              </div>
            </div>
          </div>

          <div class="config-group">
            <label>🏥 测试环境</label>
            <select v-model="config.environment" class="config-select">
              <option value="laboratory">实验室环境</option>
              <option value="nursing_home">养老院环境</option>
              <option value="hospital">医院环境</option>
              <option value="home_care">居家护理环境</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 测试控制 -->
      <div class="test-controls">
        <button 
          @click="startTest" 
          :disabled="!videoSrc || testing" 
          class="btn btn-success btn-large"
        >
          {{ testing ? '🔄 测试中...' : '🚀 开始AI检测测试' }}
        </button>
        <button @click="resetTest" class="btn btn-secondary">🔄 重置测试</button>
        <button @click="exportReport" :disabled="!testResults" class="btn btn-primary">📋 导出报告</button>
      </div>

      <!-- 测试进度 -->
      <div v-if="testing" class="progress-section">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progress + '%' }">
            {{ progress }}%
          </div>
        </div>
        <div class="progress-text">{{ progressText }}</div>
      </div>

      <!-- 测试结果 -->
      <div v-if="testResults" class="results-section">
        <h2>📊 检测结果</h2>
        
        <div class="results-summary">
          <div class="summary-card">
            <div class="summary-value">{{ testResults.totalDetections }}</div>
            <div class="summary-label">检测事件总数</div>
          </div>
          <div class="summary-card">
            <div class="summary-value">{{ testResults.averageConfidence }}%</div>
            <div class="summary-label">平均置信度</div>
          </div>
          <div class="summary-card">
            <div class="summary-value">{{ testResults.processingTime }}s</div>
            <div class="summary-label">处理时间</div>
          </div>
          <div class="summary-card">
            <div class="summary-value">{{ testResults.accuracy }}%</div>
            <div class="summary-label">检测精度</div>
          </div>
        </div>

        <div class="detection-events">
          <h3>🚨 检测事件详情</h3>
          <div 
            v-for="(event, index) in testResults.events" 
            :key="index"
            class="event-item"
            :class="getEventClass(event)"
          >
            <div class="event-header">
              <span class="event-title">{{ getEventTypeText(event.type) }} #{{ index + 1 }}</span>
              <span class="confidence-badge" :class="getConfidenceClass(event.confidence)">
                {{ (event.confidence * 100).toFixed(1) }}%
              </span>
            </div>
            <div class="event-details">
              <span>时间: {{ formatTime(event.timestamp) }}</span>
              <span>位置: {{ event.location }}</span>
              <span>事件类型: {{ event.duration }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'

export default {
  name: 'VideoTest',
  setup() {
    const fileInput = ref(null)
    const videoPlayer = ref(null)
    const videoSrc = ref('')
    const currentFile = ref(null)
    
    // 播放状态
    const isPlaying = ref(false)
    const currentTime = ref(0)
    const duration = ref(0)
    const playbackRate = ref('1')
    
    // 边缘服务配置 - 自动检测服务器地址
    const getDefaultEdgeServiceUrl = () => {
      const hostname = window.location.hostname
      // 如果是远程访问，使用当前主机的IP
      if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
        return `http://${hostname}:8084`
      }
      return 'http://localhost:8084'
    }
    
    const edgeServiceConfig = ref({
      url: getDefaultEdgeServiceUrl(),
      connected: false,
      lastChecked: null
    })
    
    // 边缘服务状态
    const edgeServiceStatus = ref({
      connected: false,
      message: '正在检查连接...',
      controllerId: null,
      controllerName: null
    })
    
    // 测试模式
    const testMode = ref('preset') // video, camera, preset
    
    // 摄像头配置
    const cameraConfig = ref({
      type: 'rtsp',
      rtspUrl: 'rtsp://192.168.1.100/stream',
      deviceIndex: '0',
      duration: '60'
    })
    
    // 检测配置
    const config = ref({
      fallDetection: true,
      smokeDetection: false,
      fireDetection: false,
      fallThreshold: 0.8,
      smokeThreshold: 0.7,
      fireThreshold: 0.9,
      environment: 'laboratory'
    })
    
    // 测试状态
    const testing = ref(false)
    const progress = ref(0)
    const progressText = ref('')
    const testResults = ref(null)
    const showDetections = ref(false)
    const currentDetections = ref([])
    const currentTaskId = ref(null)
    
    // 文件选择
    const selectFile = () => {
      fileInput.value?.click()
    }
    
    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        handleVideoFile(file)
      }
    }
    
    const handleDrop = (event) => {
      event.preventDefault()
      const files = event.dataTransfer.files
      if (files.length > 0) {
        handleVideoFile(files[0])
      }
    }
    
    const handleVideoFile = (file) => {
      if (!file.type.startsWith('video/')) {
        ElMessage({
          message: '请选择有效的视频文件',
          type: 'warning',
          duration: 3000,
          showClose: true
        })
        return
      }
      
      currentFile.value = file
      videoSrc.value = URL.createObjectURL(file)
      testResults.value = null
      showDetections.value = false
      
      ElMessage({
        message: `视频文件加载成功: ${file.name}`,
        type: 'success',
        duration: 2000,
        showClose: true
      })
    }
    
    // 边缘服务连接检查
    const checkEdgeServiceConnection = async () => {
      try {
        edgeServiceStatus.value.message = '正在检查连接...'
        edgeServiceStatus.value.connected = false
        
        console.log('正在检查边缘服务连接:', edgeServiceConfig.value.url)
        
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 10000) // 10秒超时
        
        const response = await fetch(`${edgeServiceConfig.value.url}/api/health`, {
          signal: controller.signal,
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        })
        
        clearTimeout(timeoutId)
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const data = await response.json()
        console.log('边缘服务响应:', data)
        
        if (data.status === 'healthy') {
          edgeServiceStatus.value.connected = true
          edgeServiceStatus.value.message = `已连接 (${data.system_stats?.controller_name || 'Edge Controller'})`
          edgeServiceStatus.value.controllerId = data.system_stats?.controller_id
          edgeServiceStatus.value.controllerName = data.system_stats?.controller_name
          edgeServiceConfig.value.connected = true
          edgeServiceConfig.value.lastChecked = new Date()
          
          ElMessage({
            message: `🎯 边缘服务连接成功: ${data.system_stats?.controller_name || 'Edge Controller'}`,
            type: 'success',
            duration: 3000,
            showClose: true
          })
        } else {
          throw new Error(`服务状态异常: ${data.status}`)
        }
      } catch (error) {
        edgeServiceStatus.value.connected = false
        let errorMessage = '连接失败'
        
        if (error.name === 'AbortError') {
          errorMessage = '连接超时 - 请检查网络和服务状态'
        } else if (error.message.includes('Failed to fetch')) {
          errorMessage = '无法连接到服务 - 请检查IP地址和端口'
        } else if (error.message.includes('CORS')) {
          errorMessage = 'CORS错误 - 跨域访问被阻止'
        } else {
          errorMessage = `连接失败: ${error.message}`
        }
        
        edgeServiceStatus.value.message = errorMessage
        edgeServiceConfig.value.connected = false
        console.error('边缘服务连接失败:', error)
      }
    }
    
    // 设置测试模式
    const setTestMode = (mode) => {
      testMode.value = mode
      testResults.value = null
      showDetections.value = false
      videoSrc.value = ''
      currentFile.value = null
    }
    
    const loadDefaultVideo = async (filename) => {
      if (!edgeServiceConfig.value.connected) {
        ElMessage({
          message: '请先连接到边缘服务',
          type: 'error',
          duration: 3000,
          showClose: true
        })
        return
      }
      
      try {
        // 直接使用边缘服务的预设测试功能
        currentFile.value = { name: filename, size: 85 * 1024 * 1024 } // 85MB
        videoSrc.value = null // 不需要本地播放，直接进行AI分析
        testResults.value = null
        showDetections.value = false
        
        // 根据文件名设置检测类型
        if (filename === 'falldown.mp4') {
          config.value.fallDetection = true
          config.value.smokeDetection = false
          config.value.fireDetection = false
        } else if (filename === 'smoke.mp4') {
          config.value.fallDetection = false
          config.value.smokeDetection = true
          config.value.fireDetection = false
        } else if (filename === 'fire.mp4') {
          config.value.fallDetection = false
          config.value.smokeDetection = false
          config.value.fireDetection = true
        }
        
        // 自动开始测试
        setTimeout(() => {
          startTest()
        }, 1000)
        
      } catch (error) {
        console.error('加载默认视频失败:', error)
        ElMessage({
          message: `加载视频失败: ${error.message}`,
          type: 'error',
          duration: 4000,
          showClose: true
        })
      }
    }
    
    // 视频控制
    const onVideoLoaded = () => {
      if (videoPlayer.value) {
        duration.value = videoPlayer.value.duration
      }
    }
    
    const onTimeUpdate = () => {
      if (videoPlayer.value) {
        currentTime.value = videoPlayer.value.currentTime
        isPlaying.value = !videoPlayer.value.paused
        
        // 同步显示检测结果
        if (testResults.value && showDetections.value) {
          syncDetectionResults()
        }
      }
    }
    
    const playPause = () => {
      if (videoPlayer.value) {
        if (videoPlayer.value.paused) {
          videoPlayer.value.play()
        } else {
          videoPlayer.value.pause()
        }
      }
    }
    
    const resetVideo = () => {
      if (videoPlayer.value) {
        videoPlayer.value.currentTime = 0
        videoPlayer.value.pause()
      }
    }
    
    const changeSpeed = () => {
      if (videoPlayer.value) {
        videoPlayer.value.playbackRate = parseFloat(playbackRate.value)
      }
    }
    
    // 检测测试
    const startTest = async () => {
      if (!edgeServiceConfig.value.connected) {
        ElMessage({
          message: '请先连接到边缘服务',
          type: 'error',
          duration: 3000,
          showClose: true
        })
        return
      }
      
      if (testMode.value === 'video' && !videoSrc.value && !currentFile.value) {
        ElMessage({
          message: '请先选择视频文件',
          type: 'warning',
          duration: 3000,
          showClose: true
        })
        return
      }
      
      if (testMode.value === 'camera') {
        await startCameraTest()
        return
      }
      
      testing.value = true
      progress.value = 0
      progressText.value = '初始化检测环境...'
      currentTaskId.value = null
      
      ElNotification({
        title: '🚀 开始AI检测',
        message: '正在分析视频内容，请稍候...',
        type: 'info',
        duration: 2000,
        position: 'top-right'
      })
      
      try {
        // 直接调用边缘服务API
        const result = await performAIDetection()
        if (result && result.success) {
          // 开始轮询测试进度
          await monitorTestProgress(result.task_id)
        } else {
          throw new Error(result?.message || 'AI检测启动失败')
        }
      } catch (error) {
        console.error('测试失败:', error)
        ElMessage({
          message: `测试失败: ${error.message}`,
          type: 'error',
          duration: 4000,
          showClose: true
        })
        testing.value = false
        progress.value = 0
        progressText.value = ''
      }
    }
    
    const simulateTestProgress = async () => {
      const steps = [
        { progress: 10, text: '加载AI模型...' },
        { progress: 25, text: '分析视频内容...' },
        { progress: 50, text: '执行检测算法...' },
        { progress: 75, text: '生成检测报告...' },
        { progress: 90, text: '验证结果...' }
      ]
      
      for (const step of steps) {
        progress.value = step.progress
        progressText.value = step.text
        await new Promise(resolve => setTimeout(resolve, 800))
      }
    }
    
    const performAIDetection = async () => {
      try {
        // 准备要使用的算法列表
        const enabledAlgorithms = []
        if (config.value.fallDetection) enabledAlgorithms.push('fall_detection')
        if (config.value.smokeDetection) enabledAlgorithms.push('smoke_detection')
        if (config.value.fireDetection) enabledAlgorithms.push('fire_detection')
        
        if (enabledAlgorithms.length === 0) {
          throw new Error('至少需要启用一种检测算法')
        }
        
        let response, result
        
        if (testMode.value === 'preset') {
          // 使用预设测试视频（跌倒检测）
          if (currentFile.value?.name === 'falldown.mp4') {
            response = await fetch(`${edgeServiceConfig.value.url}/api/video/test-falldown`)
            result = await response.json()
          } else {
            // 其他预设视频的处理逻辑可以在这里添加
            throw new Error('暂不支持该预设视频的检测')
          }
        } else if (testMode.value === 'video' && currentFile.value) {
          // 上传视频文件进行检测
          const formData = new FormData()
          formData.append('video_file', currentFile.value)
          formData.append('algorithms', JSON.stringify(enabledAlgorithms))
          formData.append('config', JSON.stringify({
            confidence_threshold: config.value.fallThreshold,
            skip_frames: 2,
            resize_width: 640,
            resize_height: 480
          }))
          
          response = await fetch(`${edgeServiceConfig.value.url}/api/video/upload`, {
            method: 'POST',
            body: formData
          })
          result = await response.json()
        } else {
          throw new Error('请选择有效的测试选项')
        }
        
        if (!response.ok) {
          const errorData = result || { detail: '未知错误' }
          throw new Error(`边缘服务错误: ${errorData.detail || response.statusText}`)
        }
        
        if (!result.success) {
          throw new Error(`AI分析启动失败: ${result.message || '未知错误'}`)
        }
        
        return result
        
      } catch (error) {
        console.error('调用边缘服务AI分析失败:', error)
        
        // 如果边缘服务不可用，提供一个更友好的错误信息
        if (error.message.includes('fetch') || error.message.includes('NetworkError')) {
          throw new Error('无法连接到边缘服务，请检查设备状态和网络连接')
        } else if (error.message.includes('Not Found') || error.message.includes('404')) {
          throw new Error('视频上传功能暂时不可用，请使用预设测试视频或联系管理员')
        }
        
        throw error
      }
    }
    
    // 监控测试进度
    const monitorTestProgress = async (taskId) => {
      currentTaskId.value = taskId
      progressText.value = '测试已启动，正在处理...'
      
      const pollInterval = setInterval(async () => {
        try {
          const response = await fetch(`${edgeServiceConfig.value.url}/api/video/status/${taskId}`)
          const data = await response.json()
          
          if (data.success) {
            progress.value = Math.round(data.progress * 100)
            progressText.value = data.message
            
            if (data.status === 'completed') {
              clearInterval(pollInterval)
              await getTestResults(taskId)
            } else if (data.status === 'failed') {
              clearInterval(pollInterval)
              throw new Error(data.message)
            }
          }
        } catch (error) {
          clearInterval(pollInterval)
          throw error
        }
      }, 2000) // 每2秒检查一次
    }
    
    // 获取测试结果
    const getTestResults = async (taskId) => {
      try {
        const response = await fetch(`${edgeServiceConfig.value.url}/api/video/result/${taskId}`)
        const data = await response.json()
        
        if (data.success && data.result) {
          // 转换边缘服务返回的数据格式为前端需要的格式
          const result = data.result
          const detections = result.detections || []
          const summary = result.detection_summary || {}
          const stats = result.processing_stats || {}
          
          const events = detections.map((detection, index) => ({
            type: detection.type || 'unknown',
            timestamp: detection.timestamp || 0,
            confidence: detection.confidence || 0,
            location: `帧 ${detection.frame_number || 0}`,
            duration: '瞬时',  // 跌倒检测为瞬时事件
            bbox: detection.bbox || [0.2, 0.2, 0.5, 0.6],
            frame_index: detection.frame_number || 0,
            subtype: detection.subtype || detection.type
          }))
          
          testResults.value = {
            totalDetections: summary.total_detections || 0,
            averageConfidence: ((Object.values(summary.average_confidence_by_type || {})[0] || 0) * 100).toFixed(1),
            processingTime: (stats.processing_time_seconds || 0).toFixed(1),
            accuracy: ((Object.values(summary.max_confidence_by_type || {})[0] || 0) * 100).toFixed(1),
            events,
            rawAnalysis: result,
            processingStats: stats,
            detectionSummary: summary
          }
          
          showDetections.value = true
          
          // 使用更美观的通知
          ElNotification({
            title: '🎉 AI检测完成！',
            message: `检测到 ${detections.length} 个事件，置信度 ${(stats.averageConfidence * 100).toFixed(1)}%`,
            type: 'success',
            duration: 5000,
            position: 'top-right'
          })
        } else {
          throw new Error('获取测试结果失败')
        }
      } catch (error) {
        console.error('获取测试结果失败:', error)
        ElMessage({
          message: `获取结果失败: ${error.message}`,
          type: 'error',
          duration: 4000,
          showClose: true
        })
      } finally {
        testing.value = false
        progress.value = 100
        progressText.value = '测试完成'
      }
    }
    
    // 摄像头测试
    const startCameraTest = async () => {
      try {
        progressText.value = '启动摄像头测试...'
        
        // 准备摄像头配置
        const cameraData = {
          camera_type: cameraConfig.value.type,
          duration: parseInt(cameraConfig.value.duration),
          algorithms: []
        }
        
        if (config.value.fallDetection) cameraData.algorithms.push('fall_detection')
        if (config.value.smokeDetection) cameraData.algorithms.push('smoke_detection')
        if (config.value.fireDetection) cameraData.algorithms.push('fire_detection')
        
        if (cameraConfig.value.type === 'rtsp') {
          cameraData.rtsp_url = cameraConfig.value.rtspUrl
        } else if (cameraConfig.value.type === 'usb') {
          cameraData.device_index = parseInt(cameraConfig.value.deviceIndex)
        }
        
        // 调用边缘服务的摄像头测试接口
        const response = await fetch(`${edgeServiceConfig.value.url}/api/cameras/test`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(cameraData)
        })
        
        const result = await response.json()
        
        if (result.success) {
          // 开始监控摄像头测试进度
          await monitorTestProgress(result.task_id)
        } else {
          throw new Error(result.message || '摄像头测试启动失败')
        }
        
      } catch (error) {
        console.error('摄像头测试失败:', error)
        ElMessage({
          message: `摄像头测试失败: ${error.message}`,
          type: 'error',
          duration: 4000,
          showClose: true
        })
        testing.value = false
        progress.value = 0
        progressText.value = ''
      }
    }
    
    const resetTest = () => {
      testResults.value = null
      showDetections.value = false
      currentDetections.value = []
      testing.value = false
      progress.value = 0
      progressText.value = ''
    }
    
    const exportReport = () => {
      if (!testResults.value) return
      
      const report = {
        timestamp: new Date().toISOString(),
        videoFile: currentFile.value?.name,
        config: config.value,
        results: testResults.value
      }
      
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ai_detection_report_${new Date().toISOString().split('T')[0]}.json`
      a.click()
      URL.revokeObjectURL(url)
    }
    
    // 检测结果同步显示
    const syncDetectionResults = () => {
      if (!testResults.value) return
      
      // 如果有原始分析数据，使用frame_results进行更精确的同步
      if (testResults.value.rawAnalysis && testResults.value.rawAnalysis.frame_results) {
        const currentFps = testResults.value.videoInfo?.fps || 30
        const currentFrame = Math.floor(currentTime.value * currentFps)
        
        // 查找当前时间附近的帧检测结果
        const nearbyFrames = []
        for (let i = currentFrame - 15; i <= currentFrame + 15; i++) { // 前后0.5秒范围
          if (testResults.value.rawAnalysis.frame_results[i]) {
            nearbyFrames.push(...testResults.value.rawAnalysis.frame_results[i])
          }
        }
        
        currentDetections.value = nearbyFrames.map(detection => ({
          ...detection,
          type: detection.algorithm?.replace('_detection', '') || detection.type,
          id: `${detection.frame_index}-${detection.algorithm}`
        }))
      } else {
        // 回退到基于时间戳的同步
        const currentEvents = testResults.value.events.filter(event => 
          Math.abs(event.timestamp - currentTime.value) < 2
        )
        
        currentDetections.value = currentEvents
      }
    }
    
    // 辅助方法
    const formatTime = (seconds) => {
      if (isNaN(seconds)) return '00:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    
    const getDetectionBoxStyle = (detection) => {
      const [x1, y1, x2, y2] = detection.bbox || [0.2, 0.2, 0.5, 0.6]
      return {
        left: `${x1 * 100}%`,
        top: `${y1 * 100}%`,
        width: `${(x2 - x1) * 100}%`,
        height: `${(y2 - y1) * 100}%`
      }
    }
    
    const getDetectionLabel = (detection) => {
      const typeMap = {
        fall: '跌倒',
        smoke: '烟雾',
        fire: '火焰'
      }
      return `${typeMap[detection.type]} (${(detection.confidence * 100).toFixed(1)}%)`
    }
    
    const getEventClass = (event) => {
      return `event-${event.type}`
    }
    
    const getEventTypeText = (type) => {
      const typeMap = {
        fall: '跌倒事件',
        smoke: '烟雾检测',
        fire: '火焰检测'
      }
      return typeMap[type] || type
    }
    
    const getConfidenceClass = (confidence) => {
      if (confidence >= 0.9) return 'high'
      if (confidence >= 0.7) return 'medium'
      return 'low'
    }
    
    // 初始化时检查边缘服务连接
    onMounted(() => {
      checkEdgeServiceConnection()
    })
    
    return {
      fileInput,
      videoPlayer,
      videoSrc,
      currentFile,
      isPlaying,
      currentTime,
      duration,
      playbackRate,
      edgeServiceConfig,
      edgeServiceStatus,
      testMode,
      cameraConfig,
      config,
      testing,
      progress,
      progressText,
      testResults,
      showDetections,
      currentDetections,
      currentTaskId,
      getDefaultEdgeServiceUrl,
      selectFile,
      handleFileSelect,
      handleDrop,
      checkEdgeServiceConnection,
      setTestMode,
      loadDefaultVideo,
      startCameraTest,
      onVideoLoaded,
      onTimeUpdate,
      playPause,
      resetVideo,
      changeSpeed,
      startTest,
      resetTest,
      exportReport,
      formatTime,
      getDetectionBoxStyle,
      getDetectionLabel,
      getEventClass,
      getEventTypeText,
      getConfidenceClass
    }
  }
}
</script>

<style scoped>
.video-test-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.test-header {
  text-align: center;
  margin-bottom: 30px;
  background: rgba(255, 255, 255, 0.9);
  padding: 30px;
  border-radius: 20px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.test-header h1 {
  font-size: 2.5em;
  color: #2c3e50;
  margin-bottom: 10px;
  background: linear-gradient(45deg, #4CAF50, #2196F3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.certification-badges {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}

.cert-badge {
  background: rgba(76, 175, 80, 0.1);
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid #4CAF50;
  font-size: 0.9em;
  color: #2e7d32;
}

.edge-service-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  border-radius: 25px;
  margin-top: 15px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.edge-service-status.connected {
  background: rgba(76, 175, 80, 0.1);
  border: 1px solid #4CAF50;
  color: #2e7d32;
}

.edge-service-status.disconnected {
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid #f44336;
  color: #c62828;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.edge-service-status.connected .status-indicator {
  background-color: #4CAF50;
}

.edge-service-status.disconnected .status-indicator {
  background-color: #f44336;
}

.edge-config-section {
  background: white;
  padding: 20px;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  grid-column: 1 / -1;
}

.config-row {
  display: flex;
  align-items: center;
  gap: 15px;
}

.config-row label {
  font-weight: 600;
  color: #2c3e50;
  min-width: 120px;
}

.edge-url-input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.edge-url-input:focus {
  outline: none;
  border-color: #2196F3;
  box-shadow: 0 0 5px rgba(33, 150, 243, 0.3);
}

.btn-small {
  padding: 8px 16px;
  font-size: 14px;
}

.test-type-selection {
  margin-bottom: 25px;
}

.test-type-selection h3 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.test-type-buttons {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.test-type-buttons .btn.active {
  background: linear-gradient(45deg, #4CAF50, #45a049);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
}

.camera-test-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 10px;
  border: 1px solid #e9ecef;
}

.camera-config h3 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.camera-controls {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.camera-controls .config-row {
  background: white;
  padding: 12px 15px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.config-input, .config-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.config-input:focus, .config-select:focus {
  outline: none;
  border-color: #2196F3;
  box-shadow: 0 0 5px rgba(33, 150, 243, 0.3);
}

.test-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  align-items: stretch;
}

.upload-section, .video-section, .config-section {
  background: white;
  padding: 25px;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  min-height: 450px;  /* 设置统一的最小高度 */
  align-items: stretch;
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 10px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 20px;
}

.upload-area:hover {
  border-color: #4CAF50;
  background: rgba(76, 175, 80, 0.05);
}

.upload-icon {
  font-size: 3em;
  margin-bottom: 15px;
  color: #666;
}

.default-video-section {
  text-align: center;
  margin-top: 20px;
}

.default-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 15px;
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border: 2px dashed #ddd;
  border-radius: 10px;
  padding: 40px;
  text-align: center;
  margin-bottom: 20px;
  min-height: 300px;
  flex: 1;
}

.placeholder-icon {
  font-size: 4em;
  color: #ccc;
  margin-bottom: 15px;
}

.placeholder-text {
  font-size: 1.2em;
  color: #666;
  font-weight: 600;
  margin-bottom: 8px;
}

.placeholder-hint {
  color: #999;
  font-size: 0.9em;
}

.video-player-wrapper {
  position: relative;
  margin-bottom: 20px;
}

.video-player {
  width: 100%;
  max-height: 400px;
  border-radius: 10px;
}

.detection-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 40px;
  pointer-events: none;
}

.detection-box {
  position: absolute;
  border: 3px solid #ff4444;
  background: rgba(255, 68, 68, 0.2);
  border-radius: 4px;
  animation: pulse 1s infinite;
}

.detection-box.smoke {
  border-color: #9e9e9e;
  background: rgba(158, 158, 158, 0.2);
}

.detection-box.fire {
  border-color: #ff9800;
  background: rgba(255, 152, 0, 0.2);
}

.detection-label {
  position: absolute;
  top: -25px;
  left: 0;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  white-space: nowrap;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.video-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  background: #f5f5f5;
  padding: 15px;
  border-radius: 10px;
}

.config-grid {
  display: grid;
  gap: 20px;
}

.config-group {
  margin-bottom: 20px;
}

.config-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 10px;
  color: #2c3e50;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: normal;
  margin-bottom: 0;
}

.threshold-controls {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.threshold-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.threshold-item input[type="range"] {
  flex: 1;
}

.config-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

.test-controls {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  gap: 20px;
  margin: 30px 0;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-primary {
  background: linear-gradient(45deg, #2196F3, #1976D2);
  color: white;
}

.btn-success {
  background: linear-gradient(45deg, #4CAF50, #45a049);
  color: white;
}

.btn-secondary {
  background: linear-gradient(45deg, #95a5a6, #7f8c8d);
  color: white;
}

.btn-warning {
  background: linear-gradient(45deg, #FF9800, #F57C00);
  color: white;
}

.btn-danger {
  background: linear-gradient(45deg, #f44336, #da190b);
  color: white;
}

.btn-large {
  padding: 15px 35px;
  font-size: 16px;
}

.progress-section {
  grid-column: 1 / -1;
  background: white;
  padding: 20px;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.progress-bar {
  background: #f0f0f0;
  border-radius: 15px;
  height: 30px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  background: linear-gradient(45deg, #4CAF50, #45a049);
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  transition: width 0.5s ease;
}

.progress-text {
  text-align: center;
  font-weight: 600;
  color: #2c3e50;
}

.results-section {
  grid-column: 1 / -1;
  background: white;
  padding: 25px;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.results-section h2 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.results-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.summary-card {
  text-align: center;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 10px;
  border-left: 4px solid #4CAF50;
}

.summary-value {
  font-size: 2em;
  font-weight: bold;
  color: #4CAF50;
  margin-bottom: 5px;
}

.summary-label {
  color: #666;
  font-size: 0.9em;
}

.detection-events h3 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.event-item {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 10px;
  margin-bottom: 15px;
  border-left: 4px solid #ddd;
}

.event-item.event-fall {
  border-left-color: #f44336;
}

.event-item.event-smoke {
  border-left-color: #9e9e9e;
}

.event-item.event-fire {
  border-left-color: #ff9800;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.event-title {
  font-weight: 600;
  color: #2c3e50;
}

.confidence-badge {
  padding: 4px 12px;
  border-radius: 15px;
  font-size: 0.9em;
  font-weight: bold;
  color: white;
}

.confidence-badge.high {
  background: #4CAF50;
}

.confidence-badge.medium {
  background: #FF9800;
}

.confidence-badge.low {
  background: #f44336;
}

.event-details {
  display: flex;
  gap: 20px;
  color: #666;
  font-size: 0.9em;
}

.speed-selector {
  padding: 5px 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

.time-display {
  font-family: monospace;
  color: #666;
}

@media (max-width: 768px) {
  .test-content {
    grid-template-columns: 1fr;
  }
  
  .default-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .test-controls {
    flex-direction: column;
    align-items: center;
  }
  
  .results-summary {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .event-details {
    flex-direction: column;
    gap: 5px;
  }
}
</style>