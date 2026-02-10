import { BookOpen, Upload, X } from 'lucide-react'
import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { tiktokService } from '../../services/tiktokService'

export default function TikTokStoryModal({ onClose, onSuccess }) {
  const [mode, setMode] = useState('upload') // 'upload' | 'url'
  const [file, setFile] = useState(null)
  const [mediaUrl, setMediaUrl] = useState('')
  const [mediaType, setMediaType] = useState('VIDEO')
  const [publishing, setPublishing] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef(null)

  const handleFileSelect = e => {
    const selected = e.target.files[0]
    if (!selected) return

    if (!selected.type.startsWith('video/')) {
      toast.error('Please select a video file for story upload')
      return
    }

    setFile(selected)
  }

  const handlePublish = async e => {
    e.preventDefault()

    if (mode === 'upload') {
      if (!file) {
        toast.error('Please select a video file')
        return
      }
      await handleFileUpload()
    } else {
      if (!mediaUrl.trim()) {
        toast.error('Please enter a media URL')
        return
      }
      await handleUrlPublish()
    }
  }

  const handleFileUpload = async () => {
    setPublishing(true)
    setUploadProgress(0)

    try {
      const onProgress = percent => {
        setUploadProgress(percent)
      }

      await tiktokService.uploadStoryVideo(file, onProgress)
      onSuccess()
    } catch (error) {
      console.error('Story upload failed:', error)
      toast.error(error.response?.data?.detail || 'Story upload failed.')
    } finally {
      setPublishing(false)
    }
  }

  const handleUrlPublish = async () => {
    setPublishing(true)

    try {
      await tiktokService.publishStoryByUrl({
        media_url: mediaUrl.trim(),
        media_type: mediaType,
      })
      onSuccess()
    } catch (error) {
      console.error('Story publish failed:', error)
      toast.error(error.response?.data?.detail || 'Story publish failed.')
    } finally {
      setPublishing(false)
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
            <BookOpen className="w-6 h-6 text-gray-900" />
            <h2 className="text-xl font-bold text-gray-900">Post TikTok Story</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" disabled={publishing}>
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handlePublish} className="p-6 space-y-4">
          {/* Mode Toggle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Source</label>
            <div className="flex space-x-2">
              <button
                type="button"
                onClick={() => setMode('upload')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  mode === 'upload'
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                disabled={publishing}
              >
                Upload File
              </button>
              <button
                type="button"
                onClick={() => setMode('url')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  mode === 'url'
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                disabled={publishing}
              >
                From URL
              </button>
            </div>
          </div>

          {mode === 'upload' ? (
            /* File Upload */
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Video File
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
                    disabled={publishing}
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors"
                >
                  <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">Click to select a video file</p>
                  <p className="text-xs text-gray-400 mt-1">MP4, MOV, WebM supported</p>
                </button>
              )}
            </div>
          ) : (
            /* URL Input */
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Media Type
                </label>
                <select
                  value={mediaType}
                  onChange={e => setMediaType(e.target.value)}
                  className="input"
                  disabled={publishing}
                >
                  <option value="VIDEO">Video</option>
                  <option value="PHOTO">Photo</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Media URL
                </label>
                <input
                  type="url"
                  value={mediaUrl}
                  onChange={e => setMediaUrl(e.target.value)}
                  placeholder="https://example.com/story-media.mp4"
                  className="input"
                  disabled={publishing}
                />
              </div>
            </>
          )}

          {/* Info */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
            <p className="text-sm text-amber-800">
              Stories are visible for 24 hours and will automatically disappear after that.
            </p>
          </div>

          {/* Upload Progress */}
          {publishing && mode === 'upload' && (
            <div>
              <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                <span>Uploading story video...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-gray-900 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {publishing && mode === 'url' && (
            <div className="text-center py-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 mx-auto"></div>
              <p className="text-sm text-gray-600 mt-2">Publishing story...</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={publishing}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary bg-gray-900 hover:bg-gray-800"
              disabled={
                publishing ||
                (mode === 'upload' && !file) ||
                (mode === 'url' && !mediaUrl.trim())
              }
            >
              {publishing ? 'Publishing...' : 'Post Story'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
