import { FileAudio, FileVideo, Play, Trash2, Upload } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { useApi } from '../hooks/useApi'
import { mediaService } from '../services/mediaService'
import { useStore } from '../store'
import { formatDateTime, formatDuration, formatFileSize } from '../utils/formatters'

export default function MediaLibrary() {
  const { media, setMedia, removeMedia } = useStore()
  const { loading, execute } = useApi()
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    loadMedia()
  }, [])

  const loadMedia = async () => {
    execute(
      async () => {
        const data = await mediaService.getAll()
        setMedia(data)
      },
      { errorMessage: 'Failed to load media' }
    )
  }

  const handleFileUpload = async event => {
    const file = event.target.files[0]
    if (!file) return

    const maxSize = 500 * 1024 * 1024 // 500MB
    if (file.size > maxSize) {
      toast.error('File size must be less than 500MB')
      return
    }

    setUploading(true)
    try {
      const result = await mediaService.upload(file)
      toast.success('File uploaded successfully!')
      loadMedia() // Reload media list
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
      event.target.value = '' // Reset input
    }
  }

  const handleDelete = async id => {
    if (!confirm('Are you sure you want to delete this media?')) return

    execute(
      async () => {
        await mediaService.delete(id)
        removeMedia(id)
      },
      {
        successMessage: 'Media deleted successfully',
        errorMessage: 'Failed to delete media',
      }
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Media Library</h2>
          <p className="text-gray-600 mt-1">Upload and manage your video and audio files</p>
        </div>
        <label className="btn btn-primary flex items-center space-x-2 cursor-pointer">
          <Upload className="w-5 h-5" />
          <span>{uploading ? 'Uploading...' : 'Upload Media'}</span>
          <input
            type="file"
            accept="video/*,audio/*"
            onChange={handleFileUpload}
            disabled={uploading}
            className="hidden"
          />
        </label>
      </div>

      {loading && media.length === 0 ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading media...</p>
        </div>
      ) : media.length === 0 ? (
        <div className="card p-12 text-center">
          <FileVideo className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No media files yet</h3>
          <p className="text-gray-600 mb-6">Upload your first video or audio file to get started</p>
          <label className="btn btn-primary inline-flex items-center space-x-2 cursor-pointer">
            <Upload className="w-5 h-5" />
            <span>Upload Media</span>
            <input
              type="file"
              accept="video/*,audio/*"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {media.map(item => (
            <div key={item.id} className="card overflow-hidden hover:shadow-md transition-shadow">
              {/* Thumbnail */}
              <div className="aspect-video bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
                {item.media_type === 'video' ? (
                  <FileVideo className="w-16 h-16 text-primary-600" />
                ) : (
                  <FileAudio className="w-16 h-16 text-primary-600" />
                )}
              </div>

              {/* Content */}
              <div className="p-4">
                <h3 className="font-semibold text-gray-900 truncate" title={item.original_filename}>
                  {item.original_filename}
                </h3>
                <div className="mt-2 space-y-1 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>Type:</span>
                    <span className="font-medium capitalize">{item.media_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Size:</span>
                    <span className="font-medium">{formatFileSize(item.file_size)}</span>
                  </div>
                  {item.duration && (
                    <div className="flex justify-between">
                      <span>Duration:</span>
                      <span className="font-medium">{formatDuration(item.duration)}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span>Status:</span>
                    <span
                      className={`font-medium capitalize ${
                        item.status === 'ready'
                          ? 'text-green-600'
                          : item.status === 'processing'
                          ? 'text-yellow-600'
                          : 'text-red-600'
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    {formatDateTime(item.created_at)}
                  </div>
                </div>

                {/* Actions */}
                <div className="mt-4 flex space-x-2">
                  <button className="flex-1 btn btn-secondary text-sm py-1.5">
                    <Play className="w-4 h-4 inline mr-1" />
                    View
                  </button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="btn btn-danger text-sm py-1.5 px-3"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}