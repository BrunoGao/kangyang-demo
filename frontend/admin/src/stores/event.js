import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useEventStore = defineStore('event', () => {
  const events = ref([])
  const statistics = ref({})
  const loading = ref(false)
  const pagination = ref({
    page: 0,
    size: 20,
    total: 0
  })

  // 获取事件列表
  const fetchEvents = async (params = {}) => {
    loading.value = true
    try {
      const response = await axios.get('/api/events', {
        params: {
          page: pagination.value.page,
          size: pagination.value.size,
          ...params
        }
      })
      events.value = response.data.content
      pagination.value.total = response.data.totalElements
    } catch (error) {
      console.error('获取事件列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 处理事件
  const handleEvent = async (eventId, handler, remarks = '') => {
    try {
      await axios.put(`/api/events/${eventId}/handle`, null, {
        params: { handler, remarks }
      })
      // 重新加载数据
      await fetchEvents()
      await fetchStatistics()
    } catch (error) {
      console.error('处理事件失败:', error)
      throw error
    }
  }

  // 获取统计数据
  const fetchStatistics = async () => {
    try {
      const response = await axios.get('/api/events/statistics')
      statistics.value = response.data
    } catch (error) {
      console.error('获取统计数据失败:', error)
    }
  }

  // 创建事件
  const createEvent = async (eventData) => {
    try {
      await axios.post('/api/events', eventData)
      await fetchEvents()
      await fetchStatistics()
    } catch (error) {
      console.error('创建事件失败:', error)
      throw error
    }
  }

  return {
    events,
    statistics,
    loading,
    pagination,
    fetchEvents,
    handleEvent,
    fetchStatistics,
    createEvent
  }
})