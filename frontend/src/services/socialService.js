import api from './api'

export const socialService = {
  // Get all posts
  getAll: async () => {
    const response = await api.get('/social/')
    return response.data
  },

  // Get single post
  getById: async id => {
    const response = await api.get(`/social/${id}`)
    return response.data
  },

  // Create post
  create: async postData => {
    const response = await api.post('/social/', postData)
    return response.data
  },

  // Update post
  update: async (id, postData) => {
    const response = await api.put(`/social/${id}`, postData)
    return response.data
  },

  // Publish post
  publish: async id => {
    const response = await api.post(`/social/${id}/publish`)
    return response.data
  },

  // Delete post
  delete: async id => {
    const response = await api.delete(`/social/${id}`)
    return response.data
  },
}