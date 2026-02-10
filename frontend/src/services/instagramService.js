import api from './api'

export const instagramService = {
  // ==================== Account ====================

  getAccountInfo: async () => {
    const response = await api.get('/instagram/account')
    return response.data
  },

  // ==================== Media ====================

  getMedia: async (limit = 25) => {
    const response = await api.get('/instagram/media', { params: { limit } })
    return response.data
  },

  getMediaDetails: async mediaId => {
    const response = await api.get(`/instagram/media/${mediaId}`)
    return response.data
  },

  // ==================== Comments ====================

  getMediaComments: async (mediaId, limit = 50) => {
    const response = await api.get(`/instagram/media/${mediaId}/comments`, { params: { limit } })
    return response.data
  },

  replyToComment: async (commentId, message) => {
    const response = await api.post(`/instagram/comments/${commentId}/reply`, { message })
    return response.data
  },

  deleteComment: async commentId => {
    const response = await api.delete(`/instagram/comments/${commentId}`)
    return response.data
  },

  hideComment: async (commentId, hide = true) => {
    const response = await api.post(`/instagram/comments/${commentId}/hide`, { hide })
    return response.data
  },

  // ==================== Insights ====================

  getAccountInsights: async (params = {}) => {
    const response = await api.get('/instagram/insights', { params })
    return response.data
  },

  getMediaInsights: async (mediaId, metrics = 'engagement,impressions,reach,saved') => {
    const response = await api.get(`/instagram/media/${mediaId}/insights`, {
      params: { metrics },
    })
    return response.data
  },

  // ==================== Messages ====================

  getConversations: async (limit = 50) => {
    const response = await api.get('/instagram/conversations', { params: { limit } })
    return response.data
  },

  getConversationMessages: async (conversationId, limit = 50) => {
    const response = await api.get(`/instagram/conversations/${conversationId}/messages`, {
      params: { limit },
    })
    return response.data
  },

  sendMessage: async (recipientId, message) => {
    const response = await api.post('/instagram/messages', {
      recipient_id: recipientId,
      message,
    })
    return response.data
  },
}
