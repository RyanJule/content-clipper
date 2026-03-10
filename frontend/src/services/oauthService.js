// frontend/src/services/oauthService.js
import api from './api'

export const oauthService = {
  // Initiate OAuth flow. Pass brandId to associate the account with a brand.
  initiateOAuth: async (platform, brandId = null) => {
    const params = brandId != null ? { brand_id: brandId } : {}
    const response = await api.get(`/oauth/${platform}/authorize`, { params })
    return response.data
  },

  // Check OAuth status
  checkStatus: async platform => {
    const response = await api.get(`/oauth/${platform}/status`)
    return response.data
  },

  // Disconnect OAuth account
  disconnect: async platform => {
    const response = await api.post(`/oauth/${platform}/disconnect`)
    return response.data
  },

  // Get all OAuth statuses
  getAllStatuses: async () => {
    const platforms = ['instagram', 'youtube', 'linkedin', 'tiktok']
    const statuses = await Promise.all(
      platforms.map(async platform => {
        try {
          const status = await oauthService.checkStatus(platform)
          return { platform, ...status }
        } catch (error) {
          return { platform, connected: false, error: true }
        }
      })
    )
    return statuses
  },
}