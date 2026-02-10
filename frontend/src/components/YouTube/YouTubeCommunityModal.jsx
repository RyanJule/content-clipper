import { MessageSquare, X } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { youtubeService } from '../../services/youtubeService'

export default function YouTubeCommunityModal({ onClose, onSuccess }) {
  const [text, setText] = useState('')
  const [posting, setPosting] = useState(false)

  const handleSubmit = async e => {
    e.preventDefault()

    if (!text.trim()) {
      toast.error('Please enter post text')
      return
    }

    setPosting(true)
    try {
      await youtubeService.createCommunityPost(text.trim())
      onSuccess()
    } catch (error) {
      console.error('Community post failed:', error)
      toast.error(
        error.response?.data?.detail ||
          'Failed to create community post. Your channel may need 500+ subscribers.'
      )
    } finally {
      setPosting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-lg">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <MessageSquare className="w-6 h-6 text-red-600" />
            <h2 className="text-xl font-bold text-gray-900">Create Community Post</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" disabled={posting}>
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Post Text</label>
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              rows={5}
              placeholder="What's on your mind? Share with your community..."
              className="input"
              disabled={posting}
              maxLength={5000}
            />
            <p className="text-xs text-gray-400 mt-1">{text.length}/5000 characters</p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> Community posts require your channel to have 500+ subscribers
              with the Community tab enabled.
            </p>
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <button type="button" onClick={onClose} className="btn btn-secondary" disabled={posting}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary bg-red-600 hover:bg-red-700"
              disabled={posting || !text.trim()}
            >
              {posting ? 'Posting...' : 'Post'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
