import {
  BookOpen,
  ExternalLink,
  Heart,
  ImagePlus,
  Music2,
  Plus,
  Upload,
  Users,
  Video,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { useApi } from '../hooks/useApi'
import { tiktokService } from '../services/tiktokService'
import TikTokVideoUploadModal from '../components/TikTok/TikTokVideoUploadModal'
import TikTokPhotoPostModal from '../components/TikTok/TikTokPhotoPostModal'
import TikTokStoryModal from '../components/TikTok/TikTokStoryModal'

export default function TikTokStudio() {
  const { loading, execute } = useApi()
  const [account, setAccount] = useState(null)
  const [creatorInfo, setCreatorInfo] = useState(null)
  const [showVideoModal, setShowVideoModal] = useState(false)
  const [showPhotoModal, setShowPhotoModal] = useState(false)
  const [showStoryModal, setShowStoryModal] = useState(false)

  // Publish status tracking
  const [publishHistory, setPublishHistory] = useState([])

  useEffect(() => {
    loadAccount()
    loadCreatorInfo()
  }, [])

  const loadAccount = () => {
    execute(
      async () => {
        const data = await tiktokService.getAccount()
        setAccount(data)
      },
      { errorMessage: 'Failed to load TikTok account. Please connect your account first.' }
    )
  }

  const loadCreatorInfo = () => {
    execute(
      async () => {
        const data = await tiktokService.getCreatorInfo()
        setCreatorInfo(data)
      },
      { errorMessage: 'Failed to load creator info' }
    )
  }

  const handleVideoUploadSuccess = () => {
    setShowVideoModal(false)
    toast.success('Video uploaded to TikTok!')
    addToHistory('Video Post', 'Processing')
  }

  const handlePhotoPostSuccess = () => {
    setShowPhotoModal(false)
    toast.success('Photo post published to TikTok!')
    addToHistory('Photo Post', 'Processing')
  }

  const handleStorySuccess = () => {
    setShowStoryModal(false)
    toast.success('Story published to TikTok!')
    addToHistory('Story', 'Processing')
  }

  const addToHistory = (type, status) => {
    setPublishHistory(prev => [
      {
        id: Date.now(),
        type,
        status,
        timestamp: new Date().toLocaleString(),
      },
      ...prev.slice(0, 9), // keep last 10
    ])
  }

  const formatCount = count => {
    const num = parseInt(count, 10)
    if (isNaN(num)) return '0'
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  if (loading && !account) {
    return (
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">TikTok Studio</h2>
        <p className="text-gray-600 mb-6">Manage your TikTok content</p>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading TikTok Studio...</p>
        </div>
      </div>
    )
  }

  if (!account && !loading) {
    return (
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">TikTok Studio</h2>
        <p className="text-gray-600 mb-6">Manage your TikTok content</p>
        <div className="card p-12 text-center">
          <Music2 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No TikTok Account Connected</h3>
          <p className="text-gray-600 mb-6">
            Connect your TikTok account from the Accounts page to get started.
          </p>
          <a href="/accounts" className="btn btn-primary inline-flex items-center space-x-2">
            <Plus className="w-5 h-5" />
            <span>Connect TikTok</span>
          </a>
        </div>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">TikTok Studio</h2>
          <p className="text-gray-600 mt-1">Publish videos, photos, and stories to TikTok</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowStoryModal(true)}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <BookOpen className="w-5 h-5" />
            <span>Post Story</span>
          </button>
          <button
            onClick={() => setShowPhotoModal(true)}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <ImagePlus className="w-5 h-5" />
            <span>Photo Post</span>
          </button>
          <button
            onClick={() => setShowVideoModal(true)}
            className="btn btn-primary bg-gray-900 hover:bg-gray-800 flex items-center space-x-2"
          >
            <Upload className="w-5 h-5" />
            <span>Upload Video</span>
          </button>
        </div>
      </div>

      {/* Account Stats */}
      {account && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="card p-4">
            <div className="flex items-center space-x-3">
              {account.avatar_url && (
                <img
                  src={account.avatar_url}
                  alt={account.display_name}
                  className="w-12 h-12 rounded-full"
                />
              )}
              <div>
                <h3 className="font-semibold text-gray-900 truncate">
                  {account.display_name || 'TikTok User'}
                </h3>
                <p className="text-sm text-gray-500">Account</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center space-x-3">
              <div className="bg-gray-100 p-2 rounded-lg">
                <Users className="w-5 h-5 text-gray-700" />
              </div>
              <div>
                <p className="text-xl font-bold text-gray-900">
                  {formatCount(account.follower_count)}
                </p>
                <p className="text-sm text-gray-500">Followers</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center space-x-3">
              <div className="bg-pink-100 p-2 rounded-lg">
                <Heart className="w-5 h-5 text-pink-600" />
              </div>
              <div>
                <p className="text-xl font-bold text-gray-900">
                  {formatCount(account.likes_count)}
                </p>
                <p className="text-sm text-gray-500">Total Likes</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-100 p-2 rounded-lg">
                <Video className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-xl font-bold text-gray-900">
                  {formatCount(account.video_count)}
                </p>
                <p className="text-sm text-gray-500">Videos</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Creator Info */}
      {creatorInfo && (
        <div className="card mb-6">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Creator Settings</h3>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {creatorInfo.max_video_post_duration_sec && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-sm text-gray-500">Max Video Duration</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {Math.floor(creatorInfo.max_video_post_duration_sec / 60)}m{' '}
                    {creatorInfo.max_video_post_duration_sec % 60}s
                  </p>
                </div>
              )}
              {creatorInfo.privacy_level_options && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-sm text-gray-500">Privacy Options</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {creatorInfo.privacy_level_options.map(level => (
                      <span
                        key={level}
                        className="text-xs bg-white border border-gray-200 rounded px-2 py-0.5 text-gray-700"
                      >
                        {level.replace(/_/g, ' ').toLowerCase()}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {creatorInfo.comment_disabled !== undefined && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-sm text-gray-500">Comments</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {creatorInfo.comment_disabled ? 'Disabled' : 'Enabled'}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Content Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <button
          onClick={() => setShowVideoModal(true)}
          className="card p-6 text-left hover:shadow-md transition-shadow group"
        >
          <div className="bg-gray-900 text-white p-3 rounded-lg w-12 h-12 flex items-center justify-center mb-4 group-hover:bg-gray-800 transition-colors">
            <Video className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Upload Video</h3>
          <p className="text-sm text-gray-500">
            Upload a video directly from your device. Supports up to 4GB and 10 minutes.
          </p>
        </button>

        <button
          onClick={() => setShowPhotoModal(true)}
          className="card p-6 text-left hover:shadow-md transition-shadow group"
        >
          <div className="bg-emerald-600 text-white p-3 rounded-lg w-12 h-12 flex items-center justify-center mb-4 group-hover:bg-emerald-700 transition-colors">
            <ImagePlus className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Photo Post</h3>
          <p className="text-sm text-gray-500">
            Create a photo carousel post with up to 35 images from public URLs.
          </p>
        </button>

        <button
          onClick={() => setShowStoryModal(true)}
          className="card p-6 text-left hover:shadow-md transition-shadow group"
        >
          <div className="bg-amber-500 text-white p-3 rounded-lg w-12 h-12 flex items-center justify-center mb-4 group-hover:bg-amber-600 transition-colors">
            <BookOpen className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Post Story</h3>
          <p className="text-sm text-gray-500">
            Share a story that disappears after 24 hours. Upload video or use a URL.
          </p>
        </button>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
        </div>

        {publishHistory.length === 0 ? (
          <div className="p-12 text-center">
            <Music2 className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">No recent publishing activity</p>
            <p className="text-sm text-gray-400 mt-1">
              Upload a video, create a photo post, or share a story to get started.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {publishHistory.map(item => (
              <div key={item.id} className="p-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div
                    className={`p-2 rounded-lg ${
                      item.type === 'Video Post'
                        ? 'bg-gray-100'
                        : item.type === 'Photo Post'
                          ? 'bg-emerald-100'
                          : 'bg-amber-100'
                    }`}
                  >
                    {item.type === 'Video Post' ? (
                      <Video className="w-4 h-4 text-gray-700" />
                    ) : item.type === 'Photo Post' ? (
                      <ImagePlus className="w-4 h-4 text-emerald-600" />
                    ) : (
                      <BookOpen className="w-4 h-4 text-amber-600" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{item.type}</p>
                    <p className="text-xs text-gray-500">{item.timestamp}</p>
                  </div>
                </div>
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    item.status === 'Published'
                      ? 'bg-green-100 text-green-700'
                      : item.status === 'Failed'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-yellow-100 text-yellow-700'
                  }`}
                >
                  {item.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modals */}
      {showVideoModal && (
        <TikTokVideoUploadModal
          onClose={() => setShowVideoModal(false)}
          onSuccess={handleVideoUploadSuccess}
        />
      )}

      {showPhotoModal && (
        <TikTokPhotoPostModal
          onClose={() => setShowPhotoModal(false)}
          onSuccess={handlePhotoPostSuccess}
        />
      )}

      {showStoryModal && (
        <TikTokStoryModal
          onClose={() => setShowStoryModal(false)}
          onSuccess={handleStorySuccess}
        />
      )}
    </div>
  )
}
