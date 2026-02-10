import { Image, Upload, X } from 'lucide-react'
import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { youtubeService } from '../../services/youtubeService'

export default function YouTubeThumbnailModal({ video, onClose, onSuccess }) {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)

  const handleFileSelect = e => {
    const selected = e.target.files[0]
    if (!selected) return

    if (!selected.type.startsWith('image/')) {
      toast.error('Please select an image file (JPG, PNG, or GIF)')
      return
    }

    if (selected.size > 2 * 1024 * 1024) {
      toast.error('Thumbnail must be under 2MB')
      return
    }

    setFile(selected)

    // Create preview
    const reader = new FileReader()
    reader.onload = e => setPreview(e.target.result)
    reader.readAsDataURL(selected)
  }

  const handleUpload = async e => {
    e.preventDefault()

    if (!file) {
      toast.error('Please select a thumbnail image')
      return
    }

    setUploading(true)
    try {
      await youtubeService.setThumbnail(video.id, file)
      onSuccess()
    } catch (error) {
      console.error('Thumbnail upload failed:', error)
      toast.error(
        error.response?.data?.detail ||
          'Failed to set thumbnail. Make sure your account is verified for custom thumbnails.'
      )
    } finally {
      setUploading(false)
    }
  }

  const videoTitle = video?.snippet?.title || 'Video'

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-lg">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Image className="w-6 h-6 text-red-600" />
            <div>
              <h2 className="text-xl font-bold text-gray-900">Set Thumbnail</h2>
              <p className="text-sm text-gray-500 truncate max-w-xs">{videoTitle}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={uploading}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleUpload} className="p-6 space-y-4">
          {/* Current thumbnail */}
          {video?.snippet?.thumbnails?.medium?.url && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Current Thumbnail</p>
              <img
                src={video.snippet.thumbnails.medium.url}
                alt="Current thumbnail"
                className="w-full rounded-lg border border-gray-200"
              />
            </div>
          )}

          {/* New thumbnail selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">New Thumbnail</label>
            <input
              type="file"
              ref={fileInputRef}
              accept="image/jpeg,image/png,image/gif"
              onChange={handleFileSelect}
              className="hidden"
            />

            {preview ? (
              <div className="relative">
                <img
                  src={preview}
                  alt="New thumbnail preview"
                  className="w-full rounded-lg border border-gray-200"
                />
                <button
                  type="button"
                  onClick={() => {
                    setFile(null)
                    setPreview(null)
                    if (fileInputRef.current) fileInputRef.current.value = ''
                  }}
                  className="absolute top-2 right-2 bg-white rounded-full p-1 shadow-md hover:bg-gray-100"
                  disabled={uploading}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-full border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-red-400 transition-colors"
              >
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600">Click to select a thumbnail image</p>
                <p className="text-xs text-gray-400 mt-1">1280x720 recommended, max 2MB</p>
              </button>
            )}
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-sm text-yellow-800">
              <strong>Requirements:</strong> 1280x720 (16:9), under 2MB. JPG, PNG, or GIF.
              Your account must be verified for custom thumbnails.
            </p>
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={uploading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary bg-red-600 hover:bg-red-700"
              disabled={uploading || !file}
            >
              {uploading ? 'Uploading...' : 'Set Thumbnail'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
