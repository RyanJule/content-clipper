import api from './api'

export const brandService = {
  getAll: async () => {
    const response = await api.get('/brands/')
    return response.data
  },

  getById: async id => {
    const response = await api.get(`/brands/${id}`)
    return response.data
  },

  create: async brandData => {
    const response = await api.post('/brands/', brandData)
    return response.data
  },

  update: async (id, brandData) => {
    const response = await api.put(`/brands/${id}`, brandData)
    return response.data
  },

  delete: async id => {
    await api.delete(`/brands/${id}`)
  },

  assignAccount: async (brandId, accountId) => {
    const response = await api.post(`/brands/${brandId}/accounts/${accountId}`)
    return response.data
  },

  removeAccount: async (brandId, accountId) => {
    const response = await api.delete(`/brands/${brandId}/accounts/${accountId}`)
    return response.data
  },
}
