import {
  BarChart3,
  Eye,
  Heart,
  Image,
  MessageCircle,
  MessageSquare,
  Plus,
  Trash2,
  Users,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { useApi } from '../hooks/useApi'
import { instagramService } from '../services/instagramService'

export default function InstagramDashboard() {
  const { loading, execute } = useApi()
  const [accountInfo, setAccountInfo] = useState(null)
  const [media, setMedia] = useState([])
  const [insights, setInsights] = useState([])
  const [selectedMedia, setSelectedMedia] = useState(null)
  const [comments, setComments] = useState([])
  const [replyText, setReplyText] = useState('')
  const [replyingTo, setReplyingTo] = useState(null)

  useEffect(() => {
    loadAccountInfo()
    loadMedia()
    loadInsights()
  }, [])

  const loadAccountInfo = () => {
    execute(
      async () => {
        const data = await instagramService.getAccountInfo()
        setAccountInfo(data)
      },
      { errorMessage: 'Failed to load Instagram account. Please connect your account first.' }
    )
  }

  const loadMedia = () => {
    execute(
      async () => {
        const data = await instagramService.getMedia(25)
        setMedia(data.data || [])
      },
      { errorMessage: 'Failed to load media' }
    )
  }

  const loadInsights = () => {
    execute(
      async () => {
        const data = await instagramService.getAccountInsights({
          metrics: 'impressions,reach,profile_views',
          period: 'day',
        })
        setInsights(data.data || [])
      },
      {} // Silently fail for insights — may not have permission
    )
  }

  const loadComments = async mediaId => {
    try {
      const data = await instagramService.getMediaComments(mediaId)
      setComments(data.data || [])
      setSelectedMedia(mediaId)
    } catch {
      toast.error('Failed to load comments')
    }
  }

  const handleReply = async commentId => {
    if (!replyText.trim()) return

    try {
      await instagramService.replyToComment(commentId, replyText.trim())
      toast.success('Reply posted!')
      setReplyText('')
      setReplyingTo(null)
      if (selectedMedia) loadComments(selectedMedia)
    } catch {
      toast.error('Failed to post reply')
    }
  }

  const handleDeleteComment = async commentId => {
    if (!window.confirm('Delete this comment?')) return

    try {
      await instagramService.deleteComment(commentId)
      toast.success('Comment deleted')
      setComments(prev => prev.filter(c => c.id !== commentId))
    } catch {
      toast.error('Failed to delete comment')
    }
  }

  const handleHideComment = async (commentId, hide) => {
    try {
      await instagramService.hideComment(commentId, hide)
      toast.success(hide ? 'Comment hidden' : 'Comment unhidden')
    } catch {
      toast.error('Failed to update comment')
    }
  }

  const formatCount = count => {
    const num = parseInt(count, 10)
    if (isNaN(num)) return '0'
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  if (loading && !accountInfo && media.length === 0) {
    return (
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Instagram Dashboard</h2>
        <p className="text-gray-600 mb-6">Manage your Instagram Business account</p>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading Instagram data...</p>
        </div>
      </div>
    )
  }

  if (!accountInfo && !loading) {
    return (
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Instagram Dashboard</h2>
        <p className="text-gray-600 mb-6">Manage your Instagram Business account</p>
        <div className="card p-12 text-center">
          <Image className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Instagram Account Connected</h3>
          <p className="text-gray-600 mb-6">
            Connect your Instagram Business account from the Accounts page.
          </p>
          <a href="/accounts" className="btn btn-primary inline-flex items-center space-x-2">
            <Plus className="w-5 h-5" />
            <span>Connect Instagram</span>
          </a>
        </div>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900">Instagram Dashboard</h2>
        <p className="text-gray-600 mt-1">Manage your Instagram Business account</p>
      </div>

      {/* Account Info + Stats */}
      {accountInfo && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="card p-4">
            <div className="flex items-center space-x-3">
              {accountInfo.profile_picture_url && (
                <img
                  src={accountInfo.profile_picture_url}
                  alt={accountInfo.username}
                  className="w-12 h-12 rounded-full"
                />
              )}
              <div>
                <h3 className="font-semibold text-gray-900">@{accountInfo.username}</h3>
                <p className="text-sm text-gray-500">{accountInfo.name}</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center space-x-3">
              <div className="bg-pink-100 p-2 rounded-lg">
                <Users className="w-5 h-5 text-pink-600" />
              </div>
              <div>
                <p className="text-xl font-bold text-gray-900">
                  {formatCount(accountInfo.followers_count)}
                </p>
                <p className="text-sm text-gray-500">Followers</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center space-x-3">
              <div className="bg-purple-100 p-2 rounded-lg">
                <Image className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-xl font-bold text-gray-900">
                  {formatCount(accountInfo.media_count)}
                </p>
                <p className="text-sm text-gray-500">Posts</p>
              </div>
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-100 p-2 rounded-lg">
                <Users className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-xl font-bold text-gray-900">
                  {formatCount(accountInfo.follows_count)}
                </p>
                <p className="text-sm text-gray-500">Following</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Insights */}
      {insights.length > 0 && (
        <div className="card mb-6">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
              <BarChart3 className="w-5 h-5" />
              <span>Insights</span>
            </h3>
          </div>
          <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            {insights.map(insight => (
              <div key={insight.name} className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">
                  {formatCount(
                    insight.values?.[0]?.value || 0
                  )}
                </p>
                <p className="text-sm text-gray-500 capitalize">
                  {insight.name?.replace(/_/g, ' ')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Media Grid */}
        <div className="card">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent Posts</h3>
          </div>

          {media.length === 0 ? (
            <div className="p-12 text-center">
              <Image className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">No posts yet</p>
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-1 p-1">
              {media.map(item => (
                <button
                  key={item.id}
                  onClick={() => loadComments(item.id)}
                  className={`relative aspect-square overflow-hidden rounded ${
                    selectedMedia === item.id ? 'ring-2 ring-pink-500' : ''
                  }`}
                >
                  {item.media_url && (
                    <img
                      src={item.thumbnail_url || item.media_url}
                      alt={item.caption?.substring(0, 50) || 'Post'}
                      className="w-full h-full object-cover"
                    />
                  )}
                  <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 p-1 flex items-center justify-center space-x-2 text-white text-xs">
                    <span className="flex items-center space-x-0.5">
                      <Heart className="w-3 h-3" />
                      <span>{formatCount(item.like_count)}</span>
                    </span>
                    <span className="flex items-center space-x-0.5">
                      <MessageCircle className="w-3 h-3" />
                      <span>{formatCount(item.comments_count)}</span>
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Comments Panel */}
        <div className="card">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
              <MessageCircle className="w-5 h-5" />
              <span>Comments</span>
            </h3>
          </div>

          {!selectedMedia ? (
            <div className="p-12 text-center">
              <MessageCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">Select a post to view comments</p>
            </div>
          ) : comments.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-600">No comments on this post</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
              {comments.map(comment => (
                <div key={comment.id} className="p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-sm">
                        <span className="font-semibold text-gray-900">{comment.username}</span>{' '}
                        <span className="text-gray-700">{comment.text}</span>
                      </p>
                      <div className="flex items-center space-x-3 mt-1 text-xs text-gray-500">
                        <span>{new Date(comment.timestamp).toLocaleDateString()}</span>
                        {comment.like_count > 0 && (
                          <span>{comment.like_count} likes</span>
                        )}
                        <button
                          onClick={() => setReplyingTo(replyingTo === comment.id ? null : comment.id)}
                          className="text-pink-600 hover:text-pink-700"
                        >
                          Reply
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center space-x-1 ml-2">
                      <button
                        onClick={() => handleHideComment(comment.id, true)}
                        className="text-gray-400 hover:text-gray-600 text-xs"
                        title="Hide comment"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteComment(comment.id)}
                        className="text-gray-400 hover:text-red-500"
                        title="Delete comment"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Reply input */}
                  {replyingTo === comment.id && (
                    <div className="mt-2 flex items-center space-x-2">
                      <input
                        type="text"
                        value={replyText}
                        onChange={e => setReplyText(e.target.value)}
                        placeholder="Write a reply..."
                        className="input text-sm flex-1"
                        onKeyDown={e => {
                          if (e.key === 'Enter') handleReply(comment.id)
                        }}
                      />
                      <button
                        onClick={() => handleReply(comment.id)}
                        className="btn btn-primary text-sm px-3 py-1.5 bg-pink-600 hover:bg-pink-700"
                        disabled={!replyText.trim()}
                      >
                        Reply
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
