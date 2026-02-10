import { Film, Upload, X } from 'lucide-react'
import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { youtubeService } from '../../services/youtubeService'

export default function YouTubeUploadModal({ isShort = false, onClose, onSuccess }) {
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState('')
  const [privacyStatus, setPrivacyStatus] = useState(isShort ? 'public' : 'private')
  const [notifySubscribers, setNotifySubscribers] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef(null)

  const handleFileSelect = e => {
    const selected = e.target.files[0]
    if (!selected) return

    if (!selected.type.startsWith('video/')) {
      toast.error('Please select a video file')
      return
    }

    // Shorts max 60 seconds - we can't check duration client-side easily,
    // but we can warn about file size
    if (isShort && selected.size > 100 * 1024 * 1024) {
      toast.error('Shorts should be under 60 seconds. This file seems too large.')
    }

    setFile(selected)
    if (!title) {
      // Auto-fill title from filename
      const name = selected.name.replace(/\.[^/.]+$/, '')
      setTitle(name)
    }
  }

  const handleUpload = async e => {
    e.preventDefault()

    if (!file) {
      toast.error('Please select a video file')
      return
    }

    if (!title.trim()) {
      toast.error('Please enter a title')
      return
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      const metadata = {
        title: title.trim(),
        description: description.trim(),
        tags: tags
          .split(',')
          .map(t => t.trim())
          .filter(Boolean),
        privacy_status: privacyStatus,
        is_short: isShort,
        notify_subscribers: notifySubscribers,
      }

      const onProgress = percent => {
        setUploadProgress(percent)
      }

      if (isShort) {
        await youtubeService.uploadShort(file, metadata, onProgress)
      } else {
        await youtubeService.uploadVideo(file, metadata, onProgress)
      }

      onSuccess()
    } catch (error) {
      console.error('Upload failed:', error)
      toast.error(error.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const formatFileSize = bytes => {
    if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB'
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB'
    return (bytes / 1024).toFixed(1) + ' KB'
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white z-10">
          <div className="flex items-center space-x-3">
            {isShort ? (
              <Film className="w-6 h-6 text-red-600" />
            ) : (
              <Upload className="w-6 h-6 text-red-600" />
            )}
            <h2 className="text-xl font-bold text-gray-900">
              {isShort ? 'Upload YouTube Short' : 'Upload Video'}
            </h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" disabled={uploading}>
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleUpload} className="p-6 space-y-4">
          {/* File Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Video File {isShort && <span className="text-gray-500">(vertical, max 60s)</span>}
            </label>
            <input
              type="file"
              ref={fileInputRef}
              accept="video/*"
              onChange={handleFileSelect}
              className="hidden"
            />
            {file ? (
              <div className="border border-gray-300 rounded-lg p-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setFile(null)
                    if (fileInputRef.current) fileInputRef.current.value = ''
                  }}
                  className="text-gray-400 hover:text-red-500"
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
                <p className="text-sm text-gray-600">Click to select a video file</p>
                <p className="text-xs text-gray-400 mt-1">MP4, MOV, AVI, WebM supported</p>
              </button>
            )}
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              maxLength={100}
              placeholder={isShort ? 'My YouTube Short #Shorts' : 'Video Title'}
              className="input"
              disabled={uploading}
            />
            <p className="text-xs text-gray-400 mt-1">{title.length}/100 characters</p>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              maxLength={5000}
              rows={4}
              placeholder="Tell viewers about your video..."
              className="input"
              disabled={uploading}
            />
            <p className="text-xs text-gray-400 mt-1">{description.length}/5000 characters</p>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tags <span className="text-gray-500">(comma-separated)</span>
            </label>
            <input
              type="text"
              value={tags}
              onChange={e => setTags(e.target.value)}
              placeholder="gaming, tutorial, tech"
              className="input"
              disabled={uploading}
            />
          </div>

          {/* Privacy */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Privacy</label>
            <select
              value={privacyStatus}
              onChange={e => setPrivacyStatus(e.target.value)}
              className="input"
              disabled={uploading}
            >
              <option value="private">Private</option>
              <option value="unlisted">Unlisted</option>
              <option value="public">Public</option>
            </select>
          </div>

          {/* Notify Subscribers */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="notify"
              checked={notifySubscribers}
              onChange={e => setNotifySubscribers(e.target.checked)}
              className="rounded border-gray-300 text-red-600 focus:ring-red-500"
              disabled={uploading}
            />
            <label htmlFor="notify" className="text-sm text-gray-700">
              Notify subscribers
            </label>
          </div>

          {isShort && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-sm text-yellow-800">
                <strong>Shorts requirements:</strong> Vertical video (9:16), max 60 seconds.
                #Shorts will be added to the title automatically.
              </p>
            </div>
          )}

          {/* Upload Progress */}
          {uploading && (
            <div>
              <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-red-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4">
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
              disabled={uploading || !file || !title.trim()}
            >
              {uploading ? 'Uploading...' : isShort ? 'Upload Short' : 'Upload Video'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
