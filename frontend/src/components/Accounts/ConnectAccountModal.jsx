import { Instagram, Linkedin, Twitter, X, Youtube } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { accountService } from '../../services/accountService'

const platforms = [
  { id: 'instagram', name: 'Instagram', icon: Instagram, color: 'bg-pink-500' },
  { id: 'twitter', name: 'Twitter', icon: Twitter, color: 'bg-blue-400' },
  { id: 'linkedin', name: 'LinkedIn', icon: Linkedin, color: 'bg-blue-700' },
  { id: 'youtube', name: 'YouTube', icon: Youtube, color: 'bg-red-600' },
]

export default function ConnectAccountModal({ onClose, onSuccess }) {
  const [step, setStep] = useState(1)
  const [selectedPlatform, setSelectedPlatform] = useState(null)
  const [formData, setFormData] = useState({
    account_username: '',
    access_token: '',
  })
  const [loading, setLoading] = useState(false)

  const handlePlatformSelect = platform => {
    setSelectedPlatform(platform)
    setStep(2)
  }

  const handleSubmit = async e => {
    e.preventDefault()
    setLoading(true)

    try {
      await accountService.create({
        platform: selectedPlatform.id,
        account_username: formData.account_username,
        access_token: formData.access_token,
        is_active: true,
      })
      toast.success(`${selectedPlatform.name} account connected!`)
      onSuccess()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to connect account')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white">
          <h2 className="text-2xl font-bold text-gray-900">Connect Account</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          {step === 1 && (
            <div className="space-y-4">
              <p className="text-gray-600">Select a platform to connect:</p>
              <div className="grid grid-cols-2 gap-4">
                {platforms.map(platform => (
                  <button
                    key={platform.id}
                    onClick={() => handlePlatformSelect(platform)}
                    className="card p-6 hover:shadow-md transition-shadow text-left"
                  >
                    <div className="flex items-center space-x-3">
                      <div className={`${platform.color} p-3 rounded-lg text-white`}>
                        <platform.icon className="w-6 h-6" />
                      </div>
                      <span className="font-semibold text-gray-900">{platform.name}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === 2 && selectedPlatform && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
                <div className={`${selectedPlatform.color} p-2 rounded text-white`}>
                  <selectedPlatform.icon className="w-5 h-5" />
                </div>
                <span className="font-semibold text-gray-900">{selectedPlatform.name}</span>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Account Username
                </label>
                <input
                  type="text"
                  value={formData.account_username}
                  onChange={e => setFormData({ ...formData, account_username: e.target.value })}
                  className="input"
                  placeholder="@username"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Access Token
                </label>
                <textarea
                  value={formData.access_token}
                  onChange={e => setFormData({ ...formData, access_token: e.target.value })}
                  className="input"
                  rows="3"
                  placeholder="Paste your API access token here"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Get your access token from {selectedPlatform.name}'s developer console
                </p>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  💡 <strong>Note:</strong> This is a simplified connection flow. In production, you would use OAuth 2.0 for secure authentication.
                </p>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="btn btn-secondary"
                >
                  Back
                </button>
                <button type="submit" disabled={loading} className="btn btn-primary">
                  {loading ? 'Connecting...' : 'Connect Account'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}