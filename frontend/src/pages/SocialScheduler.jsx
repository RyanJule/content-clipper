import { Calendar, Edit2, Plus, Send, Trash2 } from 'lucide-react'
import { useEffect } from 'react'
import { useApi } from '../hooks/useApi'
import { socialService } from '../services/socialService'
import { useStore } from '../store'
import { formatDateTime } from '../utils/formatters'

export default function SocialScheduler() {
  const { posts, setPosts, removePost, brands, selectedBrandId } = useStore()
  const { loading, execute } = useApi()

  // When a brand is selected, filter posts to only platforms that brand has accounts for
  const selectedBrand = selectedBrandId ? brands.find(b => b.id === selectedBrandId) : null
  const brandPlatforms = selectedBrand ? selectedBrand.accounts.map(a => a.platform) : null
  const filteredPosts = brandPlatforms ? posts.filter(p => brandPlatforms.includes(p.platform)) : posts

  useEffect(() => {
    loadPosts()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadPosts = async () => {
    execute(
      async () => {
        const data = await socialService.getAll()
        setPosts(data)
      },
      { errorMessage: 'Failed to load posts' }
    )
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this post?')) return

    execute(
      async () => {
        await socialService.delete(id)
        removePost(id)
      },
      {
        successMessage: 'Post deleted successfully',
        errorMessage: 'Failed to delete post',
      }
    )
  }

  const handlePublish = async (id) => {
    execute(
      async () => {
        await socialService.publish(id)
        loadPosts()
      },
      {
        successMessage: 'Post published successfully!',
        errorMessage: 'Failed to publish post',
      }
    )
  }

  const getStatusColor = (status) => {
    const colors = {
      published: 'bg-green-100 text-green-700',
      scheduled: 'bg-blue-100 text-blue-700',
      draft: 'bg-gray-100 text-gray-700',
      failed: 'bg-red-100 text-red-700',
    }
    return colors[status] || 'bg-gray-100 text-gray-700'
  }

  const getPlatformColor = (platform) => {
    const colors = {
      twitter: 'bg-blue-500',
      linkedin: 'bg-blue-700',
      instagram: 'bg-pink-500',
      tiktok: 'bg-black',
      youtube: 'bg-red-600',
    }
    return colors[platform] || 'bg-gray-500'
  }

  if (loading && filteredPosts.length === 0) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Social Media Scheduler</h2>
            <p className="text-gray-600 mt-1">Schedule and manage social media posts</p>
          </div>
        </div>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading posts...</p>
        </div>
      </div>
    )
  }

  if (filteredPosts.length === 0) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Social Media Scheduler</h2>
            <p className="text-gray-600 mt-1">Schedule and manage social media posts</p>
          </div>
          {!selectedBrandId && (
            <button className="btn btn-primary flex items-center space-x-2">
              <Plus className="w-5 h-5" />
              <span>Create Post</span>
            </button>
          )}
        </div>

        <div className="card p-12 text-center">
          <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            {selectedBrandId ? 'No posts for this brand' : 'No scheduled posts'}
          </h3>
          <p className="text-gray-600 mb-6">
            {selectedBrandId
              ? 'No posts found for the selected brand\'s platforms'
              : 'Create your first social media post'}
          </p>
          {!selectedBrandId && (
            <button className="btn btn-primary inline-flex items-center space-x-2">
              <Plus className="w-5 h-5" />
              <span>Create Post</span>
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Social Media Scheduler</h2>
          <p className="text-gray-600 mt-1">Schedule and manage social media posts</p>
        </div>
        <button className="btn btn-primary flex items-center space-x-2">
          <Plus className="w-5 h-5" />
          <span>Create Post</span>
        </button>
      </div>

      <div className="space-y-4">
        {filteredPosts.map((post) => {
          const platformColor = getPlatformColor(post.platform)
          const statusColor = getStatusColor(post.status)
          const platformName = post.platform.charAt(0).toUpperCase() + post.platform.slice(1)

          let hashtags = []
          try {
            hashtags = post.hashtags ? JSON.parse(post.hashtags) : []
          } catch (e) {
            hashtags = []
          }

          return (
            <div key={post.id} className="card p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-3">
                    <span
                      className={`px-3 py-1 rounded-full text-white text-sm font-medium ${platformColor}`}
                    >
                      {platformName}
                    </span>
                    <span className={`px-3 py-1 rounded text-sm ${statusColor}`}>
                      {post.status}
                    </span>
                  </div>

                  {post.title && (
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{post.title}</h3>
                  )}

                  {post.caption && <p className="text-gray-700 mb-3">{post.caption}</p>}

                  {hashtags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                      {hashtags.map((tag, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-primary-50 text-primary-600 rounded text-sm"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>Created: {formatDateTime(post.created_at)}</span>
                    {post.scheduled_for && (
                      <span>Scheduled: {formatDateTime(post.scheduled_for)}</span>
                    )}
                    {post.published_at && (
                      <span>Published: {formatDateTime(post.published_at)}</span>
                    )}
                  </div>

                  {post.platform_url && (
                    <a
                      href={post.platform_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:underline text-sm mt-2 inline-block"
                    >
                      View on {platformName}
                    </a>
                  )}
                </div>

                <div className="flex items-center space-x-2 ml-4">
                  {post.status === 'draft' && (
                    <button
                      onClick={() => handlePublish(post.id)}
                      className="btn btn-primary text-sm"
                      title="Publish now"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  )}
                  <button className="btn btn-secondary text-sm">
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(post.id)}
                    className="btn btn-danger text-sm"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
