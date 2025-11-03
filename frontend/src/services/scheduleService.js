import api from './api'

export const scheduleService = {
  // Schedules
  getAllSchedules: async (accountId = null) => {
    const params = accountId ? { account_id: accountId } : {}
    const response = await api.get('/schedules/', { params })
    return response.data
  },

  getSchedule: async id => {
    const response = await api.get(`/schedules/${id}`)
    return response.data
  },

  createSchedule: async scheduleData => {
    const response = await api.post('/schedules/', scheduleData)
    return response.data
  },

  updateSchedule: async (id, scheduleData) => {
    const response = await api.put(`/schedules/${id}`, scheduleData)
    return response.data
  },

  deleteSchedule: async id => {
    const response = await api.delete(`/schedules/${id}`)
    return response.data
  },

  // Suggestions
  getSuggestions: async platform => {
    const response = await api.get('/schedules/suggestions', { params: { platform } })
    return response.data
  },

  // Calendar
  getCalendar: async (year, month, accountId = null) => {
    const params = accountId ? { account_id: accountId } : {}
    const response = await api.get(`/schedules/calendar/${year}/${month}`, { params })
    return response.data
  },

  // Scheduled Posts
  createPost: async postData => {
    const response = await api.post('/schedules/posts', postData)
    return response.data
  },

  getPost: async id => {
    const response = await api.get(`/schedules/posts/${id}`)
    return response.data
  },

  updatePost: async (id, postData) => {
    const response = await api.put(`/schedules/posts/${id}`, postData)
    return response.data
  },

  deletePost: async id => {
    const response = await api.delete(`/schedules/posts/${id}`)
    return response.data
  },
}