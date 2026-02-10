import {
  BarChart3,
  Edit2,
  ExternalLink,
  Eye,
  Film,
  MessageSquare,
  Plus,
  ThumbsUp,
  Trash2,
  Upload,
  Users,
  Video,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { useApi } from '../hooks/useApi'
import { youtubeService } from '../services/youtubeService'
import YouTubeUploadModal from '../components/YouTube/YouTubeUploadModal'
import YouTubeCommunityModal from '../components/YouTube/YouTubeCommunityModal'
import YouTubeThumbnailModal from '../components/YouTube/YouTubeThumbnailModal'

export default function YouTubeStudio() {
  const { loading, execute } = useApi()
  const [channel, setChannel] = useState(null)
  const [videos, setVideos] = useState([])
  const [pageToken, setPageToken] = useState(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showShortModal, setShowShortModal] = useState(false)
  const [showCommunityModal, setShowCommunityModal] = useState(false)
  const [thumbnailVideo, setThumbnailVideo] = useState(null)

  useEffect(() => {
    loadChannel()
    loadVideos()
  }, [])

  const loadChannel = () => {
    execute(
      async () => {
        const data = await youtubeService.getChannel()
        setChannel(data)
      },
      { errorMessage: 'Failed to load YouTube channel. Please connect your account first.' }
    )
  }

  const loadVideos = (token = null) => {
    execute(
      async () => {
        const data = await youtubeService.getVideos({
          max_results: 25,
          page_token: token || undefined,
        })
        setVideos(data.items || [])
        setPageToken(data.nextPageToken || null)
      },
      { errorMessage: 'Failed to load videos' }
    )
  }

  const handleDeleteVideo = async videoId => {
    if (!window.confirm('Are you sure you want to delete this video? This cannot be undone.')) return

    execute(
      async () => {
        await youtubeService.deleteVideo(videoId)
        setVideos(prev => prev.filter(v => v.id !== videoId))
      },
      {
        successMessage: 'Video deleted successfully',
        errorMessage: 'Failed to delete video',
      }
    )
  }

  const handleUploadSuccess = () => {
    setShowUploadModal(false)
    setShowShortModal(false)
    loadVideos()
    toast.success('Video uploaded successfully!')
  }

  const handleCommunitySuccess = () => {
    setShowCommunityModal(false)
    toast.success('Community post created!')
  }

  const handleThumbnailSuccess = () => {
    setThumbnailVideo(null)
    toast.success('Thumbnail updated!')
  }

  const formatCount = count => {
    const num = parseInt(count, 10)
    if (isNaN(num)) return '0'
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  const formatDuration = iso => {
    if (!iso) return ''
    // Parse ISO 8601 duration like PT1H2M3S
    const match = iso.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/)
    if (!match) return iso
    const h = match[1] ? `${match[1]}:` : ''
    const m = match[2] || '0'
    const s = (match[3] || '0').padStart(2, '0')
    return `${h}${h ? m.padStart(2, '0') : m}:${s}`
  }

  if (loading && !channel && videos.length === 0) {
    return (
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">YouTube Studio</h2>
        <p className="text-gray-600 mb-6">Manage your YouTube channel and videos</p>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading YouTube Studio...</p>
        </div>
      </div>
    )
  }

  if (!channel && !loading) {
    return (
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">YouTube Studio</h2>
        <p className="text-gray-600 mb-6">Manage your YouTube channel and videos</p>
        <div className="card p-12 text-center">
          <Video className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No YouTube Channel Connected</h3>
          <p className="text-gray-600 mb-6">
            Connect your YouTube channel from the Accounts page to get started.
          </p>
          <a href="/accounts" className="btn btn-primary inline-flex items-center space-x-2">
            <Plus className="w-5 h-5" />
            <span>Connect YouTube</span>
          </a>
        </div>
      </div>
    )
  }

  const snippet = channel?.snippet || {}
  const statistics = channel?.statistics || {}

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">YouTube Studio</h2>
          <p className="text-gray-600 mt-1">Manage your YouTube channel and videos</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowCommunityModal(true)}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <MessageSquare className="w-5 h-5" />
            <span>Community Post</span>
          </button>
          <button
            onClick={() => setShowShortModal(true)}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <Film className="w-5 h-5" />
            <span>Upload Short</span>
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="btn btn-primary flex items-center space-x-2"
          >
            <Upload className="w-5 h-5" />
            <span>Upload Video</span>
          </button>
        </div>
      </div>

      {/* Channel Stats */}
      {channel && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="card p-4">
            <div className="flex items-center space-x-3">
              {snippet.thumbnails?.default?.url && (
                <img
                  src={snippet.thumbnails.default.url}
                  alt={snippet.title}
                  className="w-12 h-12 rounded-full"
                />
              )}
              <div>
                <h3 className="font-semibold text-gray-900 truncate">{snippet.title}</h3>
                <p className="text-sm text-gray-500">Channel</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center space-x-3">
              <div className="bg-red-100 p-2 rounded-lg">
                <Users className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="text-xl font-bold text-gray-900">
                  {formatCount(statistics.subscriberCount)}
                </p>
                <p className="text-sm text-gray-500">Subscribers</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-100 p-2 rounded-lg">
                <Eye className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-xl font-bold text-gray-900">
                  {formatCount(statistics.viewCount)}
                </p>
                <p className="text-sm text-gray-500">Total Views</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center space-x-3">
              <div className="bg-green-100 p-2 rounded-lg">
                <Video className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-xl font-bold text-gray-900">
                  {formatCount(statistics.videoCount)}
                </p>
                <p className="text-sm text-gray-500">Videos</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Videos List */}
      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Videos</h3>
        </div>

        {videos.length === 0 ? (
          <div className="p-12 text-center">
            <Video className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">No videos uploaded yet</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {videos.map(video => {
              const vs = video.snippet || {}
              const stats = video.statistics || {}
              const content = video.contentDetails || {}
              const statusInfo = video.status || {}
              const thumbnailUrl =
                vs.thumbnails?.medium?.url || vs.thumbnails?.default?.url || ''

              return (
                <div key={video.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start space-x-4">
                    {/* Thumbnail */}
                    <div className="relative flex-shrink-0 w-40 h-24 bg-gray-200 rounded-lg overflow-hidden">
                      {thumbnailUrl && (
                        <img
                          src={thumbnailUrl}
                          alt={vs.title}
                          className="w-full h-full object-cover"
                        />
                      )}
                      <span className="absolute bottom-1 right-1 bg-black bg-opacity-75 text-white text-xs px-1 rounded">
                        {formatDuration(content.duration)}
                      </span>
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-gray-900 truncate">{vs.title}</h4>
                      <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                        {vs.description?.substring(0, 150)}
                        {vs.description?.length > 150 ? '...' : ''}
                      </p>

                      <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                        <span className="flex items-center space-x-1">
                          <Eye className="w-3.5 h-3.5" />
                          <span>{formatCount(stats.viewCount)}</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <ThumbsUp className="w-3.5 h-3.5" />
                          <span>{formatCount(stats.likeCount)}</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <MessageSquare className="w-3.5 h-3.5" />
                          <span>{formatCount(stats.commentCount)}</span>
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-xs ${
                            statusInfo.privacyStatus === 'public'
                              ? 'bg-green-100 text-green-700'
                              : statusInfo.privacyStatus === 'unlisted'
                                ? 'bg-yellow-100 text-yellow-700'
                                : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {statusInfo.privacyStatus}
                        </span>
                        <span className="text-gray-400">
                          {new Date(vs.publishedAt).toLocaleDateString()}
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2 flex-shrink-0">
                      <button
                        onClick={() => setThumbnailVideo(video)}
                        className="btn btn-secondary text-sm p-2"
                        title="Set thumbnail"
                      >
                        <BarChart3 className="w-4 h-4" />
                      </button>
                      <a
                        href={`https://www.youtube.com/watch?v=${video.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-secondary text-sm p-2"
                        title="View on YouTube"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                      <button
                        onClick={() => handleDeleteVideo(video.id)}
                        className="btn btn-danger text-sm p-2"
                        title="Delete video"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Pagination */}
        {pageToken && (
          <div className="p-4 border-t border-gray-200 text-center">
            <button
              onClick={() => loadVideos(pageToken)}
              className="btn btn-secondary"
              disabled={loading}
            >
              Load More
            </button>
          </div>
        )}
      </div>

      {/* Modals */}
      {showUploadModal && (
        <YouTubeUploadModal
          isShort={false}
          onClose={() => setShowUploadModal(false)}
          onSuccess={handleUploadSuccess}
        />
      )}

      {showShortModal && (
        <YouTubeUploadModal
          isShort={true}
          onClose={() => setShowShortModal(false)}
          onSuccess={handleUploadSuccess}
        />
      )}

      {showCommunityModal && (
        <YouTubeCommunityModal
          onClose={() => setShowCommunityModal(false)}
          onSuccess={handleCommunitySuccess}
        />
      )}

      {thumbnailVideo && (
        <YouTubeThumbnailModal
          video={thumbnailVideo}
          onClose={() => setThumbnailVideo(null)}
          onSuccess={handleThumbnailSuccess}
        />
      )}
    </div>
  )
}
