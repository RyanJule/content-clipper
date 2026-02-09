import api from './api'

export const clipService = {
  // Get all clips
  getAll: async () => {
    const response = await api.get('/clips/')
    return response.data
  },

  // Get single clip
  getById: async id => {
    const response = await api.get(`/clips/${id}`)
    return response.data
  },

  // Create clip
  create: async clipData => {
    const response = await api.post('/clips/', clipData)
    return response.data
  },

  // Update clip
  update: async (id, clipData) => {
    const response = await api.put(`/clips/${id}`, clipData)
    return response.data
  },

  // Generate AI content for clip
  generateContent: async id => {
    const response = await api.post(`/clips/${id}/generate-content`)
    return response.data
  },

  // Delete clip
  delete: async id => {
    const response = await api.delete(`/clips/${id}`)
    return response.data
  },

  // Get presigned streaming URL for a clip
  getStreamUrl: async (id, expires = 3600) => {
    const response = await api.get(`/clips/${id}/url`, { params: { expires } })
    return response.data
  },
}