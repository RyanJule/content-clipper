import axios from 'axios'
import toast from 'react-hot-toast'

const API_URL = (import.meta.env.VITE_API_URL || 'http://192.168.86.242:8000').replace(/\/+$/, '')

console.log('API URL:', API_URL)

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor - add auth token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    console.log('API Request:', config.method.toUpperCase(), config.url)
    return config
  },
  error => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor - handle auth errors
api.interceptors.response.use(
  response => {
    console.log('API Response:', response.status, response.config.url)
    return response
  },
  error => {
    console.error('API Response Error:', error.response?.status, error.config?.url)

    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      toast.error('Request timed out - the file may be too large or the connection is slow')
      return Promise.reject(error)
    }

    if (error.response?.status === 401) {
      // Clear auth data and redirect to login
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      
      if (window.location.pathname !== '/login') {
        toast.error('Session expired - please log in again')
        window.location.href = '/login'
      }
    } else if (error.response?.status === 413) {
      toast.error('File is too large to upload')
    } else if (error.response?.status === 403) {
      toast.error('Access denied')
    } else if (error.response?.status === 404) {
      toast.error('Resource not found')
    } else if (error.response?.status >= 500 && !error.config?.skipGlobalErrorToast) {
      toast.error('Server error - please try again later')
    }
    
    return Promise.reject(error)
  }
)

export default api