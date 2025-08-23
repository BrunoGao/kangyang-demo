<template>
  <div class="events-page">
    <el-card>
      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-select v-model="searchParams.isHandled" placeholder="处理状态" clearable>
              <el-option label="未处理" :value="false" />
              <el-option label="已处理" :value="true" />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select v-model="searchParams.severity" placeholder="严重程度" clearable>
              <el-option label="紧急" value="immediate" />
              <el-option label="严重" value="critical" />
            </el-select>
          </el-col>
          <el-col :span="8">
            <el-date-picker
              v-model="dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-col>
          <el-col :span="4">
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-col>
        </el-row>
      </div>

      <!-- 事件列表 -->
      <el-table
        :data="eventStore.events"
        :loading="eventStore.loading"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="createdTime" label="发生时间" width="180">
          <template #default="scope">
            {{ formatTime(scope.row.createdTime) }}
          </template>
        </el-table-column>
        <el-table-column prop="location" label="位置" width="120" />
        <el-table-column prop="personId" label="人员ID" width="100" />
        <el-table-column prop="eventType" label="事件类型" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.eventType === 'fall_detected' ? 'danger' : 'warning'">
              {{ getEventTypeText(scope.row.eventType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="scope">
            <el-tag :type="getSeverityType(scope.row.severity)">
              {{ getSeverityText(scope.row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="持续时间" width="100">
          <template #default="scope">
            {{ scope.row.duration ? scope.row.duration + 's' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="isHandled" label="处理状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.isHandled ? 'success' : 'danger'">
              {{ scope.row.isHandled ? '已处理' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="handler" label="处理人" width="100" />
        <el-table-column prop="remarks" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button 
              v-if="!scope.row.isHandled"
              type="primary" 
              size="small" 
              @click="handleSingleEvent(scope.row)"
            >
              处理
            </el-button>
            <el-button 
              type="info" 
              size="small" 
              @click="viewDetails(scope.row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 批量操作栏 -->
      <div v-if="selectedEvents.length > 0" class="batch-actions">
        <el-alert
          :title="`已选择 ${selectedEvents.length} 个事件`"
          type="info"
          show-icon
          :closable="false"
        />
        <el-button type="primary" @click="handleBatchProcess">批量处理</el-button>
      </div>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="eventStore.pagination.page"
          v-model:page-size="eventStore.pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="eventStore.pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 事件详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="事件详情" width="600px">
      <div v-if="currentEvent">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="事件ID">{{ currentEvent.id }}</el-descriptions-item>
          <el-descriptions-item label="人员ID">{{ currentEvent.personId }}</el-descriptions-item>
          <el-descriptions-item label="摄像头ID">{{ currentEvent.cameraId }}</el-descriptions-item>
          <el-descriptions-item label="位置">{{ currentEvent.location }}</el-descriptions-item>
          <el-descriptions-item label="事件类型">{{ getEventTypeText(currentEvent.eventType) }}</el-descriptions-item>
          <el-descriptions-item label="严重程度">{{ getSeverityText(currentEvent.severity) }}</el-descriptions-item>
          <el-descriptions-item label="身体角度">{{ currentEvent.bodyAngle }}°</el-descriptions-item>
          <el-descriptions-item label="持续时间">{{ currentEvent.duration }}s</el-descriptions-item>
          <el-descriptions-item label="发生时间" :span="2">{{ formatTime(currentEvent.createdTime) }}</el-descriptions-item>
          <el-descriptions-item label="处理状态" :span="2">
            <el-tag :type="currentEvent.isHandled ? 'success' : 'danger'">
              {{ currentEvent.isHandled ? '已处理' : '待处理' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="currentEvent.handler" label="处理人">{{ currentEvent.handler }}</el-descriptions-item>
          <el-descriptions-item v-if="currentEvent.handleTime" label="处理时间">{{ formatTime(currentEvent.handleTime) }}</el-descriptions-item>
          <el-descriptions-item v-if="currentEvent.remarks" label="处理备注" :span="2">{{ currentEvent.remarks }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, watch } from 'vue'
import { useEventStore } from '@/stores/event'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'

export default defineComponent({
  name: 'Events',
  setup() {
    const eventStore = useEventStore()
    const searchParams = ref({
      isHandled: null,
      severity: null
    })
    const dateRange = ref([])
    const selectedEvents = ref([])
    const detailDialogVisible = ref(false)
    const currentEvent = ref(null)

    const handleSearch = async () => {
      const params = { ...searchParams.value }
      if (dateRange.value && dateRange.value.length === 2) {
        params.startTime = dateRange.value[0]
        params.endTime = dateRange.value[1]
      }
      eventStore.pagination.page = 0
      await eventStore.fetchEvents(params)
    }

    const handleReset = () => {
      searchParams.value = {
        isHandled: null,
        severity: null
      }
      dateRange.value = []
      handleSearch()
    }

    const handleSelectionChange = (selection) => {
      selectedEvents.value = selection
    }

    const handleSingleEvent = async (event) => {
      try {
        const { value } = await ElMessageBox.prompt('请输入处理备注', '处理告警', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          inputPlaceholder: '请输入处理备注'
        })
        
        await eventStore.handleEvent(event.id, '管理员', value)
        ElMessage.success('事件处理成功')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('处理失败')
        }
      }
    }

    const handleBatchProcess = async () => {
      try {
        const { value } = await ElMessageBox.prompt('请输入批量处理备注', '批量处理告警', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          inputPlaceholder: '请输入处理备注'
        })
        
        for (const event of selectedEvents.value) {
          if (!event.isHandled) {
            await eventStore.handleEvent(event.id, '管理员', value)
          }
        }
        
        ElMessage.success(`成功处理 ${selectedEvents.value.length} 个事件`)
        selectedEvents.value = []
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('批量处理失败')
        }
      }
    }

    const viewDetails = (event) => {
      currentEvent.value = event
      detailDialogVisible.value = true
    }

    const handleSizeChange = (size) => {
      eventStore.pagination.size = size
      eventStore.pagination.page = 0
      handleSearch()
    }

    const handleCurrentChange = (page) => {
      eventStore.pagination.page = page - 1
      handleSearch()
    }

    const formatTime = (time) => {
      return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
    }

    const getEventTypeText = (type) => {
      return type === 'fall_detected' ? '跌倒检测' : '长时间躺倒'
    }

    const getSeverityType = (severity) => {
      return severity === 'immediate' ? 'danger' : 'warning'
    }

    const getSeverityText = (severity) => {
      return severity === 'immediate' ? '紧急' : '严重'
    }

    onMounted(() => {
      eventStore.fetchEvents()
    })

    return {
      eventStore,
      searchParams,
      dateRange,
      selectedEvents,
      detailDialogVisible,
      currentEvent,
      handleSearch,
      handleReset,
      handleSelectionChange,
      handleSingleEvent,
      handleBatchProcess,
      viewDetails,
      handleSizeChange,
      handleCurrentChange,
      formatTime,
      getEventTypeText,
      getSeverityType,
      getSeverityText
    }
  }
})
</script>

<style scoped>
.events-page {
  padding: 20px;
}

.search-bar {
  margin-bottom: 20px;
}

.batch-actions {
  margin: 20px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style>