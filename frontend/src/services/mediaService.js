import api from './api'

export const mediaService = {
  // Get all media
  getAll: async () => {
    const response = await api.get('/media/')
    return response.data
  },

  // Get single media
  getById: async id => {
    const response = await api.get(`/media/${id}`)
    return response.data
  },

  // Upload media
  upload: async file => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/media/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Delete media
  delete: async id => {
    const response = await api.delete(`/media/${id}`)
    return response.data
  },
}