import api from './api'

export const mediaService = {
  getAll: async () => {
    const response = await api.get('/media/')
    return response.data
  },

  getById: async id => {
    const response = await api.get(`/media/${id}`)
    return response.data
  },

  upload: async (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/media/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 600000, // 10 minutes for large file uploads
      onUploadProgress: progressEvent => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
    return response.data
  },

  delete: async id => {
    const response = await api.delete(`/media/${id}`)
    return response.data
  },

  getStreamUrl: async (id, expires = 3600) => {
    const response = await api.get(`/media/${id}/url`, { params: { expires } })
    return response.data
  },
}