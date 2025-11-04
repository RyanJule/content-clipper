import { Lock, Mail, Scissors, User, UserPlus } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { Link, useNavigate } from 'react-router-dom'
import { authService } from '../services/authService'
import { useStore } from '../store'

export default function Register() {
  const navigate = useNavigate()
  const setUser = useStore(state => state.setUser)
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    fullName: '',
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async e => {
    e.preventDefault()
    
    console.log('Form submitted with data:', {
      email: formData.email,
      username: formData.username,
      hasPassword: !!formData.password,
      hasConfirmPassword: !!formData.confirmPassword,
      fullName: formData.fullName,
    })

    // Validation
    if (formData.password !== formData.confirmPassword) {
      console.error('Password mismatch')
      toast.error('Passwords do not match')
      return
    }

    if (formData.password.length < 8) {
      console.error('Password too short')
      toast.error('Password must be at least 8 characters')
      return
    }

    setLoading(true)
    console.log('Starting registration...')

    try {
      console.log('Calling authService.register...')
      const response = await authService.register(
        formData.email,
        formData.username,
        formData.password,
        formData.fullName
      )
      console.log('Registration successful:', response)
      setUser(response.user)
      toast.success('Account created successfully!')
      navigate('/dashboard')
    } catch (error) {
      console.error('Registration error:', error)
      console.error('Error response:', error.response)
      toast.error(error.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
      console.log('Registration attempt finished')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-lg mb-4">
            <Scissors className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-3xl font-bold text-white">Content Clipper</h1>
          <p className="text-primary-100 mt-2">Create your account</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={formData.email}
                  onChange={e => {
                    console.log('Email changed:', e.target.value)
                    setFormData({ ...formData, email: e.target.value })
                  }}
                  className="input pl-10"
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={formData.username}
                  onChange={e => {
                    console.log('Username changed:', e.target.value)
                    setFormData({ ...formData, username: e.target.value })
                  }}
                  className="input pl-10"
                  placeholder="johndoe"
                  required
                  minLength={3}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Full Name (Optional)
              </label>
              <div className="relative">
                <UserPlus className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={formData.fullName}
                  onChange={e => setFormData({ ...formData, fullName: e.target.value })}
                  className="input pl-10"
                  placeholder="John Doe"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  value={formData.password}
                  onChange={e => {
                    console.log('Password changed, length:', e.target.value.length)
                    setFormData({ ...formData, password: e.target.value })
                  }}
                  className="input pl-10"
                  placeholder="••••••••"
                  required
                  minLength={8}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">Minimum 8 characters</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  value={formData.confirmPassword}
                  onChange={e => {
                    console.log('Confirm password changed')
                    setFormData({ ...formData, confirmPassword: e.target.value })
                  }}
                  className="input pl-10"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button 
              type="submit" 
              disabled={loading} 
              className="w-full btn btn-primary"
              onClick={() => console.log('Button clicked, loading:', loading)}
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center space-y-4">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <Link to="/login" className="text-primary-600 hover:text-primary-700 font-medium">
                Sign in
              </Link>
            </p>
            <p className="text-xs text-gray-500">
              By creating an account, you agree to our{' '}
              <Link to="/terms" className="text-primary-600 hover:underline">
                Terms of Service
              </Link>
            </p>
            <a href="/privacy" className="text-xs hover:text-gray-700">Privacy Policy</a>
          </div>
        </div>
      </div>
    </div>
  )
}