import api from './api'

export const tiktokService = {
  // ==================== Account ====================

  getAccount: async () => {
    const response = await api.get('/tiktok/account')
    return response.data
  },

  getCreatorInfo: async () => {
    const response = await api.get('/tiktok/creator-info')
    return response.data
  },

  // ==================== Video Publishing ====================

  publishVideoByUrl: async data => {
    const response = await api.post('/tiktok/publish/video/url', data)
    return response.data
  },

  uploadVideo: async (file, metadata, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', metadata.title || '')
    formData.append('privacy_level', metadata.privacy_level || 'SELF_ONLY')
    formData.append('disable_duet', metadata.disable_duet || false)
    formData.append('disable_comment', metadata.disable_comment || false)
    formData.append('disable_stitch', metadata.disable_stitch || false)
    formData.append('video_cover_timestamp_ms', metadata.video_cover_timestamp_ms || 0)

    const response = await api.post('/tiktok/upload/video', formData, {
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

  // ==================== Photo Publishing ====================

  publishPhotoPost: async data => {
    const response = await api.post('/tiktok/publish/photo', data)
    return response.data
  },

  // ==================== Story Publishing ====================

  publishStoryByUrl: async data => {
    const response = await api.post('/tiktok/publish/story/url', data)
    return response.data
  },

  uploadStoryVideo: async (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/tiktok/upload/story', formData, {
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

  // ==================== Publish Status ====================

  getPublishStatus: async publishId => {
    const response = await api.post('/tiktok/publish/status', { publish_id: publishId })
    return response.data
  },
}
