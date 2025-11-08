// frontend/src/components/Accounts/OAuthConnectModal.jsx
import { Instagram, Linkedin, X, Youtube } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { oauthService } from '../../services/oauthService'

const platforms = [
  { 
    id: 'instagram', 
    name: 'Instagram', 
    icon: Instagram, 
    color: 'bg-pink-500', 
    description: 'Connect your Instagram account to schedule Reels' 
  },
  { 
    id: 'youtube', 
    name: 'YouTube', 
    icon: Youtube, 
    color: 'bg-red-600', 
    description: 'Connect your YouTube channel to upload Shorts and videos' 
  },
  { 
    id: 'linkedin', 
    name: 'LinkedIn', 
    icon: Linkedin, 
    color: 'bg-blue-700', 
    description: 'Connect your LinkedIn profile for professional content' 
  },
]

export default function OAuthConnectModal({ onClose, onSuccess }) {
  const [connecting, setConnecting] = useState(null)

  useEffect(() => {
    // Handle messages from OAuth popup
    const handleMessage = (event) => {
      // Accept messages from both www and non-www versions
      const allowedOrigins = [
        'https://machine-systems.org',
        'https://www.machine-systems.org'
      ]
      
      if (!allowedOrigins.includes(event.origin)) {
        console.warn('Received message from unknown origin:', event.origin)
        return
      }

      const { type, platform, error } = event.data

      if (type === 'OAUTH_SUCCESS') {
        console.log('OAuth success received for platform:', platform)
        toast.success(`${platform} connected successfully!`)
        setConnecting(null)
        onSuccess()
        onClose()
      } else if (type === 'OAUTH_ERROR') {
        console.error('OAuth error:', error)
        toast.error(`Failed to connect: ${error}`)
        setConnecting(null)
      }
    }

    window.addEventListener('message', handleMessage)

    return () => {
      window.removeEventListener('message', handleMessage)
    }
  }, [onClose, onSuccess])

  const handleConnect = async (platformId) => {
    setConnecting(platformId)
    
    try {
      // Get authorization URL from backend
      const response = await oauthService.initiateOAuth(platformId)
      
      // Open popup window
      const width = 600
      const height = 700
      const left = window.screen.width / 2 - width / 2
      const top = window.screen.height / 2 - height / 2
      
      const popup = window.open(
        response.authorization_url,
        'OAuthPopup',
        `width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no`
      )

      if (!popup) {
        toast.error('Popup blocked! Please allow popups for this site.')
        setConnecting(null)
        return
      }

      // Set a timeout to reset connecting state if no response after 2 minutes
      setTimeout(() => {
        if (connecting === platformId) {
          setConnecting(null)
        }
      }, 120000)

    } catch (error) {
      console.error('OAuth initiation error:', error)
      toast.error(error.response?.data?.detail || 'Failed to initiate connection')
      setConnecting(null)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
          <h2 className="text-2xl font-bold text-gray-900">Connect Account</h2>
          <button 
            onClick={onClose} 
            className="text-gray-400 hover:text-gray-600"
            disabled={connecting}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <p className="text-gray-600">
            Select a platform to connect using OAuth 2.0 secure authentication:
          </p>

          <div className="space-y-3">
            {platforms.map(platform => (
              <button
                key={platform.id}
                onClick={() => handleConnect(platform.id)}
                disabled={connecting !== null}
                className="w-full card p-6 hover:shadow-md transition-shadow text-left disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`${platform.color} p-3 rounded-lg text-white`}>
                      <platform.icon className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{platform.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">{platform.description}</p>
                    </div>
                  </div>
                  <div>
                    {connecting === platform.id ? (
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
                    ) : (
                      <span className="text-primary-600 font-medium">Connect →</span>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
            <p className="text-sm text-blue-800">
              <strong>🔒 Secure OAuth 2.0:</strong> You'll be redirected to the official platform login page. 
              We never see your password. You can revoke access at any time from your platform's settings.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}