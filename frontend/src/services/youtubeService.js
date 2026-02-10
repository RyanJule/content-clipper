import api from './api'

export const youtubeService = {
  // ==================== Channel ====================

  getChannel: async () => {
    const response = await api.get('/youtube/channel')
    return response.data
  },

  // ==================== Videos ====================

  getVideos: async (params = {}) => {
    const response = await api.get('/youtube/videos', { params })
    return response.data
  },

  getVideo: async videoId => {
    const response = await api.get(`/youtube/videos/${videoId}`)
    return response.data
  },

  updateVideo: async (videoId, data) => {
    const response = await api.put(`/youtube/videos/${videoId}`, data)
    return response.data
  },

  deleteVideo: async videoId => {
    const response = await api.delete(`/youtube/videos/${videoId}`)
    return response.data
  },

  // ==================== Upload ====================

  uploadVideo: async (file, metadata, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', metadata.title)
    formData.append('description', metadata.description || '')
    formData.append('tags', (metadata.tags || []).join(','))
    formData.append('category_id', metadata.category_id || '22')
    formData.append('privacy_status', metadata.privacy_status || 'private')
    formData.append('is_short', metadata.is_short || false)
    formData.append('notify_subscribers', metadata.notify_subscribers !== false)

    const response = await api.post('/youtube/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000, // 10 minute timeout for large uploads
      onUploadProgress: progressEvent => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent, progressEvent.loaded, progressEvent.total)
        }
      },
    })
    return response.data
  },

  uploadShort: async (file, metadata, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', metadata.title)
    formData.append('description', metadata.description || '')
    formData.append('tags', (metadata.tags || []).join(','))
    formData.append('privacy_status', metadata.privacy_status || 'public')
    formData.append('notify_subscribers', metadata.notify_subscribers !== false)

    const response = await api.post('/youtube/upload/short', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000,
      onUploadProgress: progressEvent => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent, progressEvent.loaded, progressEvent.total)
        }
      },
    })
    return response.data
  },

  // ==================== Thumbnails ====================

  setThumbnail: async (videoId, file) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post(`/youtube/videos/${videoId}/thumbnail`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  // ==================== Community Posts ====================

  createCommunityPost: async text => {
    const response = await api.post('/youtube/community', { text })
    return response.data
  },

  // ==================== Comments ====================

  getVideoComments: async (videoId, params = {}) => {
    const response = await api.get(`/youtube/videos/${videoId}/comments`, { params })
    return response.data
  },

  postComment: async (videoId, text) => {
    const response = await api.post(`/youtube/videos/${videoId}/comments`, { text })
    return response.data
  },

  replyToComment: async (commentId, text) => {
    const response = await api.post(`/youtube/comments/${commentId}/reply`, { text })
    return response.data
  },

  // ==================== Analytics ====================

  getVideoStats: async videoId => {
    const response = await api.get(`/youtube/videos/${videoId}/stats`)
    return response.data
  },

  // ==================== Categories ====================

  getCategories: async (regionCode = 'US') => {
    const response = await api.get('/youtube/categories', { params: { region_code: regionCode } })
    return response.data
  },
}
