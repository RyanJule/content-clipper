import api from './api'

const TOKEN_KEY = 'auth_token'
const USER_KEY = 'auth_user'

export const authService = {
  register: async (email, username, password, fullName) => {
    console.log('authService.register called with:', { email, username, fullName })
    
    try {
      const payload = {
        email,
        username,
        password,
        full_name: fullName || null,
      }
      
      console.log('Sending registration request:', payload)
      
      const response = await api.post('/auth/register', payload)
      
      console.log('Registration response:', response.data)
      
      if (response.data.access_token) {
        localStorage.setItem(TOKEN_KEY, response.data.access_token)
        localStorage.setItem(USER_KEY, JSON.stringify(response.data.user))
        console.log('Token and user saved to localStorage')
      }
      
      return response.data
    } catch (error) {
      console.error('authService.register error:', error)
      throw error
    }
  },

  login: async (email, password) => {
    console.log('authService.login called with:', { email })
    
    try {
      const response = await api.post('/auth/login', {
        email,
        password,
      })
      
      console.log('Login response:', response.data)
      
      if (response.data.access_token) {
        localStorage.setItem(TOKEN_KEY, response.data.access_token)
        localStorage.setItem(USER_KEY, JSON.stringify(response.data.user))
      }
      
      return response.data
    } catch (error) {
      console.error('authService.login error:', error)
      throw error
    }
  },

  logout: () => {
    console.log('authService.logout called')
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },

  getCurrentUser: () => {
    const user = localStorage.getItem(USER_KEY)
    return user ? JSON.parse(user) : null
  },

  getToken: () => {
    return localStorage.getItem(TOKEN_KEY)
  },

  isLoggedIn: () => {
    return !!localStorage.getItem(TOKEN_KEY)
  },

  getProfile: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },

  updateProfile: async fullName => {
    const response = await api.put('/auth/me', { full_name: fullName })
    const user = authService.getCurrentUser()
    if (user) {
      user.full_name = fullName
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    }
    return response.data
  },
}