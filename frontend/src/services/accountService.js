import api from './api'

export const accountService = {
  // Get all connected accounts
  getAll: async () => {
    const response = await api.get('/accounts/')
    return response.data
  },

  // Get single account
  getById: async id => {
    const response = await api.get(`/accounts/${id}`)
    return response.data
  },

  // Connect new account
  create: async accountData => {
    const response = await api.post('/accounts/', accountData)
    return response.data
  },

  // Update account
  update: async (id, accountData) => {
    const response = await api.put(`/accounts/${id}`, accountData)
    return response.data
  },

  // Disconnect account
  delete: async id => {
    const response = await api.delete(`/accounts/${id}`)
    return response.data
  },
}