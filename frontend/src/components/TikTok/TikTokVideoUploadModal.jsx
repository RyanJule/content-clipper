import { Upload, X } from 'lucide-react'
import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { tiktokService } from '../../services/tiktokService'

export default function TikTokVideoUploadModal({ onClose, onSuccess }) {
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [privacyLevel, setPrivacyLevel] = useState('SELF_ONLY')
  const [disableDuet, setDisableDuet] = useState(false)
  const [disableComment, setDisableComment] = useState(false)
  const [disableStitch, setDisableStitch] = useState(false)
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

    if (selected.size > 4 * 1024 * 1024 * 1024) {
      toast.error('Video file must be under 4GB')
      return
    }

    setFile(selected)
  }

  const handleUpload = async e => {
    e.preventDefault()

    if (!file) {
      toast.error('Please select a video file')
      return
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      const metadata = {
        title: title.trim(),
        privacy_level: privacyLevel,
        disable_duet: disableDuet,
        disable_comment: disableComment,
        disable_stitch: disableStitch,
      }

      const onProgress = percent => {
        setUploadProgress(percent)
      }

      await tiktokService.uploadVideo(file, metadata, onProgress)
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
            <Upload className="w-6 h-6 text-gray-900" />
            <h2 className="text-xl font-bold text-gray-900">Upload TikTok Video</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" disabled={uploading}>
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleUpload} className="p-6 space-y-4">
          {/* File Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Video File <span className="text-gray-500">(max 4GB, 1s-10min)</span>
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
                className="w-full border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors"
              >
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600">Click to select a video file</p>
                <p className="text-xs text-gray-400 mt-1">MP4, MOV, WebM supported</p>
              </button>
            )}
          </div>

          {/* Caption */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Caption</label>
            <textarea
              value={title}
              onChange={e => setTitle(e.target.value)}
              maxLength={2200}
              rows={4}
              placeholder="Write a caption for your TikTok..."
              className="input"
              disabled={uploading}
            />
            <p className="text-xs text-gray-400 mt-1">{title.length}/2200 characters</p>
          </div>

          {/* Privacy */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Privacy</label>
            <select
              value={privacyLevel}
              onChange={e => setPrivacyLevel(e.target.value)}
              className="input"
              disabled={uploading}
            >
              <option value="PUBLIC_TO_EVERYONE">Public</option>
              <option value="MUTUAL_FOLLOW_FRIENDS">Friends</option>
              <option value="FOLLOWER_OF_CREATOR">Followers</option>
              <option value="SELF_ONLY">Only Me</option>
            </select>
          </div>

          {/* Interaction Settings */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Interactions</label>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="allowComment"
                checked={!disableComment}
                onChange={e => setDisableComment(!e.target.checked)}
                className="rounded border-gray-300 text-gray-900 focus:ring-gray-500"
                disabled={uploading}
              />
              <label htmlFor="allowComment" className="text-sm text-gray-700">
                Allow comments
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="allowDuet"
                checked={!disableDuet}
                onChange={e => setDisableDuet(!e.target.checked)}
                className="rounded border-gray-300 text-gray-900 focus:ring-gray-500"
                disabled={uploading}
              />
              <label htmlFor="allowDuet" className="text-sm text-gray-700">
                Allow Duet
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="allowStitch"
                checked={!disableStitch}
                onChange={e => setDisableStitch(!e.target.checked)}
                className="rounded border-gray-300 text-gray-900 focus:ring-gray-500"
                disabled={uploading}
              />
              <label htmlFor="allowStitch" className="text-sm text-gray-700">
                Allow Stitch
              </label>
            </div>
          </div>

          {/* Upload Progress */}
          {uploading && (
            <div>
              <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                <span>Uploading video...</span>
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
              className="btn btn-primary bg-gray-900 hover:bg-gray-800"
              disabled={uploading || !file}
            >
              {uploading ? 'Uploading...' : 'Upload Video'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
