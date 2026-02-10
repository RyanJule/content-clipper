import api from './api'

export const linkedinService = {
  // ==================== Profile ====================

  getProfile: async () => {
    const response = await api.get('/linkedin/profile')
    return response.data
  },

  // ==================== Organizations ====================

  getOrganizations: async () => {
    const response = await api.get('/linkedin/organizations')
    return response.data
  },

  // ==================== Text Posts ====================

  createTextPost: async (text, authorUrn = null, visibility = 'PUBLIC') => {
    const response = await api.post('/linkedin/posts/text', {
      text,
      author_urn: authorUrn,
      visibility,
    })
    return response.data
  },

  // ==================== Image Posts ====================

  createImagePost: async (file, metadata, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('text', metadata.text || '')
    formData.append('alt_text', metadata.alt_text || '')
    formData.append('visibility', metadata.visibility || 'PUBLIC')
    if (metadata.author_urn) {
      formData.append('author_urn', metadata.author_urn)
    }

    const response = await api.post('/linkedin/posts/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
      onUploadProgress: progressEvent => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent, progressEvent.loaded, progressEvent.total)
        }
      },
    })
    return response.data
  },

  // ==================== Video Posts ====================

  createVideoPost: async (file, metadata, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('text', metadata.text || '')
    formData.append('title', metadata.title || '')
    formData.append('visibility', metadata.visibility || 'PUBLIC')
    if (metadata.author_urn) {
      formData.append('author_urn', metadata.author_urn)
    }

    const response = await api.post('/linkedin/posts/video', formData, {
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

  // ==================== Article Posts ====================

  createArticlePost: async (text, articleUrl, metadata = {}) => {
    const response = await api.post('/linkedin/posts/article', {
      text,
      article_url: articleUrl,
      title: metadata.title || '',
      description: metadata.description || '',
      author_urn: metadata.author_urn || null,
      visibility: metadata.visibility || 'PUBLIC',
    })
    return response.data
  },

  // ==================== Post Management ====================

  getPosts: async (authorUrn = null, count = 10) => {
    const params = { count }
    if (authorUrn) params.author_urn = authorUrn
    const response = await api.get('/linkedin/posts', { params })
    return response.data
  },

  deletePost: async postUrn => {
    const response = await api.delete(`/linkedin/posts/${encodeURIComponent(postUrn)}`)
    return response.data
  },
}
