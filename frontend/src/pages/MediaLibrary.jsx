import { FileAudio, FileImage, FileVideo, Play, RefreshCw, Trash2, Upload, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { useApi } from '../hooks/useApi'
import { mediaService } from '../services/mediaService'
import { useStore } from '../store'
import { formatDateTime, formatDuration, formatFileSize } from '../utils/formatters'

export default function MediaLibrary() {
  const { media, setMedia, removeMedia, addMedia } = useStore()
  const { loading, execute } = useApi()
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [playerMedia, setPlayerMedia] = useState(null)
  const [playerUrl, setPlayerUrl] = useState(null)
  const [loadingUrl, setLoadingUrl] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    loadMedia()
  }, [])

  const loadMedia = async () => {
    try {
      const data = await mediaService.getAll()
      setMedia(data)
      console.log('Loaded media:', data)
    } catch (error) {
      console.error('Failed to load media:', error)
      toast.error('Failed to load media files')
    }
  }

  const handleFileUpload = async event => {
    const file = event.target.files[0]
    if (!file) return

    console.log('Selected file:', file.name, file.type, file.size)

    const maxSize = 10 * 1024 * 1024 * 1024 // 10GB
    if (file.size > maxSize) {
      toast.error('File size must be less than 10GB')
      return
    }

    setUploading(true)
    setUploadProgress(0)
    
    try {
      toast.loading('Uploading file...', { id: 'upload' })
      
      const result = await mediaService.upload(file, progress => {
        setUploadProgress(progress)
      })
      
      console.log('Upload result:', result)
      toast.success('File uploaded successfully!', { id: 'upload' })
      
      // Reload media list
      await loadMedia()
    } catch (error) {
      console.error('Upload error:', error)
      const message = error.response?.data?.detail || error.message || 'Upload failed'
      toast.error(message, { id: 'upload' })
    } finally {
      setUploading(false)
      setUploadProgress(0)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleDelete = async id => {
    if (!window.confirm('Are you sure you want to delete this media?')) return

    try {
      await mediaService.delete(id)
      removeMedia(id)
      toast.success('Media deleted successfully')
    } catch (error) {
      console.error('Delete error:', error)
      toast.error('Failed to delete media')
    }
  }

  const handleView = async item => {
    setLoadingUrl(true)
    try {
      const data = await mediaService.getStreamUrl(item.id)
      setPlayerMedia(item)
      setPlayerUrl(data.url)
    } catch (error) {
      console.error('Failed to get stream URL:', error)
      toast.error('Failed to load media for playback')
    } finally {
      setLoadingUrl(false)
    }
  }

  const closePlayer = () => {
    setPlayerMedia(null)
    setPlayerUrl(null)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Media Library</h2>
          <p className="text-gray-600 mt-1">Upload and manage your video, audio, and image files</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={loadMedia}
            className="btn btn-secondary flex items-center space-x-2"
            disabled={loading}
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <label className="btn btn-primary flex items-center space-x-2 cursor-pointer">
            <Upload className="w-5 h-5" />
            <span>{uploading ? `Uploading ${uploadProgress}%` : 'Upload Media'}</span>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*,audio/*,image/*"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {uploading && (
        <div className="card p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Uploading...</span>
            <span className="text-sm font-medium text-gray-900">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
        </div>
      )}

      {loading && media.length === 0 ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading media...</p>
        </div>
      ) : media.length === 0 ? (
        <div className="card p-12 text-center">
          <FileVideo className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No media files yet</h3>
          <p className="text-gray-600 mb-6">Upload your first video, audio, or image file to get started</p>
          <label className="btn btn-primary inline-flex items-center space-x-2 cursor-pointer">
            <Upload className="w-5 h-5" />
            <span>Upload Media</span>
            <input
              type="file"
              accept="video/*,audio/*,image/*"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {media.map(item => (
            <div key={item.id} className="card overflow-hidden hover:shadow-md transition-shadow">
              <div className="aspect-video bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
                {item.media_type === 'video' ? (
                  <FileVideo className="w-16 h-16 text-primary-600" />
                ) : item.media_type === 'image' ? (
                  <FileImage className="w-16 h-16 text-primary-600" />
                ) : (
                  <FileAudio className="w-16 h-16 text-primary-600" />
                )}
              </div>

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
                  <div className="text-xs text-gray-500 mt-2">{formatDateTime(item.created_at)}</div>
                </div>

                <div className="mt-4 flex space-x-2">
                  <button
                    onClick={() => handleView(item)}
                    disabled={loadingUrl}
                    className="flex-1 btn btn-secondary text-sm py-1.5"
                  >
                    <Play className="w-4 h-4 inline mr-1" />
                    {loadingUrl ? 'Loading...' : 'View'}
                  </button>
                  <button onClick={() => handleDelete(item.id)} className="btn btn-danger text-sm py-1.5 px-3">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {playerMedia && playerUrl && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {playerMedia.original_filename}
              </h3>
              <button
                onClick={closePlayer}
                className="p-1 hover:bg-gray-100 rounded-full"
              >
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>
            <div className="p-4">
              {playerMedia.media_type === 'video' ? (
                <video
                  src={playerUrl}
                  controls
                  autoPlay
                  className="w-full max-h-[70vh] rounded"
                >
                  Your browser does not support video playback.
                </video>
              ) : playerMedia.media_type === 'image' ? (
                <img
                  src={playerUrl}
                  alt={playerMedia.original_filename}
                  className="w-full max-h-[70vh] object-contain rounded"
                />
              ) : (
                <audio src={playerUrl} controls autoPlay className="w-full">
                  Your browser does not support audio playback.
                </audio>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}